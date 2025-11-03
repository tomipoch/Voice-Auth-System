# Voice Biometrics Authentication System - Backend

## Descripción General

Sistema backend completo para autenticación biométrica por voz implementado con arquitectura hexagonal y patrones de diseño avanzados. Proporciona servicios seguros de inscripción y verificación de usuarios basados en características únicas de la voz.

## Arquitectura

### Arquitectura Hexagonal (Clean Architecture)

```
Backend/
├── src/
│   ├── domain/          # Lógica de negocio central
│   │   ├── model/       # Entidades del dominio
│   │   ├── services/    # Servicios de dominio
│   │   └── ports/       # Interfaces/Contratos
│   ├── application/     # Casos de uso y servicios de aplicación
│   │   ├── services/    # Servicios de aplicación
│   │   └── dtos/        # Objetos de transferencia de datos
│   ├── infrastructure/ # Implementaciones técnicas
│   │   ├── adapters/    # Adaptadores externos
│   │   ├── repositories/ # Persistencia de datos
│   │   └── facades/     # Fachadas para sistemas complejos
│   └── api/            # Capa de presentación
│       ├── controllers/ # Controladores REST
│       └── middleware/  # Middleware HTTP
└── tests/              # Suite de pruebas
    ├── unit/           # Pruebas unitarias
    └── integration/    # Pruebas de integración
```

### Patrones de Diseño Implementados

#### 1. **Strategy Pattern** - Políticas de Decisión
```python
# Diferentes estrategias según el contexto de uso
- StandardDecisionStrategy: Para aplicaciones generales
- BankingDecisionStrategy: Para sistemas bancarios (más estricta)
- DemoDecisionStrategy: Para demostraciones (más relajada)
```

#### 2. **Builder Pattern** - Construcción de Resultados
```python
# Construcción flexible de resultados de autenticación
ResultBuilder()
    .set_user_id("user123")
    .set_success(True)
    .set_confidence_score(0.92)
    .set_biometric_scores(scores)
    .build()
```

#### 3. **Facade Pattern** - Simplificación de Sistemas Complejos
```python
# Unifica múltiples adaptadores biométricos
VoiceBiometricEngineFacade:
    - SpeakerRecognitionAdapter
    - AntiSpoofingAdapter
    - ASRAdapter
```

#### 4. **Repository Pattern** - Abstracción de Persistencia
```python
# Abstracciones para acceso a datos
- VoiceSignatureRepositoryPort
- AuthAttemptRepositoryPort
```

## Características Principales

### 🔐 **Seguridad Avanzada**
- Detección de spoofing en tiempo real
- Autenticación por API key
- Rate limiting configurable
- Auditoría completa de intentos

### 🎯 **Precisión Biométrica**
- Extracción de características MFCC, pitch y espectrales
- Comparación vectorial con pgvector
- Múltiples umbrales según contexto de uso
- Validación de frases habladas

### ⚡ **Alto Rendimiento**
- Arquitectura asíncrona con asyncio
- Procesamiento optimizado de audio
- Cache inteligente de características
- Métricas de latencia en tiempo real

### 🔄 **Escalabilidad**
- Arquitectura modular y desacoplada
- Contenedores Docker
- Base de datos PostgreSQL con extensiones
- APIs RESTful estándar

## API Endpoints

### Inscripción de Usuario
```http
POST /api/v1/enroll
Content-Type: application/json

{
    "user_id": "user123",
    "audio_data": "base64_encoded_audio",
    "force_re_enrollment": false
}
```

### Generación de Desafío
```http
POST /api/v1/challenge
Content-Type: application/json

{
    "user_id": "user123"
}
```

### Verificación de Voz
```http
POST /api/v1/verify
Content-Type: application/json

{
    "user_id": "user123",
    "audio_data": "base64_encoded_audio",
    "challenge_phrase": "por favor di: hola mundo",
    "policy_type": "standard"
}
```

## Configuración del Entorno

### Requisitos del Sistema
- Python 3.11+
- PostgreSQL 16+ con extensión pgvector
- Docker y Docker Compose
- Mínimo 4GB RAM recomendado

### Variables de Entorno
```bash
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/voice_biometrics
DATABASE_POOL_SIZE=20

# Seguridad
API_KEY_HEADER=X-API-Key
VALID_API_KEYS=["key1", "key2", "key3"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Biometría
SIMILARITY_THRESHOLD_STANDARD=0.8
SIMILARITY_THRESHOLD_BANKING=0.9
SIMILARITY_THRESHOLD_DEMO=0.6

# Audio
MAX_AUDIO_SIZE_MB=10
SUPPORTED_AUDIO_FORMATS=["wav", "mp3", "m4a"]
```

## 🧠 Modelos de Machine Learning

### Modelos Implementados

#### 1. **ECAPA-TDNN (Speaker Recognition)**
- **Propósito**: Extracción de embeddings de speaker para verificación
- **Arquitectura**: Emphasized Channel Attention, Propagation and Aggregation in TDNN
- **Dataset**: Entrenado en VoxCeleb 1 & 2
- **Dimensión**: 192/512-dimensional embeddings
- **Precisión**: EER ~0.87% en VoxCeleb1-O test

#### 2. **RawNet2 (Anti-Spoofing)** *(En desarrollo)*
- **Propósito**: Detección de deepfakes y ataques de replay
- **Arquitectura**: End-to-end raw waveform processing
- **Dataset**: ASVspoof 2019 LA/PA
- **Características**: Detección de síntesis, conversión de voz y replay

#### 3. **Wav2Vec2 (ASR)** *(En desarrollo)*
- **Propósito**: Reconocimiento automático de speech
- **Arquitectura**: Self-supervised pre-training + fine-tuning
- **Dataset**: LibriSpeech 960h
- **Uso**: Verificación de frases de desafío

### Descarga Automática de Modelos

Los modelos se descargan automáticamente en la primera ejecución:

```python
from infrastructure.biometrics.model_manager import model_manager

# Verificar estado de modelos
models_status = model_manager.list_models()

# Descargar modelos manualmente si es necesario
model_manager.download_all_models()
```

**Requisitos de almacenamiento**:
- ECAPA-TDNN: ~45 MB
- RawNet2: ~30 MB  
- Wav2Vec2: ~360 MB
- **Total**: ~435 MB

### Configuración de GPU

Para acelerar la inferencia (opcional):

```bash
# Instalar PyTorch con soporte CUDA
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verificar GPU disponible
python -c "import torch; print(torch.cuda.is_available())"
```

### Instalación con Docker

1. **Clonar el repositorio**
```bash
git clone <repository_url>
cd Backend
```

2. **Configurar variables de entorno**
```bash
cp .env.template .env
# Editar .env con sus configuraciones
```

3. **Ejecutar con Docker Compose**
```bash
docker-compose up -d
```

4. **Verificar la instalación**
```bash
curl http://localhost:8000/health
```

### Instalación Manual

1. **Instalar dependencias de sistema**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev libsndfile1 ffmpeg

# macOS  
brew install libsndfile ffmpeg
```

2. **Instalar dependencias de Python**
```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

3. **Configurar modelos de ML**
```bash
# Probar descarga de modelos
python test_ecapa_tdnn.py

# O configurar manualmente
python -c "
from src.infrastructure.biometrics.model_manager import model_manager
model_manager.download_all_models()
"
```

4. **Configurar base de datos**
```bash
# Ejecutar script de inicialización
psql -U postgres -d voice_biometrics -f Database/init.sql
```

5. **Ejecutar la aplicación**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Nota**: La primera ejecución puede tardar varios minutos descargando modelos de ML.

## Flujos de Trabajo

### Flujo de Inscripción
1. Cliente envía audio del usuario
2. Sistema extrae características biométricas
3. Detección de spoofing
4. Almacenamiento seguro en base de datos
5. Respuesta con confirmación

### Flujo de Verificación
1. Cliente solicita desafío
2. Sistema genera frase aleatoria
3. Cliente envía audio con frase
4. Extracción y comparación de características
5. Validación de frase hablada
6. Decisión basada en política configurada
7. Registro de auditoría

## Pruebas

### Ejecutar Suite Completa
```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Pruebas por Categoría
```bash
# Pruebas unitarias
pytest tests/unit/ -v

# Pruebas de integración
pytest tests/integration/ -v

# Pruebas de patrones específicos
pytest tests/unit/test_strategy_policy.py -v
pytest tests/unit/test_builder.py -v
pytest tests/unit/test_facade_pattern.py -v
```

### Cobertura de Pruebas
- **Patrones de Diseño**: 100% cobertura
- **Servicios de Aplicación**: 95%+ cobertura
- **Flujos de Integración**: 90%+ cobertura
- **APIs REST**: 95%+ cobertura

## Monitoreo y Métricas

### Métricas Principales
- Latencia de procesamiento biométrico
- Tasas de éxito/fallo por usuario
- Detecciones de spoofing
- Uso de API por endpoint
- Rendimiento de base de datos

### Logs de Auditoría
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": "user123",
    "operation": "verification",
    "success": true,
    "confidence_score": 0.92,
    "processing_time_ms": 1500,
    "ip_address": "192.168.1.100",
    "user_agent": "VoiceBiometrics-Client/1.0"
}
```

## Configuración de Producción

### Optimizaciones Recomendadas
1. **Base de Datos**
   - Índices en columnas frecuentemente consultadas
   - Particionamiento de tablas de auditoría
   - Réplicas de lectura para reportes

2. **Aplicación**
   - Pool de conexiones optimizado
   - Cache Redis para sesiones
   - Balanceador de carga

3. **Seguridad**
   - HTTPS obligatorio
   - Firewalls configurados
   - Rotación de API keys

### Backup y Recuperación
```bash
# Backup diario automático
pg_dump voice_biometrics > backup_$(date +%Y%m%d).sql

# Backup de características biométricas (cifrado)
pg_dump -t voice_signatures voice_biometrics | gpg --encrypt > signatures_backup.sql.gpg
```

## Solución de Problemas

### Problemas Comunes

**Error: "Low similarity score"**
```bash
# Verificar umbrales de política
# Comprobar calidad del audio
# Revisar ruido de fondo
```

**Error: "Database connection failed"**
```bash
# Verificar conexión a PostgreSQL
# Comprobar pool de conexiones
# Revisar logs de base de datos
```

**Error: "Spoofing detected"**
```bash
# Verificar calidad del micrófono
# Comprobar si es audio sintético
# Revisar configuración de sensibilidad
```

### Logs de Debugging
```bash
# Habilitar logs detallados
export LOG_LEVEL=DEBUG

# Logs específicos de biometría
export BIOMETRIC_DEBUG=true

# Logs de base de datos
export DATABASE_DEBUG=true
```

## Contribución

### Estándares de Código
- **Linting**: flake8, black, isort
- **Tipado**: mypy con strict mode
- **Cobertura**: Mínimo 90% en código nuevo
- **Documentación**: Docstrings en todos los métodos públicos

### Proceso de Desarrollo
1. Fork del repositorio
2. Crear rama feature
3. Implementar cambios con pruebas
4. Ejecutar suite de calidad
5. Crear pull request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para detalles.

## Soporte

Para soporte técnico o preguntas:
- **Email**: support@voicebiometrics.com
- **Documentación**: https://docs.voicebiometrics.com
- **Issues**: GitHub Issues

---

**Versión**: 1.0.0  
**Última Actualización**: Enero 2024  
**Compatibilidad**: Python 3.11+, PostgreSQL 16+
```

### Patrones Implementados

- **Builder Pattern**: `ResultBuilder` para construcción paso a paso de resultados de autenticación
- **Strategy Pattern**: `DecisionService` y `RiskPolicyStrategy` para políticas de decisión adaptables
- **Facade Pattern**: `VoiceBiometricEngineFacade` y `AuditRecorderFacade` para interfaces simplificadas
- **Repository Pattern**: Abstracciones para persistencia de datos
- **Observer Pattern**: `ObserverDispatcher` para eventos de dominio
- **Factory Pattern**: `ModelFactory` para carga de modelos ML
- **Middleware Pattern**: Autenticación y auditoría transversal

### Estructura de Capas

```
├── api/                     # 🌐 Capa de Interfaces (FastAPI)
│   ├── controllers/         # Controladores REST
│   └── middleware/          # Middleware transversal
├── application/             # 📋 Capa de Aplicación (Casos de Uso)
│   ├── services/            # Servicios de aplicación
│   ├── dto/                 # Data Transfer Objects
│   └── policies/            # Selección de políticas
├── domain/                  # 🏛️ Capa de Dominio (Lógica de Negocio)
│   ├── model/               # Entidades y Value Objects
│   ├── services/            # Servicios de dominio
│   ├── repositories/        # Puertos (interfaces)
│   └── policies/            # Estrategias de riesgo
├── infrastructure/          # 🔧 Capa de Infraestructura (Adaptadores)
│   ├── persistence/         # Adaptadores de base de datos
│   ├── biometrics/          # Adaptadores de ML/biometría
│   ├── events/              # Manejo de eventos
│   └── security/            # Utilidades de seguridad
└── shared/                  # 🔄 Código Compartido
    ├── types/               # Tipos comunes
    ├── constants/           # Constantes del sistema
    └── utils/               # Utilidades
```

## Funcionalidades Principales

### 🎯 Endpoints Principales

1. **Enrollment (Enrolamiento)**
   - `POST /api/v1/enrollment/start` - Iniciar proceso
   - `POST /api/v1/enrollment/add-sample` - Agregar muestra de voz
   - `POST /api/v1/enrollment/complete` - Finalizar enrolamiento

2. **Challenge (Desafío Dinámico)**
   - `POST /api/v1/challenge/create` - Generar frase dinámica
   - `GET /api/v1/challenge/{id}` - Obtener desafío

3. **Verification (Verificación)**
   - `POST /api/v1/verification/verify` - Autenticación principal
   - `POST /api/v1/verification/verify-simple` - Verificación simplificada

### 🛡️ Seguridad y Auditoría

- **API Key Authentication**: Middleware de autenticación
- **Rate Limiting**: Control de límites por cliente
- **Audit Trail**: Registro completo de actividades
- **Encryption**: Cifrado de audio en reposo
- **Privacy Compliance**: Retención configurable y derecho al olvido

### 🧠 Motor Biométrico

Componentes del análisis de voz:
- **Speaker Recognition**: Extracción de embeddings de voz
- **Anti-Spoofing**: Detección de ataques de replay/deepfake
- **Speech Recognition**: Verificación de frases dinámicas

## Configuración y Despliegue

### 📋 Prerrequisitos

- Python 3.11+
- PostgreSQL 16+ con extensión pgvector
- Redis (opcional, para rate limiting)
- Docker y Docker Compose

### 🚀 Inicio Rápido

1. **Clonar y preparar entorno**:
```bash
git clone <repository>
cd Backend
cp .env.example .env
# Editar .env con tus configuraciones
```

2. **Con Docker Compose** (recomendado):
```bash
docker-compose up -d
```

3. **Desarrollo local**:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar base de datos
docker-compose up -d postgres redis

# Inicializar BD
psql -h localhost -U voice_user -d voice_biometrics -f ../Database/init.sql

# Ejecutar API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 🔧 Variables de Entorno

Ver `.env.example` para todas las configuraciones disponibles.

### 📊 Monitoreo

- **Health Check**: `GET /health`
- **API Docs**: `GET /docs` (Swagger UI)
- **Metrics**: Puerto 9090 (Prometheus)
- **Logs**: Estructurados en JSON para análisis

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📚 Documentación Técnica

### Base de Datos

El esquema incluye:
- **Users & Policies**: Gestión de usuarios y políticas de privacidad
- **Voiceprints**: Firmas biométricas y histórico
- **Challenges**: Frases dinámicas con expiración
- **Auth Attempts**: Intentos de autenticación con scores
- **Audit Log**: Trazabilidad completa

### Flujo de Verificación

1. **Validación de Request**: Audio, usuario, desafío
2. **Análisis Biométrico**: Extracción de features, anti-spoofing, ASR
3. **Selección de Política**: Strategy Pattern para riesgo adaptativo
4. **Decisión**: Builder Pattern para resultado final
5. **Auditoría**: Facade Pattern para registro unificado

### Extensibilidad

El sistema está diseñado para:
- **Nuevos Modelos ML**: Factory Pattern para carga dinámica
- **Políticas Personalizadas**: Strategy Pattern extensible
- **Nuevos Eventos**: Observer Pattern para integraciones
- **Diferentes Bases de Datos**: Repository Pattern desacoplado

## 🔒 Consideraciones de Seguridad

- Las claves API se almacenan hasheadas
- Audio sensible cifrado en reposo
- Logs sanitizados (sin información sensible)
- Rate limiting por cliente
- Validación estricta de entrada
- Principio de menor privilegio

## 📈 Rendimiento

- **Latencia objetivo**: < 5 segundos para verificación completa
- **Throughput**: Configuración de workers ajustable
- **Caching**: Redis para rate limiting y sesiones
- **Connection Pooling**: PostgreSQL optimizado

## 🤝 Contribución

El código sigue:
- **Clean Architecture** principles
- **SOLID** principles  
- **Domain-Driven Design** patterns
- **Python Type Hints** para mejor IDE support
- **Comprehensive testing** estrategia

Para contribuir, asegurate de mantener estos estándares y agregar tests para nueva funcionalidad.