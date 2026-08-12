# Documentación Técnica y Arquitectura de Software
## Sistema de Autenticación Biométrica por Voz

**Versión:** 2.0.0-RELEASE
**Fecha de Generación:** 14 de Diciembre de 2025
**Clasificación:** Confidencial / Uso Interno
**Autor:** Equipo de Arquitectura de Software

---

## 1. Visión General del Sistema

### 1.1 Resumen Ejecutivo
El **Sistema de Autenticación Biométrica por Voz** es una plataforma de seguridad de identidad digital diseñada para validar usuarios mediante el análisis de características vocales únicas (huella de voz). A diferencia de sistemas biométricos estáticos, este proyecto implementa un mecanismo de **Desafío-Respuesta Dinámico** utilizando un corpus de más de 43,000 frases literarias, lo que mitiga significativamente los ataques de suplantación (spoofing) y repetición.

### 1.2 Objetivos del Negocio
1.  **Seguridad Pasiva:** Autenticación robusta sin necesidad de recordar contraseñas complejas.
2.  **Prevención de Fraude:** Detección en tiempo real de grabaciones, síntesis de voz (TTS) y Deepfakes.
3.  **Auditoría Forense:** Trazabilidad completa e inmutable de cada intento de acceso para cumplimiento normativo.

### 1.3 Alcance Funcional
*   **Gestión de Identidad (IAM):** Registro, login y gestión de perfiles.
*   **Enrolamiento Biométrico:** Captura de múltiples muestras de voz para crear un "Voiceprint" maestro.
*   **Verificación Biométrica:** Comparación 1:1 entre el audio en vivo y el Voiceprint almacenado.
*   **Administración:** Dashboard para monitoreo de métricas, gestión de usuarios y configuración de umbrales de seguridad.

---

## 2. Diseño de Arquitectura

### 2.1 Estilo Arquitectónico
El sistema implementa una **Arquitectura Limpia (Clean Architecture)** sobre una estructura de **Monolito Modular**. Este enfoque permite una clara separación de responsabilidades, facilitando el mantenimiento y las pruebas, mientras se mantiene la simplicidad operativa de una sola unidad de despliegue.

### 2.2 Diagrama de Arquitectura (Nivel C4 - Contenedores)

```mermaid
graph TD
    User((Usuario Final))
    Admin((Administrador))

    subgraph "Cliente (Frontend)"
        WebApp[SPA React / Vite]
        AudioProc[Procesador de Audio (Web Audio API)]
    end

    subgraph "API Gateway & Backend (FastAPI)"
        Controller[Controladores REST]
        UseCase[Casos de Uso / Servicios de Aplicación]
        Domain[Lógica de Dominio & Entidades]
        Infra[Infraestructura & Adaptadores]
    end

    subgraph "Motor Biométrico (Python/PyTorch)"
        ML_Speaker[Modelo Reconocimiento (RawNet2/ECAPA)]
        ML_Spoof[Modelo Anti-Spoofing]
        ML_ASR[Speech-to-Text (Validación Frase)]
    end

    subgraph "Persistencia"
        DB[(PostgreSQL)]
        VectorStore[(pgvector)]
        FileStore[Sistema de Archivos / S3 (Audio Blobs)]
        Cache[(Redis)]
    end

    User -->|HTTPS| WebApp
    Admin -->|HTTPS| WebApp
    WebApp -->|Graba| AudioProc
    AudioProc -->|WAV/Blob| Controller
    Controller --> UseCase
    UseCase --> Domain
    UseCase --> Infra
    Infra --> ML_Speaker
    Infra --> ML_Spoof
    Infra --> DB
    Infra --> Cache
```

### 2.3 Descripción de Componentes

#### A. Capa de Presentación (Frontend)
*   **Tecnología:** React 19, TypeScript, Vite, TailwindCSS.
*   **Responsabilidades:**
    *   Renderizado de UI y gestión de rutas.
    *   **Captura de Audio:** Uso de `MediaRecorder API` y `AudioWorklet` para capturar audio en formato PCM/WAV de alta calidad (16kHz) directamente en el navegador.
    *   **Gestión de Estado:** `TanStack Query` para sincronización con el servidor y `Context API` para estado global (auth, tema).

#### B. Capa de Aplicación (Backend Core)
*   **Tecnología:** Python 3.11, FastAPI.
*   **Patrones:** Dependency Injection, Repository Pattern.
*   **Responsabilidades:**
    *   Orquestación de flujos (Enrollment, Verification).
    *   Validación de entradas (Pydantic).
    *   Gestión de sesiones JWT.

#### C. Capa de Dominio (Biometría)
*   **Tecnología:** SpeechBrain, PyTorch.
*   **Componentes:**
    *   **Speaker Encoder:** Transforma audio en un vector de 192/256 dimensiones (Embedding).
    *   **Liveness Detector:** Clasificador binario (Real vs Fake).
    *   **Phrase Validator:** Comparación fonética entre el texto esperado y el audio transcrito.

#### D. Capa de Infraestructura (Datos)
*   **Tecnología:** PostgreSQL 16.
*   **Extensiones Críticas:**
    *   `pgvector`: Permite almacenar embeddings y realizar búsquedas de similitud de cosenos (Cosine Similarity) nativamente en SQL.
    *   `pgcrypto`: Para encriptación de datos sensibles en reposo.

---

## 3. Flujos de Comunicación y Procesos

### 3.1 Proceso de Enrolamiento (Creación de Huella)
1.  **Inicio:** El usuario solicita enrolarse. El sistema selecciona 3 frases de dificultad media.
2.  **Captura:** El usuario graba cada frase. El frontend valida silencio y nivel de ruido (SNR).
3.  **Procesamiento:**
    *   Backend recibe audios.
    *   Extrae embeddings de cada muestra.
    *   Calcula el vector promedio (Centroide).
4.  **Persistencia:** El vector promedio se encripta y se guarda en la tabla `voiceprint`.

### 3.2 Proceso de Verificación (Autenticación)
1.  **Desafío:** El backend genera un `challenge_id` asociado a una frase aleatoria no usada recientemente.
2.  **Respuesta:** El usuario envía el audio leyendo esa frase específica.
3.  **Validación Triple:**
    *   **Score Similitud:** `Cosine(Audio_Input, Voiceprint_Stored) > 0.75`
    *   **Score Liveness:** `Spoof_Probability < 0.5`
    *   **Score Frase:** `Text_Match(Transcription, Phrase) > 80%`
4.  **Decisión:** Si los 3 checks pasan, se emite token de acceso.

---

## 4. Modelo de Datos (Esquema Relacional)

El diseño de base de datos es híbrido (Relacional + Vectorial).

### 4.1 Entidades Principales

| Entidad | Descripción | Detalles Técnicos |
| :--- | :--- | :--- |
| **`user`** | Identidad del usuario. | UUID, Role (RBAC), Email. |
| **`voiceprint`** | Huella biométrica activa. | Contiene columna `embedding vector(256)`. Relación 1:1 con User. |
| **`enrollment_sample`** | Muestras crudas del registro. | Usadas para re-entrenar o recalibrar el voiceprint. |
| **`phrase`** | Catálogo de desafíos. | 43,000+ registros. Columnas: `text`, `difficulty`, `source`. |
| **`challenge`** | Desafío temporal. | TTL (Time-To-Live) corto. Vincula User + Phrase. |
| **`auth_attempt`** | Registro de decisión de negocio. | Resultado final (`BOOL`), Latencia, Razón del fallo. |
| **`scores`** | Registro de evidencia técnica. | Valores exactos de similitud y probabilidad de spoofing. |

### 4.2 Tablas de Auditoría
*   **`audit_log`**: Tabla inmutable (Append-only). Registra `actor`, `action`, `timestamp` y `metadata` JSON. Crítico para cumplimiento de normas de seguridad.

---

## 5. APIs e Interfaces

### 5.1 Estándares
*   **Protocolo:** REST sobre HTTPS.
*   **Formato:** JSON para control, Multipart/Form-Data para envío de audio.
*   **Autenticación:** Header `Authorization: Bearer <JWT>`.

### 5.2 Endpoints Principales

#### Módulo de Autenticación
*   `POST /api/auth/login`: Credenciales -> JWT.
*   `POST /api/auth/register`: Creación de usuario inicial.

#### Módulo de Enrolamiento
*   `POST /api/enrollment/start`: -> `{ enrollment_id, phrases[] }`
*   `POST /api/enrollment/add-sample`: `{ audio_blob, phrase_id }` -> `{ quality_score }`
*   `POST /api/enrollment/complete`: Cierra el proceso y activa el usuario.

#### Módulo de Verificación
*   `POST /api/verification/start`: -> `{ verification_id, phrase, timeout }`
*   `POST /api/verification/verify`: `{ audio_blob, verification_id }` -> `{ verified: bool, confidence: float }`

---

## 6. Seguridad y Hacking Ético

### 6.1 Vectores de Ataque Mitigados
*   **Replay Attacks (Grabaciones):** Mitigado por el sistema de "Frases Dinámicas". El usuario nunca repite la misma frase en ventanas cortas de tiempo.
*   **Synthesized Voice (TTS/Deepfakes):** Mitigado por el módulo de Anti-Spoofing que analiza micro-frecuencias no audibles para el oído humano pero presentes en audio sintético.
*   **Brute Force:** Rate limiting estricto en API (Redis) y bloqueo de cuenta tras 3 intentos fallidos consecutivos.

### 6.2 Protección de Datos
*   **Encriptación en Reposo:** Los embeddings (vectores) son datos biométricos sensibles. Se almacenan cifrados.
*   **Privacidad:** Política de retención de audio configurable. El usuario puede decidir si sus audios crudos se guardan para auditoría o se eliminan inmediatamente tras el procesamiento.

---

## 7. Instalación y Despliegue

### 7.1 Requisitos de Infraestructura
*   **CPU:** Mínimo 2 cores (4 recomendados para inferencia ML rápida).
*   **RAM:** Mínimo 4GB (8GB recomendados).
*   **Almacenamiento:** SSD recomendado para PostgreSQL.

### 7.2 Pasos de Despliegue (Docker)

1.  **Clonar y Configurar Variables:**
    ```bash
    cp Backend/.env.example Backend/.env
    # Editar Backend/.env con credenciales seguras
    ```

2.  **Construir Contenedores:**
    ```bash
    docker-compose build
    ```

3.  **Iniciar Servicios:**
    ```bash
    docker-compose up -d
    ```

4.  **Inicialización de Datos (Seed):**
    ```bash
    # Cargar esquema y frases
    docker exec -it voice_api python scripts/run_seed.py
    ```

### 7.3 Variables de Entorno Clave
*   `SIMILARITY_THRESHOLD`: (Default: `0.75`) Ajusta el balance entre Falsos Positivos y Falsos Negativos.
*   `ANTI_SPOOFING_THRESHOLD`: (Default: `0.80`) Sensibilidad del detector de vida.
*   `DB_HOST`, `DB_USER`, `DB_PASS`: Credenciales de PostgreSQL.

---

## 8. Mantenimiento y Operaciones

### 8.1 Monitoreo
*   **Logs de Aplicación:** Estructurados en JSON, ubicados en `/Backend/logs`.
*   **Métricas de Negocio:** Consultables vía endpoints de admin (`/api/admin/stats`) o directamente en SQL (vistas materializadas).

### 8.2 Escalabilidad Futura
*   **Desacoplamiento:** El módulo de inferencia ML (`Backend/src/domain/voice_engine`) puede extraerse a un microservicio GPU dedicado si la latencia aumenta.
*   **Base de Datos:** PostgreSQL soporta particionamiento de tablas y réplicas de lectura para escalar la tabla de logs y usuarios.

### 8.3 Plan de Recuperación
*   Backups diarios automáticos de la base de datos (pg_dump).
*   Los modelos ML están versionados; si un modelo falla, el sistema permite rollback a una versión anterior en la tabla `model_version`.
