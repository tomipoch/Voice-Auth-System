# 📘 Documentación Completa del Sistema de Biometría de Voz

> **Generado automáticamente el 14 de Diciembre de 2025**
> Este documento consolida toda la información técnica, arquitectónica y operativa del repositorio, incluyendo Backend, Frontend (App) y Base de Datos.

---

## 📑 Tabla de Contenidos

1. [Visión General del Proyecto](#visión-general-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Base de Datos (Schema y Modelado)](#base-de-datos)
5. [Backend (API y Servicios)](#backend)
6. [Frontend (App y UI/UX)](#frontend)
7. [Configuración y Variables de Entorno](#configuración)
8. [Guía de Instalación y Despliegue](#instalación-y-despliegue)

---

## 1. <a name="visión-general-del-proyecto"></a>Visión General del Proyecto

Este proyecto es un sistema avanzado de **Autenticación Biométrica por Voz** que utiliza inteligencia artificial para verificar la identidad de usuarios basándose en las características únicas de su voz. El sistema está diseñado para ser seguro, robusto y resistente a ataques de suplantación (anti-spoofing).

### Características Principales
*   **Biometría de Voz**: Verificación de identidad mediante embeddings de voz.
*   **Detección de Vida (Liveness)**: Uso de frases dinámicas aleatorias para evitar ataques de repetición (Replay Attacks).
*   **Frases Dinámicas**: Base de datos con más de 43,000 frases extraídas de literatura clásica para garantizar entropía en los desafíos.
*   **Seguridad**: Encriptación de datos sensibles, logs de auditoría inmutables y gestión de sesiones segura.
*   **Arquitectura Moderna**: Backend asíncrono con FastAPI y Frontend reactivo con React.

---

## 2. <a name="arquitectura-del-sistema"></a>Arquitectura del Sistema

El proyecto sigue una arquitectura de **Monorepo** con separación clara de responsabilidades:

```
/
├── App/ (Frontend)      -> Cliente Web React (Vite + TypeScript)
├── Backend/ (Backend)   -> API REST FastAPI (Python + ML Models)
├── Database/ (Data)     -> Scripts SQL, Migraciones y PDFs fuente
└── docs/                -> Documentación transversal
```

### Flujos de Datos

#### 1. Enrolamiento (Registro de Voz)
1.  El usuario solicita iniciar enrolamiento.
2.  Backend selecciona 3-5 frases aleatorias (nivel de dificultad configurable).
3.  Usuario graba su voz leyendo cada frase.
4.  Backend procesa el audio:
    *   Verifica calidad (SNR).
    *   Genera embeddings con modelos de IA.
5.  Al completar, se crea un `voiceprint` (huella de voz) promedio y se guarda encriptado.

#### 2. Verificación (Login por Voz)
1.  Usuario solicita acceso.
2.  Backend envía un "desafío" (frase aleatoria no usada recientemente).
3.  Usuario graba el audio.
4.  Backend valida:
    *   **Speaker Verification**: ¿Es la misma persona? (Similitud de cosenos > umbral).
    *   **Anti-Spoofing**: ¿Es una grabación o una voz real?
    *   **ASR (Speech-to-Text)**: ¿Dijo la frase correcta?
5.  Si todo aprueba, se concede acceso y se registra en auditoría.

---

## 3. <a name="stack-tecnológico"></a>Stack Tecnológico

### Backend
*   **Lenguaje**: Python 3.11+
*   **Framework Web**: FastAPI (Asíncrono)
*   **IA/ML**:
    *   `SpeechBrain`: Procesamiento de audio y embeddings.
    *   `PyTorch`: Motor de tensores.
    *   `pgvector`: Búsqueda vectorial en base de datos.
*   **Seguridad**: `python-jose` (JWT), `passlib` (Hashing).
*   **Contenedor**: Docker.

### Frontend
*   **Framework**: React 19+
*   **Build Tool**: Vite
*   **Lenguaje**: TypeScript
*   **Estilos**: Tailwind CSS
*   **Estado Servidor**: TanStack Query (React Query)
*   **HTTP Client**: Axios

### Base de Datos
*   **Motor**: PostgreSQL 16+
*   **Extensiones**:
    *   `pgvector`: Almacenamiento y búsqueda de embeddings de voz.
    *   `pgcrypto`: Funciones criptográficas para seguridad.
*   **Cache**: Redis (para sesiones y rate limiting).

---

## 4. <a name="base-de-datos"></a>Base de Datos

El esquema de base de datos está diseñado para alta seguridad y trazabilidad. A continuación se detalla el esquema completo (`Database/init.sql`).

### Tablas Principales

#### `user`
Almacena la identidad de los usuarios.
- `id`: UUID.
- `email`: Identificador único.
- `role`: 'user', 'admin', 'superadmin'.
- `failed_auth_attempts`: Para bloqueo de cuentas.

#### `voiceprint`
Almacena la huella biométrica del usuario.
- `embedding`: Vector binario (BYTEA) con la firma de voz encriptada.
- `user_id`: Referencia al usuario.

#### `phrase`
Catálogo de frases para desafíos.
- `text`: Contenido de la frase.
- `difficulty`: 'easy', 'medium', 'hard'.
- `source`: Libro de origen.

#### `auth_attempt` y `scores`
Registro detallado de cada intento de acceso.
- `auth_attempt`: Decisión de negocio (Aceptado/Rechazado, Razón).
- `scores`: Métricas técnicas (Similitud, Spoof Probability, Phrase Match).

#### `audit_log`
Log inmutable de operaciones críticas.
- `actor`: Quién realizó la acción.
- `action`: Qué hizo (ENROLL, VERIFY, DELETE).
- `metadata`: JSON con detalles.

### Script de Inicialización (Extracto Resumido)

```sql
-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- pgvector se asume instalado en la imagen de Docker

-- Usuarios
CREATE TABLE "user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  password TEXT,
  role TEXT DEFAULT 'user',
  -- ... traza de seguridad
);

-- Huellas de Voz
CREATE TABLE voiceprint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id),
  embedding BYTEA NOT NULL, -- Encriptado
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Frases (Desafíos)
CREATE TABLE phrase (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text TEXT NOT NULL,
  difficulty TEXT,
  source TEXT
);

-- Auditoría
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ DEFAULT now(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  metadata JSONB
);
```

---

## 5. <a name="backend"></a>Backend (API y Servicios)

El backend expone una API RESTful documentada automáticamente mediante Swagger/OpenAPI.

### Endpoints Clave

#### Autenticación (`/api/auth`)
*   `POST /register`: Crear nueva cuenta.
*   `POST /login`: Obtener JWT.
*   `POST /refresh`: Renovar token.

#### Enrolamiento (`/api/enrollment`)
*   `POST /start`: Inicia sesión de enrolamiento, devuelve lista de frases.
*   `POST /add-sample`: Sube audio para una frase específica.
*   `POST /complete`: Finaliza el proceso y genera el `voiceprint`.

#### Verificación (`/api/verification`)
*   `POST /start-multi`: Inicia verificación (1-3 frases).
*   `POST /verify-phrase`: Verifica una muestra de audio. Devuelve scores parciales.

#### Administración (`/api/admin`)
*   `GET /users`: Listado de usuarios.
*   `GET /stats`: Métricas globales del sistema.
*   `GET /phrase-rules`: Configuración de reglas de negocio.

### Estructura de Directorios (`Backend/src`)
*   `api/`: Routers y controladores.
*   `application/`: Lógica de negocio y Casos de Uso (Services).
*   `domain/`: Modelos de dominio y excepciones.
*   `infrastructure/`: Repositorios (DB), Servicios externos (ML), Config.
*   `models/`: Modelos de ML serializados o configuraciones.

---

## 6. <a name="frontend"></a>Frontend (App y UI/UX)

La aplicación web ofrece una interfaz intuitiva para el proceso biométrico.

### Componentes Clave (`App/src/components`)
*   **`DynamicEnrollment`**: Wizard paso a paso para el registro de voz. Maneja la grabación, subida y feedback visual de calidad de audio.
*   **`DynamicVerification`**: Interfaz de login. Muestra la frase desafío y feedback en tiempo real del resultado (Scores de similitud y anti-spoofing).
*   **`AudioRecorder`**: Componente reutilizable para capturar audio del micrófono, visualizar ondas de sonido y gestionar permisos.

### Páginas (`App/src/pages`)
*   `EnrollmentPage`: Vista principal de registro biométrico.
*   `VerificationPage`: Vista de prueba de verificación.
*   `LoginPage` / `RegisterPage`: Autenticación tradicional.
*   `AdminDashboard`: Panel de control para administradores.

### Integración API (`App/src/services`)
*   `enrollmentService.ts`: Maneja el flujo de estado del enrolamiento.
*   `verificationService.ts`: Coordina las llamadas de verificación.
*   `authService.ts`: Gestión de tokens JWT.

---

## 7. <a name="configuración"></a>Configuración y Variables de Entorno

### Backend (`Backend/.env`)

```ini
# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=xxxx

# Servidor API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Seguridad (JWT)
SECRET_KEY=xxxx
JWT_SECRET_KEY=xxxx
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Modelos ML
MODEL_CACHE_DIR=./models
DEVICE=cpu # o cuda
MAX_AUDIO_SIZE_MB=10
```

### Frontend (`App/.env`)

```ini
# Conexión API
VITE_API_URL=http://localhost:8000/api
VITE_BACKEND_URL=http://localhost:8000

# Configuración Audio
VITE_AUDIO_SAMPLE_RATE=16000
VITE_AUDIO_MAX_DURATION=10
```

---

## 8. <a name="instalación-y-despliegue"></a>Guía de Instalación y Despliegue

### Requisitos Previos
*   Docker y Docker Compose
*   Node.js 18+ (para desarrollo local frontend)
*   Python 3.11+ (para desarrollo local backend)

### Despliegue con Docker (Recomendado)

1.  **Clonar repositorio y navegar a Backend**:
    ```bash
    cd Backend
    ```
2.  **Iniciar servicios (DB, Redis, API)**:
    ```bash
    docker-compose up -d --build
    ```
3.  **Inicializar Base de Datos**:
    ```bash
    # Cargar schema
    docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < ../Database/init.sql
    
    # Cargar frases (Seed)
    docker exec -it voice_biometrics_api python scripts/extract_phrases.py
    ```

### Ejecución Local (Desarrollo)

**Backend**:
```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start_server.sh
```

**Frontend**:
```bash
cd App
npm install
npm run dev
```

El sistema estará disponible en:
*   Frontend: `http://localhost:5173`
*   Backend API Docs: `http://localhost:8000/docs`
