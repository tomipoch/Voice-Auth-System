# Sistema de Autenticación Biométrica por Voz con Frases Dinámicas

## 🎯 Visión General

Sistema completo de autenticación biométrica por voz que utiliza **43,459 frases dinámicas** extraídas de libros PDF para el proceso de enrollment y verificación. Las frases se seleccionan aleatoriamente según dificultad y se evitan repeticiones recientes.

## 📋 Módulos Implementados

### 1. Módulo de Enrollment (Registro de voz)
**Archivo**: `Backend/src/application/enrollment_service.py`  
**Endpoints**: `/api/v1/enrollment/*`

**Flujo**:
```
Usuario → Inicio → Obtiene N frases → Lee cada frase → Sistema graba → Completa enrollment → Voiceprint creado
```

**Endpoints**:
- `POST /api/v1/enrollment/start` - Iniciar enrollment
- `POST /api/v1/enrollment/add-sample` - Agregar muestra de voz
- `POST /api/v1/enrollment/complete` - Finalizar enrollment
- `GET /api/v1/enrollment/status/{user_id}` - Consultar estado

### 2. Módulo de Verification (Autenticación de voz)
**Archivo**: `Backend/src/application/verification_service_v2.py`  
**Endpoints**: `/api/v1/verification/*`

**Flujo**:
```
Usuario → Inicio → Obtiene 1 frase → Lee frase → Sistema verifica → Decisión: ✓ o ✗
```

**Endpoints**:
- `POST /api/v1/verification/start` - Iniciar verificación
- `POST /api/v1/verification/verify` - Verificar voz
- `POST /api/v1/verification/quick-verify` - Verificación rápida
- `GET /api/v1/verification/history/{user_id}` - Historial

## 🔄 Flujo Completo del Sistema

### Paso 1: Enrollment (Una vez por usuario)

```bash
# 1. Iniciar enrollment
curl -X POST http://localhost:8000/api/v1/enrollment/start \
  -F "difficulty=medium"

# Respuesta:
{
  "enrollment_id": "abc123...",
  "user_id": "user456...",
  "phrases": [
    {"id": "phrase1", "text": "El rápido zorro marrón salta sobre el perro perezoso", "difficulty": "medium"},
    {"id": "phrase2", "text": "La tecnología avanza a pasos agigantados cada día", "difficulty": "medium"},
    {"id": "phrase3", "text": "El conocimiento es poder y la educación es libertad", "difficulty": "medium"}
  ],
  "required_samples": 3
}

# 2. Grabar y enviar cada frase
for phrase in phrases:
  curl -X POST http://localhost:8000/api/v1/enrollment/add-sample \
    -F "enrollment_id=abc123..." \
    -F "phrase_id=${phrase.id}" \
    -F "audio_file=@recording_${phrase.id}.wav"

# 3. Completar enrollment
curl -X POST http://localhost:8000/api/v1/enrollment/complete \
  -F "enrollment_id=abc123..."

# Respuesta:
{
  "voiceprint_id": "voiceprint789...",
  "user_id": "user456...",
  "quality_score": 0.92,
  "samples_used": 3
}
```

### Paso 2: Verification (Cada autenticación)

```bash
# 1. Iniciar verificación
curl -X POST http://localhost:8000/api/v1/verification/start \
  -F "user_id=user456..." \
  -F "difficulty=medium"

# Respuesta:
{
  "verification_id": "verify789...",
  "user_id": "user456...",
  "phrase": {
    "id": "phrase42",
    "text": "La seguridad es fundamental en el mundo digital",
    "difficulty": "medium"
  }
}

# 2. Usuario lee la frase y sistema verifica
curl -X POST http://localhost:8000/api/v1/verification/verify \
  -F "verification_id=verify789..." \
  -F "phrase_id=phrase42" \
  -F "audio_file=@verification_audio.wav"

# Respuesta (verificación exitosa):
{
  "verification_id": "verify789...",
  "user_id": "user456...",
  "is_verified": true,
  "confidence_score": 0.87,
  "similarity_score": 0.87,
  "anti_spoofing_score": 0.23,
  "phrase_match": true,
  "is_live": true,
  "threshold_used": 0.75
}
```

## 🎨 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐        ┌──────────────────┐            │
│  │  Enrollment API │        │ Verification API │            │
│  │   Controller    │        │    Controller    │            │
│  └────────┬────────┘        └────────┬─────────┘            │
│           │                          │                       │
│           ▼                          ▼                       │
│  ┌─────────────────┐        ┌──────────────────┐            │
│  │  Enrollment     │        │  Verification    │            │
│  │   Service       │        │    Service V2    │            │
│  └────────┬────────┘        └────────┬─────────┘            │
│           │                          │                       │
│           └──────────┬───────────────┘                       │
│                      ▼                                       │
│         ┌─────────────────────────┐                         │
│         │   Phrase Service        │                         │
│         │   (43,459 frases)       │                         │
│         └────────────┬────────────┘                         │
│                      │                                       │
│                      ▼                                       │
│         ┌─────────────────────────┐                         │
│         │  VoiceBiometric Engine  │                         │
│         │  - Embedding extraction │                         │
│         │  - Anti-spoofing        │                         │
│         │  - Similarity calc      │                         │
│         └────────────┬────────────┘                         │
│                      │                                       │
└──────────────────────┼─────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   PostgreSQL Database    │
        │  - phrase (43,459 rows)  │
        │  - phrase_usage          │
        │  - user                  │
        │  - voiceprint            │
        │  - enrollment_sample     │
        │  - verification_attempt  │
        │  - audit_log             │
        └──────────────────────────┘
```

## 📊 Base de Datos

### Tabla: `phrase`
```sql
id          | UUID (PK)
text        | TEXT (frase)
difficulty  | VARCHAR(10) (easy/medium/hard)
language    | VARCHAR(5) (es)
word_count  | INTEGER
char_length | INTEGER
source      | VARCHAR(255) (libro PDF)
is_active   | BOOLEAN
created_at  | TIMESTAMP
```

**Estadísticas**:
- Total: 43,459 frases
- Easy: 6,637 (15.3%)
- Medium: 25,063 (57.7%)
- Hard: 11,759 (27.0%)

### Tabla: `phrase_usage`
```sql
id         | UUID (PK)
phrase_id  | UUID (FK → phrase)
user_id    | UUID (FK → user)
used_for   | VARCHAR(20) (enrollment/verification)
used_at    | TIMESTAMP
```

**Propósito**: Evitar repetición de frases para el mismo usuario.

### Tabla: `voiceprint`
```sql
id                | UUID (PK)
user_id           | UUID (FK → user)
embedding         | FLOAT[] (vector 256D)
speaker_model_id  | INTEGER (opcional)
created_at        | TIMESTAMP
updated_at        | TIMESTAMP
```

**Propósito**: Almacena la "huella de voz" promedio del usuario.

## 🔧 Configuración

### Variables de entorno (`.env`)
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=voice_password

# Thresholds
SIMILARITY_THRESHOLD=0.75
ANTI_SPOOFING_THRESHOLD=0.5

# Development
SKIP_AUTH=true
DEVELOPMENT_MODE=true
```

### Umbrales configurables

**Similarity Threshold** (default: 0.75):
- `0.65` - Más permisivo (mejor UX, menor seguridad)
- `0.75` - Balance recomendado
- `0.85` - Más estricto (mayor seguridad, menor UX)

**Anti-spoofing Threshold** (default: 0.5):
- Score < 0.5 → Voz en vivo ✓
- Score ≥ 0.5 → Posible spoofing ✗

## 🧪 Testing con Postman

### Collection Structure
```
Voice Biometrics API
├── Enrollment
│   ├── 1. Start Enrollment
│   ├── 2. Add Sample (Phrase 1)
│   ├── 3. Add Sample (Phrase 2)
│   ├── 4. Add Sample (Phrase 3)
│   ├── 5. Complete Enrollment
│   └── 6. Get Status
│
└── Verification
    ├── 1. Start Verification
    ├── 2. Verify Voice
    ├── 3. Quick Verify
    └── 4. Get History
```

### Variables de entorno Postman
```json
{
  "base_url": "http://localhost:8000",
  "enrollment_id": "",
  "verification_id": "",
  "user_id": "",
  "phrase_id": ""
}
```

## 📈 Métricas y Calidad

### Enrollment Quality Score
Calculado como similitud promedio entre todas las muestras:
```python
quality_score = mean([cosine_similarity(sample_i, sample_j) for all pairs])
```

**Rangos**:
- `0.90 - 1.00` - Excelente
- `0.80 - 0.89` - Bueno
- `0.70 - 0.79` - Aceptable
- `< 0.70` - Pobre (considerar re-enrollment)

### Verification Metrics

**Confidence Score**: Similitud coseno normalizada (0.0 - 1.0)

**Decision**:
```python
is_verified = (similarity_score >= threshold) AND (is_live)
```

**Posibles resultados**:
- ✅ `is_verified = true` - Usuario autenticado
- ❌ `is_verified = false` - Autenticación fallida

**Razones de fallo**:
1. Baja similitud (`similarity_score < 0.75`)
2. Posible spoofing (`anti_spoofing_score >= 0.5`)
3. Usuario no enrolado (sin voiceprint)
4. Frase incorrecta (phrase_id no coincide)

## 🔐 Seguridad

### Implementado
- ✅ Validación de phrase_id en sesión
- ✅ Validación de embeddings (dimensión, NaN, infinitos)
- ✅ Anti-spoofing opcional
- ✅ Auditoría completa (audit_log)
- ✅ Limpieza de sesiones después de uso
- ✅ Exclusión de frases recientes

### Pendiente
- ⏳ Rate limiting (5 intentos/minuto)
- ⏳ Bloqueo temporal después de N fallos
- ⏳ Timeout de sesiones (5 minutos)
- ⏳ Detección de ataques de replay
- ⏳ Logging de IPs y user agents
- ⏳ Encriptación de embeddings en DB

## 📖 Referencias

### Documentos relacionados
- `Backend/ENROLLMENT_MODULE_SUMMARY.md` - Detalles del módulo de enrollment
- `Backend/VERIFICATION_MODULE_SUMMARY.md` - Detalles del módulo de verification
- `Backend/API_DOCUMENTATION.md` - Documentación completa de la API
- `COMMANDS_CHEATSHEET.md` - Comandos útiles del sistema

### Arquitectura
- **Patrón de diseño**: Repository Pattern, Service Layer
- **Inyección de dependencias**: FastAPI Depends
- **Gestión de sesiones**: In-memory (migrar a Redis en producción)
- **Base de datos**: PostgreSQL con asyncpg

## 🚀 Próximos pasos

1. **Frontend**:
   - Interfaz de enrollment con grabadora de audio
   - Interfaz de verificación con feedback en tiempo real
   - Visualización de quality score y confidence

2. **Backend**:
   - Migrar sesiones a Redis
   - Implementar rate limiting
   - Agregar métricas de FAR/FRR
   - Sistema de reentrenamiento periódico

3. **Testing**:
   - Tests unitarios para servicios
   - Tests de integración para endpoints
   - Tests de carga (performance)
   - Tests de seguridad (penetration)

4. **Producción**:
   - Docker Compose para orquestación
   - CI/CD con GitHub Actions
   - Monitoreo con Prometheus/Grafana
   - Backup automático de DB

## 📞 Soporte

Para dudas o problemas:
1. Revisar logs: `Backend/logs/`
2. Verificar Docker: `docker-compose ps`
3. Revisar documentación API
4. Consultar cheatsheet de comandos

---

**Estado**: ✅ Módulos de enrollment y verification completamente funcionales
**Última actualización**: 20 de noviembre de 2025
