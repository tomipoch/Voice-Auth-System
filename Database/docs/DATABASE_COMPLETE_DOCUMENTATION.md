# Documentación Completa de la Base de Datos - Voice Biometrics System

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura y Diseño](#arquitectura-y-diseño)
3. [Extensiones de PostgreSQL](#extens iones-de-postgresql)
4. [Schema Completo](#schema-completo)
5. [Tablas Principales](#tablas-principales)
6. [Relaciones y Constraints](#relaciones-y-constraints)
7. [Índices y Performance](#índices-y-performance)
8. [Triggers y Funciones](#triggers-y-funciones)
9. [Vistas](#vistas)
10. [Seguridad y Encriptación](#seguridad-y-encriptación)
11. [Políticas de Retención](#políticas-de-retención)
12. [Queries Comunes](#queries-comunes)
13. [Migraciones](#migraciones)
14. [Optimización y Mantenimiento](#optimización-y-mantenimiento)

---

## 1. Visión General

### Descripción del Sistema

La base de datos **Voice Biometrics DB** es un sistema PostgreSQL 16+ diseñado para soportar autenticación biométrica por voz con las siguientes características principales:

- **Almacenamiento seguro** de voiceprints (embeddings encriptados)
- **Trazabilidad completa** de intentos de autenticación
- **Auditoría forense** con versionado de modelos ML
- **Políticas de privacidad** y derecho al olvido (GDPR-compliant)
- **Dynamic phrase system** con 43,459 frases únicas
- **Optimización para consultas** de alta concurrencia

### Características Principales

✅ **PostgreSQL 16+** con extensiones avanzadas  
✅ **pgcrypto** para generación de UUIDs y hashing  
✅ **Enforcement de integridad** mediante triggers  
✅ **Versionado de modelos ML** para auditoría  
✅ **Soft deletes** para datos de usuarios  
✅ **Timestamp tracking** automático  
✅ **Índices optimizados** para queries comunes  
✅ **Cleanup automático** de datos expirados  
✅ **ENUM types** para valores categóricos  
✅ **JSONB** para metadata flexible  

### Stack Tecnológico

| Componente | Versión |
|-----------|---------|
| **DBMS** | PostgreSQL 16+ |
| **Extensiones** | pgcrypto, uuid-ossp |
| **Lenguaje de Triggers** | PL/pgSQL |
| **Tipos de Datos** | UUID, BYTEA, TIMESTAMPTZ, JSONB, ENUM |

---

## 2. Arquitectura y Diseño

### Principios de Diseño

El schema sigue los siguientes principios:

1. **Normalización**: Hasta 3NF para eliminar redundancia
2. **Integridad Referencial**: Foreign keys con acciones apropiadas
3. **Soft Deletes**: `deleted_at` en vez de DELETE duro para usuarios
4. **Audit Trail**: Registros inmutables de intentos de autenticación
5. **Time Partitioning Ready**: Timestamps para futuro particionamiento
6. **Security by Design**: Encriptación de datos sensibles

### Diagrama ER

```mermaid
erDiagram
    USER ||--o{ VOICEPRINT : "has"
    USER ||--o{ VOICEPRINT_HISTORY : "historical"
    USER ||--o{ ENROLLMENT_SAMPLE : "creates"
    USER ||--o{ CHALLENGE : "receives"
    USER ||--o{ AUTH_ATTEMPT : "attempts"
    USER ||--|| USER_POLICY : "has policy"
    USER ||--o{ PHRASE_USAGE : "uses"
    
    CLIENT_APP ||--o{ API_KEY : "has"
    CLIENT_APP ||--o{ AUTH_ATTEMPT : "initiates"
    
    PHRASE ||--o{ CHALLENGE : "used in"
    PHRASE ||--o{ PHRASE_USAGE : "tracked"
    
    CHALLENGE ||--o{ AUTH_ATTEMPT : "validated in"
    
    AUTH_ATTEMPT ||--|| SCORES : "measured by"
    AUTH_ATTEMPT ||--o| AUDIO_BLOB : "contains"
    
    MODEL_VERSION ||--o{ VOICEPRINT_HISTORY : "created with"
    MODEL_VERSION ||--o{ SCORES : "speaker model"
    MODEL_VERSION ||--o{ SCORES : "antispoof model"
    MODEL_VERSION ||--o{ SCORES : "asr model"
```

### Dominios de Datos

```
┌────────────────────────────────────────────────┐
│           API Access Control                   │
│  • client_app                                  │
│  • api_key                                     │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│            User Management                     │
│  • user                                        │
│  • user_policy                                 │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│        Biometric Enrollment                    │
│  • voiceprint                                  │
│  • voiceprint_history                          │
│  • enrollment_sample                           │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│          Verification System                   │
│  • challenge                                   │
│  • auth_attempt                                │
│  • scores                                      │
│  • audio_blob                                  │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│          Phrase Management                     │
│  • phrase                                      │
│  • phrase_usage                                │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│         Infrastructure                         │
│  • model_version                               │
│  • audit_log                                   │
└────────────────────────────────────────────────┘
```

---

## 3. Extensiones de PostgreSQL

### pgcrypto

**Propósito**: Funciones criptográficas y generación de UUIDs.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

**Uso en el sistema**:
- `gen_random_uuid()`: Generación de PKs

**Funciones disponibles**:
```sql
-- UUID generation
SELECT gen_random_uuid();

-- Password hashing (bcrypt)
SELECT crypt('password', gen_salt('bf', 12));

-- Password verification
SELECT password_hash = crypt('input_password', password_hash);
```

---

## 4. Schema Completo

### Resumen de Tablas

| Tabla | Propósito | Registros Estimados |
|------|-----------|-------------------|
| `client_app` | Clientes de API | 5-10 |
| `api_key` | Keys de autenticación API | 10-20 |
| `user` | Usuarios del sistema | 1K-1M |
| `user_policy` | Políticas de privacidad | 1K-1M |
| `model_version` | Versionado de modelos ML | 10-50 |
| `voiceprint` | Voiceprints activos | 1K-1M |
| `voiceprint_history` | Historial de voiceprints | 5K-5M |
| `enrollment_sample` | Muestras de enrollment | 5K-5M |
| `challenge` | Challenges activos/expirados | 10K-100K |
| `audio_blob` | Audio crudo (opcional) | 0-1M |
| `auth_attempt` | Intentos de autenticación | 100K-10M |
| `scores` | Scores biométricos | 100K-10M |
| `audit_log` | Logs de auditoría | 500K-50M |
| `phrase` | Frases para lectura | 43K |
| `phrase_usage` | Historial de uso de frases | 100K-5M |

---

## 5. Tablas Principales

### 5.1 client_app

**Propósito**: Gestiona clientes que consumen la API biométrica.

```sql
CREATE TABLE IF NOT EXISTS client_app (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  contact_email TEXT
);
```

**Columnas**:
- `id`: UUID único del cliente
- `name`: Nombre identificador del cliente
- `contact_email`: Email de contacto

**Ejemplo**:
```sql
INSERT INTO client_app (name, contact_email) VALUES
  ('Mobile App iOS', 'mobile@company.com'),
  ('Web Portal', 'web@company.com');
```

---

### 5.2 api_key

**Propósito**: Almacena API keys hasheadas para autenticación.

```sql
CREATE TABLE IF NOT EXISTS api_key (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES client_app(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ,
  CONSTRAINT ck_api_key_not_revoked
    CHECK (revoked_at IS NULL OR revoked_at > created_at)
);
```

**Columnas**:
- `id`: UUID único de la key
- `client_id`: FK a client_app
- `key_hash`: Hash de la key (nunca la key en claro)
- `created_at`: Timestamp de creación
- `revoked_at`: NULL si activa, timestamp si revocada

**Constraint**:
- `ck_api_key_not_revoked`: Asegura que revoked_at > created_at

**Uso**:
```sql
-- Check if key is valid
SELECT EXISTS (
  SELECT 1 FROM api_key
  WHERE key_hash = crypt('provided_key', key_hash)
    AND revoked_at IS NULL
);
```

---

### 5.3 user

**Propósito**: Usuarios finales del sistema (quienes autentican).

```sql
CREATE TABLE IF NOT EXISTS "user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref TEXT UNIQUE,
  email TEXT UNIQUE,
  password TEXT,
  first_name TEXT,
  last_name TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'superadmin')),
  company TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,
  failed_auth_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,
  last_login TIMESTAMPTZ
);
```

**Columnas**:
- `id`: UUID único del usuario
- `external_ref`: Referencia externa (ej: ID bancario)
- `email`: Email único (usado para login web)
- `password`: bcrypt hash de la contraseña
- `first_name`, `last_name`: Nombre del usuario
- `role`: Rol del usuario (user/admin/superadmin)
- `company`: Organización del usuario
- `created_at`: Timestamp de registro
- `deleted_at`: Soft delete (NULL = activo)
- `failed_auth_attempts`: Contador de intentos fallidos
- `locked_until`: Timestamp hasta cuando está bloqueado
- `last_login`: Último login exitoso

**Soft Delete**:
```sql
-- Soft delete user
UPDATE "user" SET deleted_at = now() WHERE id = '...';

-- Get active users only
SELECT * FROM "user" WHERE deleted_at IS NULL;
```

**Account Locking**:
```sql
-- Lock account after 5 failed attempts
UPDATE "user"
SET locked_until = now() + interval '30 minutes',
    failed_auth_attempts = failed_auth_attempts + 1
WHERE id = '...' AND failed_auth_attempts >= 4;

-- Check if locked
SELECT locked_until > now() AS is_locked FROM "user" WHERE id = '...';
```

---

### 5.4 user_policy

**Propósito**: Políticas de privacidad y retención por usuario.

```sql
CREATE TABLE IF NOT EXISTS user_policy (
  user_id UUID PRIMARY KEY REFERENCES "user"(id) ON DELETE CASCADE,
  keep_audio BOOLEAN NOT NULL DEFAULT FALSE,
  retention_days INT NOT NULL DEFAULT 7,
  consent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Columnas**:
- `user_id`: FK a user (PK)
- `keep_audio`: ¿Guardar audio crudo de intentos?
- `retention_days`: Días de retención de audio
- `consent_at`: Timestamp de consentimiento

**Uso GDPR**:
- Usuario puede solicitar `keep_audio = FALSE`
- Audio se borra automáticamente después de `retention_days`
- `consent_at` registra cuando el usuario aceptó

---

### 5.5 model_version

**Propósito**: Versionado de modelos ML para auditoría forense.

```sql
CREATE TABLE IF NOT EXISTS model_version (
  id SERIAL PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('speaker','antispoof','asr')),
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  UNIQUE(kind, name, version)
);
```

**Columnas**:
- `id`: ID serial (usado en FKs)
- `kind`: Tipo de modelo (speaker/antispoof/asr)
- `name`: Nombre del modelo
- `version`: Versión del modelo

**Ejemplos**:
```sql
INSERT INTO model_version (kind, name, version) VALUES
  ('speaker', 'ECAPA-TDNN', '1.0.0'),
  ('speaker', 'x-vector', '1.0.0'),
  ('antispoof', 'AASIST', '1.0.0'),
  ('antispoof', 'RawNet2', '1.0.0'),
  ('asr', 'Wav2Vec2-CommonVoice-ES', '1.0.0');
```

**Propósito de Auditoría**:
- Cada `auth_attempt` registra qué modelos se usaron
- Permite rastrear cambios en performance tras updates de modelos
- Cumple con requisitos de trazabilidad forense

---

### 5.6 voiceprint

**Propósito**: Almacena el voiceprint activo de cada usuario.

```sql
CREATE TABLE IF NOT EXISTS voiceprint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_voiceprint_user UNIQUE(user_id)
);
```

**Columnas**:
- `id`: UUID único del voiceprint
- `user_id`: FK a user (UNIQUE - un voiceprint por usuario)
- `embedding`: Embedding encriptado (512-D float32 vector → ~2KB)
- `created_at`: Timestamp de creación
- `updated_at`: Timestamp de última actualización

**Constraint**:
- `uq_voiceprint_user`: Asegura un solo voiceprint activo por usuario

**Encriptación**:
```python
# Backend encripta antes de guardar
encrypted_embedding = fernet.encrypt(embedding.tobytes())
```

**Nota**: El voiceprint es el promedio normalizado de 5 muestras de enrollment.

---

### 5.7 voiceprint_history

**Propósito**: Historial de voiceprints para trazabilidad.

```sql
CREATE TABLE IF NOT EXISTS voiceprint_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  speaker_model_id INT REFERENCES model_version(id)
);
```

**Columnas**:
- `id`: UUID único del registro histórico
- `user_id`: FK a user
- `embedding`: Embedding encriptado
- `created_at`: Timestamp de creación
- `speaker_model_id`: FK a model_version (qué modelo lo generó)

**Uso**:
- Cada vez que se actualiza un voiceprint, el anterior se guarda aquí
- Permite rollback en caso de re-enrollment problemático
- Auditoría forense: "¿Qué voiceprint tenía el usuario el 2024-01-15?"

---

### 5.8 enrollment_sample

**Propósito**: Muestras individuales de enrollment (5 por usuario).

```sql
CREATE TABLE IF NOT EXISTS enrollment_sample (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  snr_db REAL,
  duration_sec REAL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Columnas**:
- `id`: UUID único de la muestra
- `user_id`: FK a user
- `embedding`: Embedding de esta muestra específica
- `snr_db`: Signal-to-Noise Ratio (calidad de audio)
- `duration_sec`: Duración del audio grabado
- `created_at`: Timestamp

**Uso**:
```sql
-- Get all enrollment samples for a user
SELECT * FROM enrollment_sample
WHERE user_id = '...'
ORDER BY created_at ASC;

-- Calculate average quality
SELECT AVG(snr_db) AS avg_quality
FROM enrollment_sample
WHERE user_id = '...';
```

---

### 5.9 challenge

**Propósito**: Challenges dinámicos (frases que el usuario debe leer).

```sql
CREATE TABLE IF NOT EXISTS challenge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
  phrase TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_challenge_time
    CHECK (
      expires_at > created_at AND
      (used_at IS NULL OR used_at >= created_at)
    )
);
```

**Columnas**:
- `id`: UUID único del challenge
- `user_id`: FK a user (puede ser NULL para challenges genéricos)
- `phrase`: Texto de la frase a leer
- `expires_at`: No reutilizable después de este timestamp
- `used_at`: Marca cuando fue consumido (NULL = no usado)
- `created_at`: Timestamp de creación

**Constraint**:
- `ck_challenge_time`: Asegura `expires_at > created_at` y `used_at >= created_at`

**Lifecycle**:
```
1. Created → expires_at = now() + 5 minutes
2. Used in auth_attempt → used_at = now()
3. Expired → purge_expired_data() lo elimina después de 14 días
```

**Anti-Replay**:
- Cada challenge expira en 5 minutos
- Una vez usado, no puede reutilizarse
- Mitiga ataques de replay

---

### 5.10 audio_blob

**Propósito**: Almacenamiento opcional de audio crudo encriptado.

```sql
CREATE TABLE IF NOT EXISTS audio_blob (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content BYTEA NOT NULL,
  mime TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Columnas**:
- `id`: UUID único del blob
- `content`: Audio encriptado (BYTEA)
- `mime`: Tipo MIME (ej: "audio/webm")
- `created_at`: Timestamp

**Uso**:
- Solo si `user_policy.keep_audio = TRUE`
- Usado para auditoría forense / peritaje antifraude
- Se borra automáticamente según `retention_days`

**Tamaño**:
- Audio webm de 5 segundos ≈ 50-100 KB
- Con 1M usuarios haciendo 10 verificaciones/mes = ~5-10 GB/mes

---

### 5.11 auth_attempt

**Propósito**: Registro de intentos de autenticación (decisión final).

```sql
DO $$ BEGIN
  CREATE TYPE auth_reason AS ENUM (
    'ok',
    'low_similarity',
    'spoof',
    'bad_phrase',
    'expired_challenge',
    'error'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS auth_attempt (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
  client_id UUID REFERENCES client_app(id) ON DELETE SET NULL,
  challenge_id UUID REFERENCES challenge(id) ON DELETE SET NULL,
  audio_id UUID REFERENCES audio_blob(id) ON DELETE SET NULL,
  
  decided BOOLEAN NOT NULL DEFAULT FALSE,
  accept BOOLEAN,
  reason auth_reason,
  
  policy_id TEXT,
  total_latency_ms INT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ,
  
  CONSTRAINT ck_accept_consistency CHECK (
    (decided = FALSE AND accept IS NULL) OR
    (decided = TRUE  AND accept IS NOT NULL)
  )
);
```

**Columnas**:
- `id`: UUID único del intento
- `user_id`: FK a user
- `client_id`: FK a client_app
- `challenge_id`: FK a challenge
- `audio_id`: FK a audio_blob (opcional)
- `decided`: ¿Ya se resolvió? (proceso completo)
- `accept`: TRUE = autenticado, FALSE = rechazado
- `reason`: Razón del resultado (ENUM)
- `policy_id`: Política de riesgo usada (ej: 'bank_strict_v1')
- `total_latency_ms`: Latencia end-to-end
- `created_at`: Timestamp de inicio
- `decided_at`: Timestamp de decisión final

**auth_reason ENUM**:
- `ok`: Autenticado exitosamente
- `low_similarity`: Similarity < threshold
- `spoof`: Detectado como spoofing
- `bad_phrase`: Frase no coincide
- `expired_challenge`: Challenge expirado
- `error`: Error del sistema

**Constraint**:
- `ck_accept_consistency`: `decided = TRUE` implica `accept IS NOT NULL`

**Uso**:
```sql
-- Get successful attempts for a user
SELECT * FROM auth_attempt
WHERE user_id = '...' AND accept = TRUE
ORDER BY created_at DESC;

-- Calculate success rate
SELECT
  COUNT(*) FILTER (WHERE accept = TRUE) AS successful,
  COUNT(*) FILTER (WHERE accept = FALSE) AS failed,
  COUNT(*) FILTER (WHERE accept = TRUE)::FLOAT / COUNT(*)::FLOAT AS success_rate
FROM auth_attempt
WHERE user_id = '...';
```

---

### 5.12 scores

**Propósito**: Scores biométricos técnicos de cada intento.

```sql
CREATE TABLE IF NOT EXISTS scores (
  attempt_id UUID PRIMARY KEY REFERENCES auth_attempt(id) ON DELETE CASCADE,
  
  similarity REAL NOT NULL,
  spoof_prob REAL NOT NULL,
  phrase_match REAL NOT NULL,
  phrase_ok BOOLEAN,
  
  inference_ms INT,
  
  speaker_model_id INT REFERENCES model_version(id),
  antispoof_model_id INT REFERENCES model_version(id),
  asr_model_id INT REFERENCES model_version(id)
);
```

**Columnas**:
- `attempt_id`: FK a auth_attempt (PK - relación 1:1)
- `similarity`: Score de similitud de voz (0.0-1.0)
- `spoof_prob`: Probabilidad de spoofing (0.0-1.0, 0=genuino)
- `phrase_match`: Similitud textual ASR (0.0-1.0)
- `phrase_ok`: Interpretación binaria de phrase_match
- `inference_ms`: Latencia de modelos ML
- `speaker_model_id`: FK a model_version (ECAPA-TDNN/x-vector)
- `antispoof_model_id`: FK a model_version (AASIST/RawNet2)
- `asr_model_id`: FK a model_version (Wav2Vec2)

**Separación de Concerns**:
- `auth_attempt`: Decisión de negocio (accept/reject)
- `scores`: Señales técnicas crudas

**Análisis**:
```sql
-- Distribution of similarity scores
SELECT
  CASE
    WHEN similarity >= 0.9 THEN '0.9-1.0'
    WHEN similarity >= 0.8 THEN '0.8-0.9'
    WHEN similarity >= 0.7 THEN '0.7-0.8'
    WHEN similarity >= 0.6 THEN '0.6-0.7'
    ELSE '<0.6'
  END AS similarity_range,
  COUNT(*)
FROM scores
GROUP BY similarity_range;

-- High spoof probability attempts
SELECT a.*, s.spoof_prob
FROM auth_attempt a
JOIN scores s ON s.attempt_id = a.id
WHERE s.spoof_prob > 0.7
ORDER BY s.spoof_prob DESC;
```

---

### 5.13 audit_log

**Propósito**: Registro de auditoría operacional.

```sql
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  metadata JSONB,
  success BOOLEAN DEFAULT TRUE,
  error_message TEXT
);
```

**Columnas**:
- `id`: BIGSERIAL (auto-increment)
- `timestamp`: Timestamp del evento
- `actor`: Quién realizó la acción ('user:uuid', 'api:uuid', 'system')
- `action`: Acción realizada ('ENROLL', 'VERIFY', 'DELETE_USER', etc.)
- `entity_type`: Tipo de entidad ('user', 'voiceprint', 'phrase', etc.)
- `entity_id`: ID de la entidad afectada
- `metadata`: Detalles extras en JSON
- `success`: ¿Fue exitosa?
- `error_message`: Mensaje de error si `success = FALSE`

**Ejemplos de eventos**:
```sql
-- User enrolled
INSERT INTO audit_log (actor, action, entity_type, entity_id, metadata)
VALUES ('system', 'ENROLL', 'user', '...', '{"samples": 5, "quality": 0.87}');

-- API key rotated
INSERT INTO audit_log (actor, action, entity_type, entity_id)
VALUES ('admin:...', 'ROTATE_KEY', 'api_key', '...');

-- Failed verification
INSERT INTO audit_log (actor, action, entity_type, entity_id, success, error_message)
VALUES ('user:...', 'VERIFY', 'auth_attempt', '...', FALSE, 'low_similarity');
```

**Queries**:
```sql
-- Recent actions by user
SELECT * FROM audit_log
WHERE actor = 'user:...'
ORDER BY timestamp DESC
LIMIT 50;

-- Failed actions in last 24 hours
SELECT * FROM audit_log
WHERE success = FALSE
  AND timestamp > now() - interval '24 hours'
ORDER BY timestamp DESC;
```

---

### 5.14 phrase

**Propósito**: Biblioteca de frases para enrollment y verification.

```sql
CREATE TABLE IF NOT EXISTS phrase (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text TEXT NOT NULL,
  source TEXT,
  word_count INTEGER NOT NULL,
  char_count INTEGER NOT NULL,
  language TEXT NOT NULL DEFAULT 'es',
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_phrase_length CHECK (char_count >= 20 AND char_count <= 500)
);
```

**Columnas**:
- `id`: UUID único de la frase
- `text`: Texto de la frase
- `source`: Libro de origen
- `word_count`: Número de palabras
- `char_count`: Número de caracteres
- `language`: Idioma (default: 'es')
- `difficulty`: Nivel de dificultad
- `is_active`: Disponible para uso
- `created_at`: Timestamp

**Constraint**:
- `ck_phrase_length`: 20 ≤ char_count ≤ 500

**Distribución**:
```sql
SELECT difficulty, COUNT(*) AS total
FROM phrase
WHERE is_active = TRUE
GROUP BY difficulty;

-- Resultado:
-- easy    | 6637
-- medium  | 25063
-- hard    | 11759
-- TOTAL   | 43459
```

---

### 5.15 phrase_usage

**Propósito**: Historial de uso de frases por usuario.

```sql
CREATE TABLE IF NOT EXISTS phrase_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phrase_id UUID NOT NULL REFERENCES phrase(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  used_for TEXT NOT NULL CHECK (used_for IN ('enrollment', 'verification')),
  used_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Columnas**:
- `id`: UUID único del registro
- `phrase_id`: FK a phrase
- `user_id`: FK a user
- `used_for`: Tipo de uso (enrollment/verification)
- `used_at`: Timestamp de uso

**Propósito**:
- Evitar repetir frases frecuentemente para el mismo usuario
- El backend excluye las últimas 50 frases usadas al generar challenges

**Query**:
```sql
-- Get recent phrases for user (to exclude)
SELECT phrase_id
FROM phrase_usage
WHERE user_id = '...'
ORDER BY used_at DESC
LIMIT 50;
```

---

## 6. Relaciones y Constraints

### Foreign Keys

```mermaid
graph TD
    user -->|voiceprint.user_id| voiceprint
    user -->|enrollment_sample.user_id| enrollment_sample
    user -->|voiceprint_history.user_id| voiceprint_history
    user -->|challenge.user_id| challenge
    user -->|auth_attempt.user_id| auth_attempt
    user -->|user_policy.user_id| user_policy
    user -->|phrase_usage.user_id| phrase_usage
    
    client_app -->|api_key.client_id| api_key
    client_app -->|auth_attempt.client_id| auth_attempt
    
    phrase -->|challenge.phrase| challenge
    phrase -->|phrase_usage.phrase_id| phrase_usage
    
    challenge -->|auth_attempt.challenge_id| auth_attempt
    
    auth_attempt -->|scores.attempt_id| scores
    auth_attempt -->|audio_blob| audio_blob
    
    model_version -->|voiceprint_history| voiceprint_history
    model_version -->|scores| scores
```

### Cascade Actions

| FK | ON DELETE | Razón |
|----|-----------|-------|
| `api_key.client_id` | CASCADE | Si se borra cliente, borrar sus keys |
| `voiceprint.user_id` | CASCADE | Si se borra usuario, borrar voiceprint |
| `enrollment_sample.user_id` | CASCADE | Si se borra usuario, borrar muestras |
| `auth_attempt.user_id` | SET NULL | Mantener histórico anonimizado |
| `scores.attempt_id` | CASCADE | Si se borra attempt, borrar scores |

### Unique Constraints

| Tabla | Columnas | Propósito |
|-------|----------|-----------|
| `client_app` | `name` | No duplicar nombres de clientes |
| `user` | `email` | Un email por usuario |
| `voiceprint` | `user_id` | Un voiceprint por usuario |
| `model_version` | `(kind, name, version)` | No duplicar versiones |

### Check Constraints

```sql
-- Role validation
role CHECK (role IN ('user', 'admin', 'superadmin'))

-- Difficulty validation
difficulty CHECK (difficulty IN ('easy', 'medium', 'hard'))

-- Phrase length
char_count CHECK (char_count >= 20 AND char_count <= 500)

-- Timestamp consistency
expires_at > created_at

-- Decision consistency
(decided = FALSE AND accept IS NULL) OR (decided = TRUE AND accept IS NOT NULL)
```

---

## 7. Índices y Performance

### Índices Principales

```sql
-- Voiceprint lookups
CREATE INDEX idx_voiceprint_user ON voiceprint(user_id);
CREATE INDEX idx_enrollment_user ON enrollment_sample(user_id);

-- User authentication
CREATE INDEX idx_user_email ON "user"(email) WHERE email IS NOT NULL;
CREATE INDEX idx_user_role ON "user"(role);
CREATE INDEX idx_user_company ON "user"(company) WHERE company IS NOT NULL;

-- Challenge management
CREATE INDEX idx_challenge_user ON challenge(user_id);
CREATE INDEX idx_challenge_expires ON challenge(expires_at);
CREATE INDEX idx_challenge_used ON challenge(used_at);

-- Auth attempt queries
CREATE INDEX idx_auth_created ON auth_attempt(created_at);
CREATE INDEX idx_auth_user_time ON auth_attempt(user_id, created_at DESC);
CREATE INDEX idx_auth_reason ON auth_attempt(reason);

-- Scores analysis
CREATE INDEX idx_scores_similarity ON scores(similarity);
CREATE INDEX idx_scores_spoof ON scores(spoof_prob);
CREATE INDEX idx_scores_phrase_ok ON scores(phrase_ok);

-- Audit log
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_actor ON audit_log(actor);

-- Phrase selection
CREATE INDEX idx_phrase_active ON phrase(is_active);
CREATE INDEX idx_phrase_difficulty ON phrase(difficulty);
CREATE INDEX idx_phrase_source ON phrase(source);

-- Phrase usage
CREATE INDEX idx_phrase_usage_user ON phrase_usage(user_id, used_at DESC);
CREATE INDEX idx_phrase_usage_phrase ON phrase_usage(phrase_id);
```

### Partial Indexes

Índices parciales para optimizar queries comunes:

```sql
-- Only active users
CREATE INDEX idx_user_email ON "user"(email) WHERE email IS NOT NULL;

-- Only active phrases
CREATE INDEX idx_phrase_active_difficulty
ON phrase(difficulty) WHERE is_active = TRUE;

-- Only decided attempts
CREATE INDEX idx_auth_decided
ON auth_attempt(user_id, created_at DESC) WHERE decided = TRUE;
```

### Composite Indexes

```sql
-- User + timestamp (VERY common query)
CREATE INDEX idx_auth_user_time ON auth_attempt(user_id, created_at DESC);

-- Phrase usage (for exclusion logic)
CREATE INDEX idx_phrase_usage_user ON phrase_usage(user_id, used_at DESC);
```

### Index Maintenance

```sql
-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan;

-- Unused indexes (candidates for removal)
SELECT * FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND idx_tup_read = 0;

-- Rebuild index
REINDEX INDEX idx_auth_user_time;
```

---

## 8. Triggers y Funciones

### 8.1 trg_auth_attempt_consistency

**Propósito**: Mantener consistencia en auth_attempt.

```sql
CREATE OR REPLACE FUNCTION trg_auth_attempt_consistency() RETURNS trigger AS $$
DECLARE ch_user UUID;
BEGIN
  -- Auto-timestamp decision
  IF NEW.decided = TRUE AND NEW.decided_at IS NULL THEN
    NEW.decided_at := now();
  END IF;

  -- Validate challenge belongs to user
  IF NEW.challenge_id IS NOT NULL AND NEW.user_id IS NOT NULL THEN
    SELECT user_id INTO ch_user FROM challenge WHERE id = NEW.challenge_id;
    IF ch_user IS NOT NULL AND NEW.user_id IS DISTINCT FROM ch_user THEN
      RAISE EXCEPTION 'challenge % no pertenece al user %', NEW.challenge_id, NEW.user_id;
    END IF;
  END IF;

  -- Mark challenge as used
  IF NEW.decided = TRUE AND NEW.challenge_id IS NOT NULL THEN
    UPDATE challenge
      SET used_at = COALESCE(used_at, now())
      WHERE id = NEW.challenge_id;
  END IF;

  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auth_attempt_consistency
BEFORE INSERT OR UPDATE OF decided ON auth_attempt
FOR EACH ROW EXECUTE FUNCTION trg_auth_attempt_consistency();
```

**Funciones**:
1. **Auto-timestamp**: Sella `decided_at` cuando `decided = TRUE`
2. **Validación**: Asegura que `challenge.user_id = auth_attempt.user_id`
3. **Mark used**: Marca `challenge.used_at` cuando se decide

---

## 9. Vistas

### v_attempt_metrics

**Propósito**: Combinar datos de `auth_attempt` y `scores` para análisis.

```sql
CREATE OR REPLACE VIEW v_attempt_metrics AS
SELECT
  a.id AS attempt_id,
  a.created_at,
  a.decided_at,
  a.accept,
  a.reason,
  a.policy_id,
  a.total_latency_ms,
  s.similarity,
  s.spoof_prob,
  s.phrase_match,
  s.phrase_ok,
  s.inference_ms,
  a.user_id,
  a.client_id,
  a.challenge_id
FROM auth_attempt a
JOIN scores s ON s.attempt_id = a.id;
```

**Uso**:
```sql
-- Get metrics for failed attempts
SELECT * FROM v_attempt_metrics
WHERE accept = FALSE
ORDER BY created_at DESC;

-- Average metrics by user
SELECT
  user_id,
  COUNT(*) AS total_attempts,
  AVG(similarity) AS avg_similarity,
  AVG(spoof_prob) AS avg_spoof,
  AVG(total_latency_ms) AS avg_latency
FROM v_attempt_metrics
GROUP BY user_id;
```

---

## 10. Seguridad y Encriptación

### Datos Encriptados

| Tabla | Columna | Tipo | Algoritmo |
|-------|---------|------|-----------|
| `api_key` | `key_hash` | TEXT | bcrypt |
| `user` | `password` | TEXT | bcrypt |
| `voiceprint` | `embedding` | BYTEA | Fernet (AES-128) |
| `enrollment_sample` | `embedding` | BYTEA | Fernet (AES-128) |
| `audio_blob` | `content` | BYTEA | Fernet (AES-128) |

### Password Hashing

```sql
-- Hash password (bcrypt, cost=12)
SELECT crypt('user_password', gen_salt('bf', 12));

-- Verify password
SELECT password = crypt('provided_password', password) AS is_valid
FROM "user" WHERE email = 'user@example.com';
```

### Embedding Encryption

**Backend (Python)**:
```python
from cryptography.fernet import Fernet

class EmbeddingEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, embedding: np.ndarray) -> bytes:
        serialized = embedding.tobytes()
        return self.cipher.encrypt(serialized)
    
    def decrypt(self, encrypted: bytes) -> np.ndarray:
        decrypted = self.cipher.decrypt(encrypted)
        return np.frombuffer(decrypted, dtype=np.float32)
```

### Row-Level Security (RLS)

El schema actual NO usa RLS, pero podría implementarse:

```sql
-- Enable RLS on voiceprint
ALTER TABLE voiceprint ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own voiceprint
CREATE POLICY voiceprint_user_policy ON voiceprint
  FOR SELECT
  USING (user_id = current_setting('app.current_user_id')::UUID);

-- Set current user in session
SET app.current_user_id = 'uuid-here';
```

---

## 11. Políticas de Retención

### Cleanup Function

```sql
CREATE OR REPLACE FUNCTION purge_expired_data() RETURNS void AS $$
BEGIN
  -- Delete expired audio (based on user policy)
  DELETE FROM audio_blob ab
  USING auth_attempt a, user_policy up
  WHERE a.audio_id = ab.id
    AND a.user_id = up.user_id
    AND a.created_at < now() - (up.retention_days || ' days')::interval;

  -- Delete old challenges (used or expired >14 days ago)
  DELETE FROM challenge
  WHERE (used_at IS NOT NULL OR expires_at < now())
    AND created_at < now() - interval '14 days';
END; $$ LANGUAGE plpgsql;
```

### Scheduled Execution

**Con pg_cron** (extension):
```sql
CREATE EXTENSION pg_cron;

-- Run cleanup daily at 3 AM
SELECT cron.schedule('purge-expired-data', '0 3 * * *', 'SELECT purge_expired_data()');
```

**Con backend job** (actual):
```python
# jobs/cleanup_expired_challenges.py
async def cleanup_expired_challenges_job(repo, interval_seconds):
    while True:
        await asyncio.sleep(interval_seconds)
        await repo.delete_expired_challenges()
```

### GDPR Compliance

**Right to be Forgotten**:
```sql
-- Anonymize user data
UPDATE "user"
SET deleted_at = now(),
    email = NULL,
    first_name = 'Deleted',
    last_name = 'User',
    external_ref = NULL
WHERE id = '...';

-- Delete voiceprint
DELETE FROM voiceprint WHERE user_id = '...';

-- Delete audio
DELETE FROM audio_blob ab
USING auth_attempt a
WHERE a.audio_id = ab.id AND a.user_id = '...';
```

---

## 12. Queries Comunes

### Get User with Voiceprint Status

```sql
SELECT
  u.id,
  u.email,
  u.first_name,
  u.last_name,
  u.role,
  EXISTS(SELECT 1 FROM voiceprint WHERE user_id = u.id) AS has_voiceprint,
  u.created_at
FROM "user" u
WHERE u.deleted_at IS NULL;
```

### Recent Verification Attempts

```sql
SELECT
  a.id,
  a.created_at,
  a.accept,
  a.reason,
  s.similarity,
  s.spoof_prob,
  u.email
FROM auth_attempt a
JOIN scores s ON s.attempt_id = a.id
JOIN "user" u ON u.id = a.user_id
WHERE a.decided = TRUE
ORDER BY a.created_at DESC
LIMIT 100;
```

### User Enrollment Progress

```sql
SELECT
  u.id AS user_id,
  u.email,
  COUNT(es.id) AS samples_collected,
  5 - COUNT(es.id) AS samples_remaining,
  EXISTS(SELECT 1 FROM voiceprint WHERE user_id = u.id) AS enrollment_complete
FROM "user" u
LEFT JOIN enrollment_sample es ON es.user_id = u.id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.email;
```

### Phrase Selection (Excluding Recent)

```sql
WITH recent_phrases AS (
  SELECT phrase_id
  FROM phrase_usage
  WHERE user_id = '...'
  ORDER BY used_at DESC
  LIMIT 50
)
SELECT p.id, p.text, p.difficulty
FROM phrase p
WHERE p.is_active = TRUE
  AND p.difficulty = 'medium'
  AND p.id NOT IN (SELECT phrase_id FROM recent_phrases)
ORDER BY RANDOM()
LIMIT 3;
```

### Admin Dashboard Stats

```sql
-- Total users, enrolled, verifications today
SELECT
  COUNT(*) AS total_users,
  COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM voiceprint WHERE user_id = "user".id)) AS enrolled_users,
  (SELECT COUNT(*) FROM auth_attempt WHERE created_at > now() - interval '24 hours') AS attempts_today,
  (SELECT COUNT(*) FROM auth_attempt WHERE accept = TRUE AND created_at > now() - interval '24 hours') AS successful_today
FROM "user"
WHERE deleted_at IS NULL;
```

### Spoof Detection Analysis

```sql
SELECT
  CASE
    WHEN spoof_prob >= 0.8 THEN 'Very High'
    WHEN spoof_prob >= 0.6 THEN 'High'
    WHEN spoof_prob >= 0.4 THEN 'Medium'
    WHEN spoof_prob >= 0.2 THEN 'Low'
    ELSE 'Very Low'
  END AS spoof_risk,
  COUNT(*) AS attempts
FROM scores
GROUP BY spoof_risk
ORDER BY spoof_risk;
```

---

## 13. Migraciones

### Estructura de Migraciones

```
Database/migrations/
├── 001_add_phrase_quality_rules.sql
├── 001_add_user_auth_columns.sql
├── 002_fix_audit_log.sql
├── 003_add_books_table.sql
└── rollback_001.sql
```

### Migration Script

```python
# run_migration.py
import asyncpg
import asyncio

async def run_migration(migration_file):
    conn = await asyncpg.connect('postgresql://...')
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        await conn.execute(sql)
        print(f"✓ Migration {migration_file} completed")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
    finally:
        await conn.close()
```

### Example Migration

```sql
-- migrations/004_add_user_company.sql

-- Add company column
ALTER TABLE "user"
ADD COLUMN company TEXT;

-- Add index
CREATE INDEX idx_user_company ON "user"(company)
WHERE company IS NOT NULL;

-- Update audit log
INSERT INTO audit_log (actor, action, entity_type, metadata)
VALUES ('system', 'MIGRATION', 'user', '{"version": "004", "changes": "added company column"}');
```

---

## 14. Optimización y Mantenimiento

### VACUUM y ANALYZE

```sql
-- Full vacuum (locks table)
VACUUM FULL ANALYZE auth_attempt;

-- Regular vacuum (no lock)
VACUUM ANALYZE auth_attempt;

-- Auto-vacuum config (postgresql.conf)
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
```

### Table Statistics

```sql
-- Table sizes
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Row counts
SELECT COUNT(*) FROM "user";
SELECT COUNT(*) FROM auth_attempt;
SELECT COUNT(*) FROM phrase;
```

### Query Performance

```sql
-- Enable query timing
\timing on

-- Explain analyze
EXPLAIN ANALYZE
SELECT * FROM auth_attempt WHERE user_id = '...';

-- Slow queries (requires pg_stat_statements)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Partitioning (Future)

Para tablas masivas como `auth_attempt`:

```sql
-- Partition by month
CREATE TABLE auth_attempt_2024_01 PARTITION OF auth_attempt
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE auth_attempt_2024_02 PARTITION OF auth_attempt
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

---

## Apéndices

### A. Tipos de Datos

| Tipo PostgreSQL | Tamaño | Uso en Schema |
|-----------------|--------|---------------|
| UUID | 16 bytes | PKs, FKs |
| TEXT | Variable | Strings sin límite |
| INTEGER | 4 bytes | Counters, IDs |
| REAL | 4 bytes | Scores (0.0-1.0) |
| BOOLEAN | 1 byte | Flags |
| TIMESTAMPTZ | 8 bytes | Timestamps con timezone |
| BYTEA | Variable | Embeddings, audio encriptado |
| JSONB | Variable | Metadata flexible |
| ENUM | 4 bytes | auth_reason |

### B. Tamaños Estimados

**Por registro**:
- `user`: ~200 bytes
- `voiceprint`: ~2.5 KB (embedding encriptado)
- `auth_attempt`: ~150 bytes
- `scores`: ~80 bytes
- `phrase`: ~250 bytes
- `audit_log`: ~300 bytes

**Proyección para 100K usuarios**:
- `user`: 20 MB
- `voiceprint`: 250 MB
- `auth_attempt` (10 per user): 150 MB
- `scores`: 80 MB
- **TOTAL**: ~500 MB

### C. Comandos Útiles

```bash
# Conectar a BD
psql postgresql://voice_user:password@localhost:5432/voice_biometrics

# Backup
pg_dump voice_biometrics > backup.sql

# Restore
psql voice_biometrics < backup.sql

# Monitorear conexiones
SELECT * FROM pg_stat_activity;

# Kill connection
SELECT pg_terminate_backend(pid) WHERE pid = 12345;
```

---

**Última actualización**: Diciembre 2024  
**Versión del Schema**: 1.0.0  
**Mantenido por**: Voice Biometrics Team
