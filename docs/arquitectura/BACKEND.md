# Backend Architecture Documentation

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Estructura de Directorios](#estructura-de-directorios)
4. [Capas de la Aplicación](#capas-de-la-aplicación)
5. [Componentes Principales](#componentes-principales)
6. [Flujo de Datos](#flujo-de-datos)
7. [Patrones de Diseño](#patrones-de-diseño)
8. [Tecnologías](#tecnologías)

---

## Visión General

El backend es una **API RESTful** construida con **FastAPI** que implementa un sistema de autenticación biométrica por voz. Utiliza **arquitectura hexagonal (puertos y adaptadores)** para mantener el código desacoplado y testeable.

### Características Principales

- 🎤 **Biometría de Voz**: ECAPA-TDNN para embeddings
- 🛡️ **Anti-Spoofing**: Detección de audio falsificado
- 🗣️ **ASR**: Reconocimiento de voz (Wav2Vec2)
- 🔐 **Autenticación**: JWT con refresh tokens
- 📊 **Base de Datos**: PostgreSQL con asyncpg
- 🧹 **Cleanup Jobs**: Limpieza automática de desafíos

---

## Arquitectura

### Arquitectura Hexagonal (Clean Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Auth         │  │ Enrollment   │  │ Verification │  │
│  │ Controller   │  │ Controller   │  │ Controller   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Auth         │  │ Enrollment   │  │ Verification │  │
│  │ Service      │  │ Service      │  │ Service      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Domain Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Repositories │  │ Domain       │  │ Business     │  │
│  │ (Ports)      │  │ Models       │  │ Rules        │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Infrastructure Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL   │  │ ML Models    │  │ External     │  │
│  │ Adapters     │  │ (ECAPA-TDNN) │  │ Services     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Estructura de Directorios

```
Backend/
├── src/
│   ├── api/                    # Capa de API (Controllers)
│   │   ├── middleware/         # Middlewares (auth, audit)
│   │   ├── auth_controller.py
│   │   ├── enrollment_controller.py
│   │   ├── verification_controller_v2.py
│   │   ├── challenge_controller.py
│   │   ├── admin_controller.py
│   │   └── error_handlers.py
│   │
│   ├── application/            # Capa de Aplicación (Services)
│   │   ├── dto/                # Data Transfer Objects
│   │   ├── services/           # Servicios auxiliares
│   │   ├── policies/           # Políticas de negocio
│   │   ├── auth_service.py
│   │   ├── enrollment_service.py
│   │   ├── verification_service.py
│   │   ├── challenge_service.py
│   │   └── phrase_service.py
│   │
│   ├── domain/                 # Capa de Dominio (Core)
│   │   ├── model/              # Modelos de dominio
│   │   ├── repositories/       # Interfaces (Ports)
│   │   ├── services/           # Servicios de dominio
│   │   └── policies/           # Estrategias de riesgo
│   │
│   ├── infrastructure/         # Capa de Infraestructura
│   │   ├── biometrics/         # Adaptadores ML
│   │   │   ├── SpeakerEmbeddingAdapter.py
│   │   │   ├── SpoofDetectorAdapter.py
│   │   │   ├── ASRAdapter.py
│   │   │   └── VoiceBiometricEngineFacade.py
│   │   ├── persistence/        # Adaptadores BD
│   │   │   ├── PostgresUserRepository.py
│   │   │   ├── PostgresVoiceSignatureRepository.py
│   │   │   ├── PostgresChallengeRepository.py
│   │   │   └── PostgresPhraseRepository.py
│   │   ├── security/           # Seguridad
│   │   │   ├── encryption.py
│   │   │   └── jwt_handler.py
│   │   └── config/             # Configuración
│   │       └── dependencies.py
│   │
│   ├── jobs/                   # Background Jobs
│   │   └── cleanup_expired_challenges.py
│   │
│   ├── shared/                 # Código compartido
│   │   ├── types/              # Tipos comunes
│   │   └── constants/          # Constantes
│   │
│   ├── utils/                  # Utilidades
│   │   └── validators.py
│   │
│   ├── config.py               # Configuración global
│   └── main.py                 # Punto de entrada
│
├── scripts/                    # Scripts de utilidad
│   └── create_admin_users.sql
│
├── tests/                      # Tests
│   ├── unit/
│   ├── integration/
│   └── manual/
│
├── models/                     # Modelos ML (descargados, gitignored)
│   ├── speaker-recognition/
│   └── text-verification/
│
├── requirements.txt
├── requirements-dev.txt
├── ruff.toml
├── pytest.ini
├── Dockerfile               # Build de la imagen API (compose de raíz)
└── start_server.sh
```

---

## Capas de la Aplicación

### 1. **API Layer** (`src/api/`)

**Responsabilidad**: Manejar requests HTTP, validación de entrada, serialización.

**Componentes**:
- **Controllers**: Endpoints REST
- **Middleware**: Autenticación, auditoría, CORS
- **Error Handlers**: Manejo centralizado de errores

**Ejemplo**:
```python
@router.post("/start", response_model=StartEnrollmentResponse)
async def start_enrollment(
    request: StartEnrollmentRequest,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    return await enrollment_service.start_enrollment(
        user_id=request.user_id,
        difficulty=request.difficulty
    )
```

---

### 2. **Application Layer** (`src/application/`)

**Responsabilidad**: Lógica de negocio, orquestación de casos de uso.

**Componentes**:
- **Services**: Implementan casos de uso
- **DTOs**: Objetos de transferencia de datos
- **Policies**: Políticas de negocio

**Servicios Principales**:
- `EnrollmentService`: Gestión de enrollment
- `VerificationServiceV2`: Verificación multi-frase
- `ChallengeService`: Gestión de desafíos
- `PhraseService`: Gestión de frases

**Ejemplo**:
```python
class EnrollmentService:
    async def start_enrollment(self, user_id: str, difficulty: str):
        # 1. Validar usuario
        # 2. Crear challenges
        # 3. Iniciar sesión de enrollment
        # 4. Retornar challenges
```

---

### 3. **Domain Layer** (`src/domain/`)

**Responsabilidad**: Modelos de dominio, reglas de negocio core.

**Componentes**:
- **Models**: Entidades del dominio
- **Repository Ports**: Interfaces (contratos)
- **Domain Services**: Lógica de dominio pura
- **Policies**: Estrategias (Strategy Pattern)

**Ejemplo**:
```python
class ChallengeRepositoryPort(ABC):
    @abstractmethod
    async def create_challenge(self, ...): pass
    
    @abstractmethod
    async def get_challenge(self, challenge_id): pass
```

---

### 4. **Infrastructure Layer** (`src/infrastructure/`)

**Responsabilidad**: Implementaciones concretas, acceso a recursos externos.

**Componentes**:

#### **Biometrics** (`infrastructure/biometrics/`)
- `SpeakerEmbeddingAdapter`: ECAPA-TDNN
- `SpoofDetectorAdapter`: Anti-spoofing
- `ASRAdapter`: Wav2Vec2 para ASR
- `VoiceBiometricEngineFacade`: Facade pattern

#### **Persistence** (`infrastructure/persistence/`)
- `PostgresUserRepository`
- `PostgresVoiceSignatureRepository`
- `PostgresChallengeRepository`
- `PostgresPhraseRepository`

#### **Security** (`infrastructure/security/`)
- `encryption.py`: Encriptación de embeddings
- `jwt_handler.py`: Manejo de JWT

---

## Componentes Principales

### 1. **Voice Biometric Engine**

```python
VoiceBiometricEngineFacade
├── SpeakerEmbeddingAdapter (ECAPA-TDNN)
├── SpoofDetectorAdapter (RawNet2/AASIST)
└── ASRAdapter (Wav2Vec2)
```

**Funciones**:
- Extraer embeddings de voz
- Detectar spoofing
- Transcribir audio (ASR)

---

### 2. **Challenge System**

```python
ChallengeService
├── Phrase Database (37,407 frases)
├── Difficulty-based Timeouts
│   ├── Easy: 60s
│   ├── Medium: 90s
│   └── Hard: 120s
└── Cleanup Job (cada 30s)
```

**Funciones**:
- Generar desafíos dinámicos
- Expiración automática
- Limpieza de desafíos viejos

---

### 3. **Authentication System**

```python
AuthService
├── JWT Tokens (access + refresh)
├── Password Hashing (bcrypt)
└── Session Management
```

**Funciones**:
- Login/Logout
- Gestión de tokens
- Cambio de contraseña

---

### 4. **Database Schema**

**Tablas Principales**:
- `user`: Usuarios del sistema
- `voiceprint`: Huellas de voz (embeddings)
- `enrollment_sample`: Muestras de enrollment
- `challenge`: Desafíos dinámicos
- `phrase`: Base de datos de frases
- `auth_attempt`: Intentos de autenticación
- `scores`: Scores biométricos
- `audit_log`: Logs de auditoría

---

## Flujo de Datos

### Enrollment Flow

```
1. Usuario → POST /api/enrollment/start
   ↓
2. EnrollmentService.start_enrollment()
   ↓
3. ChallengeService.create_challenge_batch(5)
   ↓
4. PhraseRepository.find_random()
   ↓
5. Return 5 challenges
   ↓
6. Usuario graba 5 muestras → POST /api/enrollment/add-sample
   ↓
7. VoiceBiometricEngine.get_speaker_embedding()
   ↓
8. EnrollmentSampleRepository.save()
   ↓
9. Usuario → POST /api/enrollment/complete
   ↓
10. VoiceSignatureRepository.create_voiceprint()
    ↓
11. Enrollment completado ✅
```

---

### Verification Flow

```
1. Usuario → POST /api/verification/start-multi
   ↓
2. VerificationService.start_multi_phrase()
   ↓
3. ChallengeService.create_challenge_batch(3)
   ↓
4. Return 3 challenges
   ↓
5. Usuario graba frase → POST /api/verification/verify-phrase
   ↓
6. VoiceBiometricEngine.verify_speaker()
   ├── Speaker Similarity Score
   ├── Anti-Spoofing Score
   └── ASR Score
   ↓
7. DecisionService.evaluate()
   ↓
8. AuthAttemptRepository.save()
   ↓
9. Repeat for 3 phrases
   ↓
10. Calculate average score
    ↓
11. Verification result ✅/❌
```

---

## Patrones de Diseño

### 1. **Repository Pattern**
```python
# Port (Interface)
class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, user_id): pass

# Adapter (Implementation)
class PostgresUserRepository(UserRepositoryPort):
    async def get_by_id(self, user_id):
        # PostgreSQL implementation
```

### 2. **Facade Pattern**
```python
class VoiceBiometricEngineFacade:
    def __init__(self, speaker_adapter, spoof_adapter, asr_adapter):
        self._speaker = speaker_adapter
        self._spoof = spoof_adapter
        self._asr = asr_adapter
    
    async def verify_speaker(self, audio):
        # Orchestrates all biometric checks
```

### 3. **Strategy Pattern**
```python
class RiskPolicyStrategy(ABC):
    @abstractmethod
    def evaluate(self, scores): pass

class StrictPolicy(RiskPolicyStrategy):
    def evaluate(self, scores):
        return scores.similarity > 0.85

class RelaxedPolicy(RiskPolicyStrategy):
    def evaluate(self, scores):
        return scores.similarity > 0.65
```

### 4. **Dependency Injection**
```python
# FastAPI Depends
async def get_enrollment_service() -> EnrollmentService:
    pool = await get_db_pool()
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = PostgresUserRepository(pool)
    return EnrollmentService(voice_repo, user_repo, ...)
```

### 5. **Builder Pattern**
```python
class ResultBuilder:
    def with_similarity(self, score): ...
    def with_spoofing(self, score): ...
    def with_asr(self, score): ...
    def build(self): ...
```

---

## Tecnologías

### Core
- **FastAPI**: Framework web asíncrono
- **Python 3.13**: Lenguaje
- **asyncpg**: Cliente PostgreSQL asíncrono
- **Pydantic**: Validación de datos

### Machine Learning
- **PyTorch**: Framework ML
- **SpeechBrain**: ECAPA-TDNN
- **Transformers**: Wav2Vec2
- **torchaudio**: Procesamiento de audio

### Base de Datos
- **PostgreSQL 16**: Base de datos principal
- **pgvector**: Extensión para embeddings
- **pgcrypto**: Extensión para encriptación

### Seguridad
- **PyJWT**: JSON Web Tokens
- **bcrypt**: Hashing de contraseñas
- **cryptography**: Encriptación de embeddings

### Infraestructura
- **Docker**: Containerización
- **Docker Compose**: Orquestación
- **Uvicorn**: Servidor ASGI

### Desarrollo
- **pytest**: Testing
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Linting

---

## Configuración

### Variables de Entorno (`.env`)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=voice_password

# Security
SECRET_KEY=your-secret-key
EMBEDDING_ENCRYPTION_KEY=your-encryption-key

# API
CORS_ALLOWED_ORIGINS=http://localhost:5173
RATE_LIMIT=100/minute

# Thresholds
SIMILARITY_THRESHOLD=0.60
ANTI_SPOOFING_THRESHOLD=0.5
```

---

## Background Jobs

### Cleanup Job

**Archivo**: `src/jobs/cleanup_expired_challenges.py`

**Función**: Limpia desafíos expirados cada 30 segundos

**Inicio**: Automático al arrancar el servidor

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cleanup job
    cleanup_task = asyncio.create_task(
        cleanup_expired_challenges_job(challenge_repo, 30)
    )
    
    yield
    
    # Cancel on shutdown
    cleanup_task.cancel()
```

---

## Seguridad

### 1. **Autenticación**
- JWT con access + refresh tokens
- Tokens firmados con HS256
- Expiración configurable

### 2. **Encriptación**
- Embeddings encriptados en BD (Fernet)
- Contraseñas hasheadas (bcrypt)
- HTTPS en producción

### 3. **Rate Limiting**
- 100 req/min global
- 3 desafíos activos por usuario
- 50 desafíos/hora por usuario

### 4. **Validación**
- Pydantic para request validation
- Sanitización de inputs
- CORS configurado

---

## Testing

### Estructura
```
tests/
├── unit/
│   ├── test_services.py
│   ├── test_repositories.py
│   └── test_biometrics.py
└── integration/
    ├── test_api.py
    └── test_database.py
```

### Ejecutar Tests
```bash
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

---

## Deployment

### Docker
```bash
docker-compose up -d
```

### Manual
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python scripts/run_seed.py

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Próximos Pasos

- [ ] Implementar tests automatizados
- [ ] Agregar CI/CD pipeline
- [ ] Configurar Kubernetes
- [ ] Implementar backup automático
- [ ] Agregar más métricas de monitoreo

---

## Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SpeechBrain](https://speechbrain.github.io/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
