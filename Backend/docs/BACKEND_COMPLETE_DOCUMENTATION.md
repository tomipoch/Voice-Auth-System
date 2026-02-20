# Documentación Completa del Backend - Voice Biometrics System

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura de Directorios](#estructura-de-directorios)
4. [API Reference](#api-reference)
5. [Servicios y Lógica de Negocio](#servicios-y-lógica-de-negocio)
6. [Modelos de Dominio](#modelos-de-dominio)
7. [Base de Datos](#base-de-datos)
8. [Seguridad](#seguridad)
9. [Modelos de Machine Learning](#modelos-de-machine-learning)
10. [Configuración y Deployment](#configuración-y-deployment)
11. [Flujos Principales](#flujos-principales)
12. [Testing](#testing)
13. [Performance y Optimización](#performance-y-optimización)

---

## 1. Visión General

### Descripción del Sistema

El **Voice Biometrics Backend** es una API REST construida con FastAPI que implementa un sistema completo de autenticación biométrica por voz. El sistema utiliza técnicas avanzadas de Machine Learning para:

- **Enrollment**: Registro de huellas de voz de usuarios
- **Verification**: Autenticación de usuarios mediante voz
- **Anti-Spoofing**: Detección de intentos de fraude (deepfakes, replay attacks)
- **Text Verification**: Validación de frases mediante ASR

### Características Principales

✅ **Arquitectura Hexagonal** (Clean Architecture)  
✅ **Async/Await** con asyncpg para alta concurrencia  
✅ **Multi-phrase Verification** para mayor seguridad  
✅ **Dynamic Phrase System** con 43,459 frases únicas  
✅ **Ensemble Anti-Spoofing** (AASIST + RawNet2 + Nes2Net)  
✅ **JWT Authentication** con refresh tokens  
✅ **Rate Limiting** y protección CSRF  
✅ **Docker Ready** con multi-stage builds  
✅ **Comprehensive Logging** y auditoría

### Stack Tecnológico

| Categoría | Tecnologías |
|-----------|------------|
| **Framework** | FastAPI 0.115.6, Python 3.11+ |
| **Database** | PostgreSQL 16 con pgvector |
| **ML/AI** | PyTorch 2.6.0, SpeechBrain 1.0.3, Transformers |
| **Security** | bcrypt, cryptography, PyJWT |
| **Audio** | librosa, torchaudio, pydub |
| **Testing** | pytest, pytest-asyncio |
| **Deployment** | Docker, uvicorn |

---

## 2. Arquitectura del Sistema

### Arquitectura Hexagonal

El sistema sigue el patrón de **Arquitectura Hexagonal** (también conocido como Ports and Adapters):

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                  │
│   Controllers - Manejo de HTTP requests/responses       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Auth     │  │Enrollment│  │Verification│ │ Admin  ││
│  │Controller│  │Controller│  │ Controller │ │Controller││
│  └────┬─────┘  └────┬─────┘  └────┬───────┘ └────┬────┘│
└───────┼─────────────┼──────────────┼──────────────┼─────┘
        │             │              │              │
┌───────┴─────────────┴──────────────┴──────────────┴─────┐
│               Application Layer                          │
│   Services - Orquestación de casos de uso                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Auth     │  │Enrollment│  │Verification│ │ Phrase  ││
│  │ Service  │  │ Service  │  │ Service V2 │ │ Service ││
│  └────┬─────┘  └────┬─────┘  └────┬───────┘ └────┬────┘│
└───────┼─────────────┼──────────────┼──────────────┼─────┘
        │             │              │              │
┌───────┴─────────────┴──────────────┴──────────────┴─────┐
│                  Domain Layer                            │
│   Modelos de dominio + Repository Ports (interfaces)     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Models     │  │ Repositories │  │   Business   │  │
│  │   (Entities) │  │   (Ports)    │  │    Rules     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────┐
│            Infrastructure Layer                          │
│   Adaptadores - Implementaciones concretas               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │  ML Models   │  │   Security   │  │
│  │  Adapters    │  │  (ECAPA-TDNN)│  │  (Encryption)│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Capas y Responsabilidades

#### API Layer (`src/api/`)
**Responsabilidad**: Manejar requests HTTP, validación de entrada, serialización

**Componentes**:
- **Controllers**: Endpoints REST organizados por dominio
- **Middleware**: Authentication, CORS, Rate Limiting
- **Error Handlers**: Manejo centralizado de excepciones
- **DTOs**: Request/Response models con Pydantic

**Principios**:
- No lógica de negocio directa
- Validación de entrada mediante Pydantic
- Transformación entre DTOs y modelos de dominio

#### Application Layer (`src/application/`)
**Responsabilidad**: Casos de uso, lógica de negocio, orquestación

**Componentes**:
- **Services**: Implementan casos de uso completos
- **DTOs**: Objetos de transferencia de datos
- **Policies**: Políticas de negocio (umbrales, reglas)

**Principios**:
- Orquestan múltiples repositorios
- Implementan lógica de negocio transversal
- No conocen detalles de persistencia

#### Domain Layer (`src/domain/`)
**Responsabilidad**: Core del negocio, reglas invariantes

**Componentes**:
- **Models**: Entidades y value objects
- **Repository Ports**: Interfaces (contratos)
- **Domain Services**: Lógica de dominio pura
- **Policies**: Estrategias (Strategy Pattern)

**Principios**:
- Independiente de frameworks
- Sin dependencias externas
- Reglas de negocio invariables

#### Infrastructure Layer (`src/infrastructure/`)
**Responsabilidad**: Implementaciones concretas, acceso a recursos

**Componentes**:
- **Persistence**: Implementaciones de repositorios
- **Biometrics**: Adaptadores de ML models
- **Security**: Encriptación, JWT
- **Config**: Configuración y dependencies

**Principios**:
- Implementa interfaces del dominio
- Maneja detalles técnicos
- Reemplazable sin afectar lógica

---

## 3. Estructura de Directorios

```
Backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada de la aplicación
│   ├── config.py                  # Configuración global
│   │
│   ├── api/                       # 🌐 API Layer - Controllers
│   │   ├── auth_controller.py     # Login, register, logout
│   │   ├── enrollment_controller.py  # Enrollment endpoints
│   │   ├── verification_controller_v2.py  # Verification multi-phrase
│   │   ├── challenge_controller.py  # Challenge management
│   │   ├── phrase_controller.py   # Phrase management
│   │   ├── admin_controller.py    # Admin endpoints
│   │   ├── error_handlers.py      # Centralized error handling
│   │   └── middleware/
│   │       ├── auth_middleware.py  # JWT authentication
│   │       └── audit_middleware.py # Audit logging
│   │
│   ├── application/               # 🏢 Application Layer - Services
│   │   ├── dto/                   # Data Transfer Objects
│   │   │   ├── auth_dto.py
│   │   │   ├── enrollment_dto.py
│   │   │   └── verification_dto.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py    # Authentication logic
│   │   │   ├── enrollment_service.py  # Enrollment workflow
│   │   │   ├── verification_service_v2.py  # Verification logic
│   │   │   ├── challenge_service.py  # Challenge generation
│   │   │   └── phrase_service.py  # Phrase selection
│   │   │
│   │   └── policies/              # Business policies
│   │       ├── similarity_policy.py
│   │       └── risk_policy.py
│   │
│   ├── domain/                    # 💼 Domain Layer - Core Business
│   │   ├── model/                 # Domain entities
│   │   │   ├── user.py
│   │   │   ├── voiceprint.py
│   │   │   ├── challenge.py
│   │   │   ├── phrase.py
│   │   │   ├── enrollment_sample.py
│   │   │   └── verification_attempt.py
│   │   │
│   │   ├── repositories/          # Repository interfaces (Ports)
│   │   │   ├── user_repository_port.py
│   │   │   ├── voiceprint_repository_port.py
│   │   │   ├── challenge_repository_port.py
│   │   │   ├── phrase_repository_port.py
│   │   │   └── audit_repository_port.py
│   │   │
│   │   └── services/              # Domain services
│   │       ├── decision_service.py
│   │       └── risk_assessment_service.py
│   │
│   ├── infrastructure/            # 🔧 Infrastructure - Implementations
│   │   ├── biometrics/            # ML Models adapters
│   │   │   ├── VoiceBiometricEngineFacade.py  # Facade pattern
│   │   │   ├── SpeakerEmbeddingAdapter.py  # ECAPA-TDNN
│   │   │   ├── SpoofDetectorAdapter.py  # Anti-spoofing ensemble
│   │   │   ├── ASRAdapter.py      # Speech recognition
│   │   │   ├── model_manager.py   # Model loading/caching
│   │   │   └── local_antispoof_models.py  # Local model implementations
│   │   │
│   │   ├── persistence/           # Database adapters
│   │   │   ├── PostgresUserRepository.py
│   │   │   ├── PostgresVoiceSignatureRepository.py
│   │   │   ├── PostgresChallengeRepository.py
│   │   │   ├── PostgresPhraseRepository.py
│   │   │   ├── PostgresAuditRepository.py
│   │   │   └── PostgresAuthAttemptRepository.py
│   │   │
│   │   ├── security/              # Security components
│   │   │   ├── encryption.py      # Fernet encryption
│   │   │   ├── jwt_handler.py     # JWT generation/validation
│   │   │   └── password_hasher.py # bcrypt hashing
│   │   │
│   │   └── config/
│   │       └── dependencies.py    # Dependency injection
│   │
│   ├── jobs/                      # 🔄 Background jobs
│   │   └── cleanup_expired_challenges.py
│   │
│   ├── shared/                    # 🔗 Shared utilities
│   │   ├── types/                 # Common types
│   │   │   └── common_types.py
│   │   └── constants/             # Constants
│   │       └── biometric_constants.py
│   │
│   └── utils/                     # 🛠️ Utilities
│       └── validators.py
│
├── tests/                         # 🧪 Tests
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_repositories.py
│   │   └── test_biometrics.py
│   └── integration/
│       ├── test_enrollment_flow.py
│       ├── test_verification_flow.py
│       └── test_api_endpoints.py
│
├── scripts/                       # 📜 Utility scripts
│   ├── create_users.py
│   ├── run_seed.py
│   └── extract_phrases.py
│
├── models/                        # 🤖 ML Models (downloaded)
│   ├── speaker-recognition/
│   │   ├── ecapa_tdnn/
│   │   └── x_vector/
│   ├── text-verification/
│   │   └── lightweight_asr/
│   └── anti-spoofing/
│       ├── aasist/
│       ├── rawnet2/
│       └── nes2net/
│
├── docs/                          # 📚 Documentation
│   ├── API_DOCUMENTATION.md
│   ├── BACKEND_ARCHITECTURE.md
│   ├── ML_MODELS_OVERVIEW.md
│   └── DYNAMIC_PHRASES_SYSTEM.md
│
├── logs/                          # 📝 Application logs
├── temp/                          # 🗃️ Temporary files
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker Compose setup
├── .env.example                   # Environment variables template
└── README.md
```

### Convenciones de Nomenclatura

**Archivos**:
- Controllers: `*_controller.py`
- Services: `*_service.py`
- Repositories: `Postgres*Repository.py`
- Adapters: `*Adapter.py`
- DTOs: `*_dto.py`

**Clases**:
- Controllers: `*Router` (FastAPI routers)
- Services: `*Service`
- Repositories: `*Repository`
- Models: PascalCase sin sufijo

**Funciones**:
- snake_case para todo
- Async functions: prefijo `async def`
- Private methods: prefijo `_`

---

## 4. API Reference

### Índice de Endpoints

| Categoría | Endpoint | Método | Auth | Descripción |
|-----------|----------|--------|------|-------------|
| **Root** | `/` | GET | No | Información de la API |
| **Health** | `/health` | GET | No | Health check |
| **Auth** | `/api/auth/register` | POST | No | Registro de usuario |
| **Auth** | `/api/auth/login` | POST | No | Login con JWT |
| **Auth** | `/api/auth/logout` | POST | Sí | Logout |
| **Auth** | `/api/auth/me` | GET | Sí | Datos del usuario |
| **Auth** | `/api/auth/change-password` | POST | Sí | Cambiar contraseña |
| **Enrollment** | `/api/enrollment/start` | POST | Sí | Iniciar enrollment |
| **Enrollment** | `/api/enrollment/add-sample` | POST | Sí | Agregar muestra de voz |
| **Enrollment** | `/api/enrollment/complete` | POST | Sí | Completar enrollment |
| **Enrollment** | `/api/enrollment/status/{user_id}` | GET | Sí | Estado de enrollment |
| **Verification** | `/api/verification/start-multi` | POST | Sí | Iniciar verificación (3 frases) |
| **Verification** | `/api/verification/verify-phrase` | POST | Sí | Verificar frase individual |
| **Verification** | `/api/verification/history/{user_id}` | GET | Sí | Historial de verificaciones |
| **Phrases** | `/api/phrases/random` | GET | No | Obtener frases aleatorias |
| **Phrases** | `/api/phrases/stats` | GET | No | Estadísticas de frases |
| **Phrases** | `/api/phrases/list` | GET | Sí | Listar frases (paginado) |
| **Challenges** | `/api/challenges/{challenge_id}` | GET | No | Obtener challenge por ID |
| **Admin** | `/api/admin/stats` | GET | Admin | Estadísticas del sistema |
| **Admin** | `/api/admin/users` | GET | Admin | Listar usuarios |

### Autenticación

El sistema usa **JWT (JSON Web Tokens)** con access y refresh tokens.

#### Login Flow

```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

#### Authenticated Requests

```
GET /api/enrollment/status/{user_id}
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Enrollment Endpoints

#### POST /api/enrollment/start

Inicia el proceso de enrollment para un usuario.

**Request**:
```json
{
  "difficulty": "medium"  // "easy", "medium", "hard"
}
```

**Response**:
```json
{
  "enroll_id": "uuid-enrollment-session",
  "user_id": "uuid-user",
  "challenges": [
    {
      "challenge_id": "uuid-challenge-1",
      "phrase_id": "uuid-phrase-1",
      "phrase_text": "La tecnología avanza rápidamente",
      "difficulty": "medium",
      "order": 1
    },
    // ... 4 más (total 5)
  ],
  "required_samples": 5,
  "expires_at": "2024-12-14T21:30:00Z"
}
```

**Business Logic**:
1. Valida que el usuario no esté ya enrolado
2. Genera 5 frases únicas con la dificultad especificada
3. Evita frases usadas recientemente por el usuario
4. Crea una sesión de enrollment temporal
5. Retorna challenges con expiración

#### POST /api/enrollment/add-sample

Agrega una muestra de voz para el enrollment.

**Request** (multipart/form-data):
```
enroll_id: uuid-enrollment-session
challenge_id: uuid-challenge-1
audio_file: (binary audio file - WAV/MP3/WEBM)
```

**Response**:
```json
{
  "sample_id": "uuid-sample-1",
  "enroll_id": "uuid-enrollment-session",
  "challenge_id": "uuid-challenge-1",
  "quality_score": 0.87,
  "is_valid": true,
  "samples_collected": 1,
  "samples_required": 5,
  "details": {
    "embedding_dimension": 512,
    "anti_spoofing_score": 0.12,
    "is_live": true,
    "phrase_match": true,
    "similarity_to_phrase": 0.92
  }
}
```

**Processing**:
1. Valida la sesión de enrollment
2. Extrae embedding de voz con ECAPA-TDNN
3. Ejecuta anti-spoofing detection
4. Transcribe audio y valida frase
5. Almacena embedding encriptado
6. Calcula quality score

#### POST /api/enrollment/complete

Completa el proceso de enrollment y genera el voiceprint.

**Request**:
```json
{
  "enroll_id": "uuid-enrollment-session"
}
```

**Response**:
```json
{
  "voiceprint_id": "uuid-voiceprint",
  "user_id": "uuid-user",
  "quality_score": 0.89,
  "samples_used": 5,
  "created_at": "2024-12-14T21:00:00Z",
  "status": "active"
}
```

**Logic**:
1. Valida que se tengan 5 muestras
2. Calcula embedding promedio
3. Normaliza el voiceprint
4. Encripta con Fernet
5. Almacena en PostgreSQL
6. Limpia sesión temporal

### Verification Endpoints

####  /api/verification/start-multi

Inicia verificación multi-frase (3 frases).

**Request**:
```json
{
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "verification_id": "uuid-verification-session",
  "user_id": "uuid-user",
  "challenges": [
    {
      "challenge_id": "uuid-challenge-1",
      "phrase_text": "La seguridad es fundamental",
      "order": 1
    },
    {
      "challenge_id": "uuid-challenge-2",
      "phrase_text": "Verificación de identidad en proceso",
      "order": 2
    },
    {
      "challenge_id": "uuid-challenge-3",
      "phrase_text": "Autenticación biométrica activada",
      "order": 3
    }
  ],
  "required_verifications": 3,
  "expires_at": "2024-12-14T21:35:00Z"
}
```

#### POST /api/verification/verify-phrase

Verifica una frase individual.

**Request** (multipart/form-data):
```
verification_id: uuid-verification-session
challenge_id: uuid-challenge-1
audio_file: (binary)
```

**Response**:
```json
{
  "verification_id": "uuid-verification-session",
  "challenge_id": "uuid-challenge-1",
  "is_verified": true,
  "similarity_score": 0.87,
  "anti_spoofing_score": 0.15,
  "phrase_match": true,
  "confidence": 0.91,
  "verifications_completed": 1,
  "verifications_required": 3,
  "final_decision": null  // Null hasta completar las 3
}
```

**Final Response (después de 3 frases)**:
```json
{
  "verification_id": "uuid-verification-session",
  "challenge_id": "uuid-challenge-3",
  "is_verified": true,
  "similarity_score": 0.85,
  "anti_spoofing_score": 0.18,
  "phrase_match": true,
  "confidence": 0.89,
  "verifications_completed": 3,
  "verifications_required": 3,
  "final_decision": {
    "is_authenticated": true,
    "average_similarity": 0.86,
    "average_confidence": 0.90,
    "all_phrases_matched": true,
    "all_live_detection": true,
    "decision": "APPROVED"
  }
}
```

### Admin Endpoints

#### GET /api/admin/stats

Obtiene estadísticas del sistema (requiere rol admin).

**Response**:
```json
{
  "users": {
    "total": 142,
    "enrolled": 98,
    "not_enrolled": 44,
    "by_role": {
      "user": 135,
      "admin": 5,
      "superadmin": 2
    }
  },
  "verifications": {
    "total_attempts": 1523,
    "successful": 1378,
    "failed": 145,
    "success_rate": 0.905
  },
  "phrases": {
    "total": 43459,
    "easy": 6637,
    "medium": 25063,
    "hard": 11759
  },
  "system": {
    "uptime_seconds": 342523,
    "version": "1.0.0"
  }
}
```

---

## 5. Servicios y Lógica de Negocio

### EnrollmentService

**Archivo**: `src/application/services/enrollment_service.py`

**Responsabilidad**: Orquestar el proceso completo de enrollment.

**Dependencias**:
- `VoiceSignatureRepository`: Persistencia de voiceprints
- `UserRepository`: Gestión de usuarios
- `ChallengeService`: Generación de challenges
- `VoiceBiometricEngine`: Extracción de embeddings

**Métodos Principales**:

```python
class EnrollmentService:
    async def start_enrollment(
        self, 
        user_id: str, 
        difficulty: str
    ) -> StartEnrollmentResponse:
        """
        Inicia proceso de enrollment.
        
        1. Valida que el usuario no esté enrolado
        2. Genera 5 challenges con frases únicas
        3. Crea sesión temporal en memoria
        4. Retorna challenges al cliente
        """
        
    async def add_enrollment_sample(
        self,
        enroll_id: str,
        challenge_id: str,
        audio_data: bytes,
        audio_format: str
    ) -> EnrollmentSampleResponse:
        """
        Procesa una muestra de enrollment.
        
        1. Valida sesión y challenge
        2. Extrae embedding con ECAPA-TDNN
        3. Ejecuta anti-spoofing
        4. Transcribe y valida frase
        5. Almacena embedding encriptado
        """
        
    async def complete_enrollment(
        self,
        enroll_id: str
    ) -> CompleteEnrollmentResponse:
        """
        Finaliza enrollment y crea voiceprint.
        
        1. Valida 5 muestras completas
        2. Calcula embedding promedio
        3. Normaliza voiceprint
        4. Encripta y persiste
        5. Limpia sesión temporal
        """
```

**Quality Score Calculation**:
```python
def _calculate_quality_score(self, samples: List[Embedding]) -> float:
    """
    Calcula calidad del enrollment basado en:
    - Similitud entre muestras (consistencia)
    - Normalización de embeddings
    - Ausencia de outliers
    
    Score: 0.0 - 1.0
    - > 0.9: Excelente
    - 0.8-0.9: Bueno
    - 0.7-0.8: Aceptable
    - < 0.7: Pobre (recomendar re-enrollment)
    """
    similarities = []
    for i, emb1 in enumerate(samples):
        for emb2 in samples[i+1:]:
            sim = cosine_similarity(emb1, emb2)
            similarities.append(sim)
    
    return np.mean(similarities)
```

### VerificationServiceV2

**Archivo**: `src/application/services/verification_service_v2.py`

**Responsabilidad**: Multi-phrase verification con agregación de scores.

**Flow**:
```
User Request
    ↓
start_multi_phrase()
    ↓
Generate 3 Challenges
    ↓
User records phrase 1 → verify_phrase()
    ├─ Extract embedding
    ├─ Compare with voiceprint
    ├─ Anti-spoofing check
    ├─ ASR verification
    └─ Store result (1/3)
    ↓
User records phrase 2 → verify_phrase()
    └─ Store result (2/3)
    ↓
User records phrase 3 → verify_phrase()
    └─ Store result (3/3)
    ↓
Aggregate Results
    ├─ Average similarity: 0.86
    ├─ All live: true
    ├─ All phrases matched: true
    └─ DECISION: APPROVED
```

**Decision Logic**:
```python
def _make_final_decision(
    self,
    phrase_results: List[PhraseVerificationResult]
) -> FinalDecision:
    """
    Decisión basada en múltiples criteriosh:
    
    1. Todas las frases deben pasar anti-spoofing
    2. Todas las frases deben coincidir (ASR)
    3. Promedio de similarity >= threshold (0.60)
    4. Al menos 2/3 frases con similarity alta (>= 0.70)
    """
    # Check anti-spoofing
    all_live = all(r.is_live for r in phrase_results)
    if not all_live:
        return FinalDecision(approved=False, reason="spoofing_detected")
    
    # Check phrase matching
    all_matched = all(r.phrase_match for r in phrase_results)
    if not all_matched:
        return FinalDecision(approved=False, reason="phrase_mismatch")
    
    # Check similarity
    avg_similarity = np.mean([r.similarity for r in phrase_results])
    high_similarity_count = sum(1 for r in phrase_results if r.similarity >= 0.70)
    
    if avg_similarity >= SIMILARITY_THRESHOLD and high_similarity_count >= 2:
        return FinalDecision(approved=True, confidence=avg_similarity)
    else:
        return FinalDecision(approved=False, reason="low_similarity")
```

### ChallengeService

**Archivo**: `src/application/services/challenge_service.py`

**Responsabilidad**: Gestión de challenges y selección de frases.

**Características**:
- Selección aleatoria con exclusión de frases recientes
- Soporte para dificultad (easy/medium/hard)
- Expiración automática de challenges
- Prevención de reutilización de frases

**Algoritmo de Selección**:
```python
async def create_challenge_batch(
    self,
    user_id: str,
    count: int,
    difficulty: str
) -> List[Challenge]:
    """
    1. Obtiene frases usadas recientemente (últimas 50)
    2. Selecciona frases aleatorias de la dificultad
    3. Excluye las ya usadas
    4. Crea challenges con timeout
    5. Registra uso en phrase_usage
    """
    # Get recently used phrases (last 50 for this user)
    recent_phrases = await self._get_recent_phrases(user_id, limit=50)
    
    # Get random phrases excluding recent ones
    phrases = await self.phrase_repo.find_random_excluding(
        count=count,
        difficulty=difficulty,
        exclude_ids=recent_phrases
    )
    
    # Create challenges
    challenges = []
    for order, phrase in enumerate(phrases, start=1):
        challenge = Challenge(
            phrase_id=phrase.id,
            phrase_text= phrase.text,
            difficulty=difficulty,
            expires_at=now() + timeout_for_difficulty(difficulty),
            order=order
        )
        challenges.append(challenge)
        
        # Record usage
        await self.usage_repo.record_usage(user_id, phrase.id, "enrollment")
    
    return challenges
```

### AuthService

**Archivo**: `src/application/services/auth_service.py`

**Responsabilidad**: Autenticación, gestión de sesiones, JWT.

**Métodos**:
```python
class AuthService:
    async def register(self, email: str, password: str, name: str):
        """Register new user with hashed password"""
        
    async def login(self, email: str, password: str):
        """Authenticate and return JWT tokens"""
        
    async def change_password(self, user_id: str, old_pass: str, new_pass: str):
        """Change user password with validation"""
        
    async def verify_token(self, token: str) -> User:
        """Verify JWT and return user"""
```

---

## 6. Modelos de Dominio

### User

**Archivo**: `src/domain/model/user.py`

```python
@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str
    role: str  # 'user', 'admin', 'superadmin'
    is_active: bool
    created_at: datetime
    updated_at: datetime
    has_voiceprint: bool = False
```

### Voiceprint

**Archivo**: `src/domain/model/voiceprint.py`

```python
@dataclass
class Voiceprint:
    id: str
    user_id: str
    embedding: np.ndarray  # 512-D vector
    speaker_model_id: int
    quality_score: float
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
```

**Persistence**: El embedding se encripta con Fernet antes de almacenar en PostgreSQL.

### Challenge

**Archivo**: `src/domain/model/challenge.py`

```python
@dataclass
class Challenge:
    id: str
    phrase_id: str
    phrase_text: str
    difficulty: str
    order: int
    created_at: datetime
    expires_at: datetime
    is_used: bool = False
```

### EnrollmentSample

**Archivo**: `src/domain/model/enrollment_sample.py`

```python
@dataclass
class EnrollmentSample:
    id: str
    user_id: str
    challenge_id: str
    embedding: np.ndarray
    quality_score: float
    anti_spoofing_score: float
    is_live: bool
    asr_confidence: float
    phrase_match: bool
    created_at: datetime
```

---

## 7. Base de Datos

### Schema Overview

El sistema usa **PostgreSQL 16** con la extensión **pgvector** para almacenamiento de embeddings.

**Extensiones**:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### Tablas Principales

#### `users`

```sql
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_role ON "user"(role);
```

#### `phrase`

```sql
CREATE TABLE phrase (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text TEXT NOT NULL,
    difficulty VARCHAR(10) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    language VARCHAR(5) DEFAULT 'es',
    word_count INTEGER,
    char_length INTEGER,
    source VARCHAR(255),
    book_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phrase_difficulty ON phrase(difficulty);
CREATE INDEX idx_phrase_is_active ON phrase(is_active);
CREATE INDEX idx_phrase_book ON phrase(book_id);
```

**Estadísticas**:
- Total: 43,459 frases
- Easy: 6,637 (15.3%)
- Medium: 25,063 (57.7%)
- Hard: 11,759 (27.0%)

#### `voiceprint`

```sql
CREATE TABLE voiceprint (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    embedding BYTEA NOT NULL,  -- Encrypted 512-D vector
    speaker_model_id INTEGER,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(user_id)  -- One voiceprint per user
);

CREATE INDEX idx_voiceprint_user ON voiceprint(user_id);
```

**Nota**: El embedding se almacena encriptado con Fernet. Se desencripta solo cuando se necesita para comparación.

#### `enrollment_sample`

```sql
CREATE TABLE enrollment_sample (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    challenge_id UUID REFERENCES challenge(id),
    embedding BYTEA NOT NULL,
    quality_score FLOAT,
    anti_spoofing_score FLOAT,
    is_live BOOLEAN,
    asr_confidence FLOAT,
    phrase_match BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `verification_attempt`

```sql
CREATE TABLE verification_attempt (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES "user"(id),
    similarity_score FLOAT,
    decision VARCHAR(50),
    anti_spoofing_score FLOAT,
    is_live BOOLEAN,
    phrase_matches BOOLEAN,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

#### `challenge`

```sql
CREATE TABLE challenge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phrase_id UUID REFERENCES phrase(id),
    difficulty VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    used_at TIMESTAMP
);

CREATE INDEX idx_challenge_expires ON challenge(expires_at);
CREATE INDEX idx_challenge_is_used ON challenge(is_used);
```

**Cleanup**: Challenges expirados se limpian automáticamente cada 30 segundos por un background job.

#### `phrase_usage`

```sql
CREATE TABLE phrase_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phrase_id UUID REFERENCES phrase(id),
    user_id UUID REFERENCES "user"(id),
    used_for VARCHAR(20),  -- 'enrollment' | 'verification'
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phrase_usage_user ON phrase_usage(user_id, used_at DESC);
```

**Propósito**: Evitar repetir frases para el mismo usuario. El sistema excluye las últimas 50 frases usadas.

### Relaciones

```mermaid
erDiagram
    USER ||--o{ VOICEPRINT : "has one"
    USER ||--o{ ENROLLMENT_SAMPLE : "creates many"
    USER ||--o{ VERIFICATION_ATTEMPT : "performs many"
    USER ||--o{ PHRASE_USAGE : "uses phrases"
    
    PHRASE ||--o{ CHALLENGE : "referenced in"
    PHRASE ||--o{ PHRASE_USAGE : "tracked in"
    PHRASE }o--|| BOOK : "belongs to"
    
    CHALLENGE ||--o{ ENROLLMENT_SAMPLE : "used for"
    CHALLENGE ||--o{ VERIFICATION_ATTEMPT : "validated against"
```

---

## 8. Seguridad

### Autenticación JWT

**Tokens**:
- **Access Token**: 30 minutos de expiración
- **Refresh Token**: 7 días de expiración

**Generación**:
```python
# src/infrastructure/security/jwt_handler.py

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Validación**:
```python
def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid token")
```

### Encriptación de Embeddings

Los embeddings de voz se almacenan encriptados con **Fernet** (AES-128).

```python
# src/infrastructure/security/encryption.py

from cryptography.fernet import Fernet

class EmbeddingEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_embedding(self, embedding: np.ndarray) -> bytes:
        # Serialize numpy array
        serialized = embedding.tobytes()
        # Encrypt
        encrypted = self.cipher.encrypt(serialized)
        return encrypted
    
    def decrypt_embedding(self, encrypted: bytes) -> np.ndarray:
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted)
        # Deserialize
        embedding = np.frombuffer(decrypted, dtype=np.float32)
        return embedding
```

**Key Management**:
- Key almacenada en variable de entorno `EMBEDDING_ENCRYPTION_KEY`
- Generada con `Fernet.generate_key()`
- Nunca commitear al repositorio

### Hashing de Contraseñas

Usa **bcrypt** con salt automático:

```python
# src/infrastructure/security/password_hasher.py

import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

### Rate Limiting

**Configuración**:
```python
# Default: 100 requests/minute por IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)
```

**Endpoints específicos**:
```python
@router.post("/login")
@limiter.limit("10/minute")  # Solo 10 intentos de login/minuto
async def login(...):
    pass
```

### CORS

**Development**:
```python
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]
```

**Production**:
```python
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS").split(",")
```

### Security Headers

```python
# X-Content-Type-Options
response.headers["X-Content-Type-Options"] = "nosniff"

# X-Frame-Options
response.headers["X-Frame-Options"] = "DENY"

# X-XSS-Protection
response.headers["X-XSS-Protection"] = "1; mode=block"

# HSTS (Production only)
if env == "production":
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
```

---

## 9. Modelos de Machine Learning

*Ver documento completo*: [`ML_MODELS_OVERVIEW.md`](./ML_MODELS_OVERVIEW.md)

### Resumen

| Modelo | Propósito | Dataset | Dimensión |
|--------|-----------|---------|-----------|
| ECAPA-TDNN | Speaker Recognition | VoxCeleb | 512-D |
| x-vector | Speaker Recognition (alt) | VoxCeleb | 512-D |
| Wav2Vec2 | ASR (Español) | CommonVoice 14 | - |
| AASIST | Anti-Spoofing | ASVspoof 2019/21 | - |
| RawNet2 | Anti-Spoofing | ASVspoof 2019/21 | - |
| Nes2Net | Anti-Spoofing | ASVspoof 2021 | - |

### Model Loading

```python
# src/infrastructure/biometrics/model_manager.py

class ModelManager:
    def download_model(self, model_key: str) -> bool:
        """Download model from HuggingFace/SpeechBrain"""
        
    def get_model_path(self, model_key: str) -> Path:
        """Get local path for model"""
        
    def is_model_available(self, model_key: str) -> bool:
        """Check if model is downloaded"""
```

**Lazy Loading**: Los modelos se cargan solo cuando se usan por primera vez.

---

## 10. Configuración y Deployment

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=your_password

# Security
SECRET_KEY=your-secret-key
EMBEDDING_ENCRYPTION_KEY=your-fernet-key
JWT_SECRET_KEY=your-jwt-secret

# API
API_HOST=0.0.0.0
API_PORT=8000
ENV=development  # development | production

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT=100/minute

# ML Models
MODEL_CACHE_DIR=./models
DEVICE=cpu  # cpu | cuda

# Logging
LOG_LEVEL=INFO
```

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1

# Create venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app
WORKDIR /app
COPY src/ ./src/

# Run
CMD ["python", "-m", "src.main"]
```

**docker-compose.yml**:
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: voice_biometrics
      POSTGRES_USER: voice_user
      POSTGRES_PASSWORD: voice_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
    depends_on:
      - postgres
    volumes:
      - ./models:/app/models

volumes:
  postgres_data:
```

**Start**:
```bash
docker-compose up -d
```

---

## 11. Flujos Principales

### Enrollment Flow

```mermaid
sequenceDiagram
    participant U as User/Frontend
    participant API as FastAPI
    participant ES as EnrollmentService
    participant BE as BiometricEngine
    participant DB as PostgreSQL
    
    U->>API: POST /enrollment/start
    API->>ES: start_enrollment(user_id, difficulty)
    ES->>DB: Check if user enrolled
    ES->>DB: Generate 5 challenges
    ES-->>U: Return 5 phrases
    
    loop For each phrase (5 times)
        U->>API: POST /enrollment/add-sample (audio)
        API->>ES: add_enrollment_sample(audio)
        ES->>BE: Extract embedding (ECAPA-TDNN)
        BE-->>ES: 512-D embedding
        ES->>BE: Detect spoofing
        BE-->>ES: Spoof score
        ES->>BE: Transcribe audio (ASR)
        BE-->>ES: Transcribed text
        ES->>DB: Save encrypted embedding
        ES-->>U: Sample accepted (1/5, 2/5, ...)
    end
    
    U->>API: POST /enrollment/complete
    API->>ES: complete_enrollment(enroll_id)
    ES->>DB: Load 5 embeddings
    ES->>ES: Calculate average embedding
    ES->>ES: Normalize voiceprint
    ES->>DB: Save voiceprint (encrypted)
    ES-->>U: Enrollment complete!
```

### Verification Flow

```mermaid
sequenceDiagram
    participant U as User/Frontend
    participant API as FastAPI
    participant VS as VerificationService
    participant BE as BiometricEngine
    participant DB as PostgreSQL
    
    U->>API: POST /verification/start-multi
    API->>VS: start_multi_phrase(user_id)
    VS->>DB: Check if user enrolled
    VS->>DB: Generate 3 challenges
    VS-->>U: Return 3 phrases
    
    loop For each phrase (3 times)
        U->>API: POST /verification/verify-phrase (audio)
        API->>VS: verify_phrase(audio, challenge_id)
        VS->>BE: Extract embedding
        BE-->>VS: Test embedding
        VS->>DB: Load voiceprint
        DB-->>VS: Encrypted voiceprint
        VS->>VS: Decrypt voiceprint
        VS->>VS: Calculate similarity (cosine)
        VS->>BE: Anti-spoofing check
        BE-->>VS: Is live?
        VS->>BE: ASR verification
        BE-->>VS: Phrase match?
        VS->>DB: Save verification attempt
        VS-->>U: Phrase verified (1/3, 2/3, ...)
    end
    
    VS->>VS: Aggregate 3 results
    VS->>VS: Average similarity >= 0.60?
    VS->>VS: All live + All matched?
    
    alt All checks passed
        VS-->>U: ✅ Authentication SUCCESS
    else Any check failed
        VS-->>U: ❌ Authentication FAILED
    end
```

---

## 12. Testing

### Unit Tests

**Location**: `tests/unit/`

```bash
# Run unit tests
pytest tests/unit/

# With coverage
pytest tests/unit/ --cov=src --cov-report=html
```

**Example**:
```python
# tests/unit/test_enrollment_service.py

@pytest.mark.asyncio
async def test_start_enrollment_success():
    # Arrange
    user_id = "test-user-123"
    difficulty = "medium"
    mock_repo = MockVoiceprintRepository()
    service = EnrollmentService(voiceprint_repo=mock_repo)
    
    # Act
    result = await service.start_enrollment(user_id, difficulty)
    
    # Assert
    assert result.required_samples == 5
    assert len(result.challenges) == 5
    assert all(c.difficulty == "medium" for c in result.challenges)
```

### Integration Tests

**Location**: `tests/integration/`

```bash
# Run integration tests (requires DB)
pytest tests/integration/
```

**Example**:
```python
# tests/integration/test_enrollment_flow.py

@pytest.mark.asyncio
async def test_full_enrollment_flow():
    """Test complete enrollment from start to finish"""
    
    # 1. Start enrollment
    response = await client.post("/api/enrollment/start", 
        json={"difficulty": "easy"})
    assert response.status_code == 200
    enroll_id = response.json()["enroll_id"]
    
    # 2. Add 5 samples
    for i in range(5):
        with open(f"test_audio_{i}.wav", "rb") as f:
            response = await client.post("/api/enrollment/add-sample",
                files={"audio_file": f},
                data={"enroll_id": enroll_id})
            assert response.status_code == 200
    
    # 3. Complete enrollment
    response = await client.post("/api/enrollment/complete",
        json={"enroll_id": enroll_id})
    assert response.status_code == 200
    assert response.json()["samples_used"] == 5
```

### Test Coverage

**Target**: 80%+ coverage

**Current** (estimated):
- Services: 85%
- Repositories: 90%
- Biometrics: 70%
- Controllers: 75%

---

## 13. Performance y Optimización

### Database Optimization

**Connection Pooling**:
```python
# Connection pool with asyncpg
pool = await asyncpg.create_pool(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    min_size=10,  # Minimum connections
    max_size=50   # Maximum connections
)
```

**Indexes**:
```sql
-- User lookups
CREATE INDEX idx_user_email ON "user"(email);

-- Phrase selection
CREATE INDEX idx_phrase_difficulty ON phrase(difficulty);
CREATE INDEX idx_phrase_is_active ON phrase(is_active);

-- Challenge cleanup
CREATE INDEX idx_challenge_expires ON challenge(expires_at);

-- Recent phrase usage
CREATE INDEX idx_phrase_usage_user ON phrase_usage(user_id, used_at DESC);
```

### Caching

**Model Caching**:
- ML models loaded once at startup
- Kept in memory for entire application lifecycle
- ~2-3 GB RAM usage

**Embedding Caching**:
```python
# Cache voiceprints in memory (optional)
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_voiceprint(user_id: str) -> Voiceprint:
    return await voiceprint_repo.get_by_user_id(user_id)
```

### Async Processing

All I/O operations are async:
```python
# Database queries
await user_repo.get_by_id(user_id)

# ML inference
embedding = await asyncio.to_thread(
    biometric_engine.extract_embedding,
    audio_data
)
```

### Performance Metrics

| Operation | Time (avg) |
|-----------|-----------|
| Enrollment start | 50-100ms |
| Add sample (extract embedding) | 1.5-2.5s |
| Complete enrollment | 200-400ms |
| Verification start | 50-100ms |
| Verify phrase | 1.5-2.5s |
| Database query | 5-20ms |

**Bottleneck**: ML inference (ECAPA-TDNN) es CPU-intensive.

**Optimizations**:
- Use GPU if available (`use_gpu=True`)
- Batch processing for multiple verifications
- Limit audio to 5 seconds for ASR

---

## Apéndices

### A. Glosario

| Término | Definición |
|---------|-----------|
| **Embedding** | Vector numérico 512-D que representa características únicas de voz |
| **Voiceprint** | "Huella de voz" - embedding promedio de 5 muestras de enrollment |
| **Challenge** | Frase que el usuario debe leer durante enrollment/verification |
| **Anti-Spoofing** | Detección de intentos de fraude (deepfakes, replay attacks) |
| **ASR** | Automatic Speech Recognition - transcripción de voz a texto |
| **Cosine Similarity** | Métrica de similitud entre embeddings (0-1) |
| **Spoof Score** | Probabilidad de que el audio sea sintético (0-1) |

### B. Referencias

**Papers**:
- ECAPA-TDNN: https://arxiv.org/abs/2005.07143
- AASIST: https://arxiv.org/abs/2110.01200
- RawNet2: https://arxiv.org/abs/2011.01108

**Frameworks**:
- FastAPI: https://fastapi.tiangolo.com/
- SpeechBrain: https://speechbrain.github.io/
- PostgreSQL: https://www.postgresql.org/

**Datasets**:
- VoxCeleb: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/
- ASVspoof: https://www.asvspoof.org/
- CommonVoice: https://commonvoice.mozilla.org/

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0.0  
**Mantenido por**: Voice Biometrics Team
