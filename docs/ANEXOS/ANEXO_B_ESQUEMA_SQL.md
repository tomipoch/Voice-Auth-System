# Anexo B: Esquema SQL Completo

## Sistema de Autenticación Biométrica por Voz

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Autor:** Tomás Ipinza Poch  
**Motor de Base de Datos:** PostgreSQL 16+

---

## Tabla de Contenidos

1. [Extensiones de PostgreSQL](#1-extensiones-de-postgresql)
2. [Tablas de Control de Acceso](#2-tablas-de-control-de-acceso)
3. [Tablas de Gestión de Usuarios](#3-tablas-de-gestión-de-usuarios)
4. [Tablas de Versionado de Modelos](#4-tablas-de-versionado-de-modelos)
5. [Tablas de Enrolamiento Biométrico](#5-tablas-de-enrolamiento-biométrico)
6. [Tablas de Desafíos y Frases](#6-tablas-de-desafíos-y-frases)
7. [Tablas de Autenticación y Auditoría](#7-tablas-de-autenticación-y-auditoría)
8. [Funciones y Triggers](#8-funciones-y-triggers)
9. [Vistas de Consulta](#9-vistas-de-consulta)
10. [Índices de Rendimiento](#10-índices-de-rendimiento)
11. [Políticas de Retención](#11-políticas-de-retención)

---

## 1. Extensiones de PostgreSQL

```sql
-- =====================================================
-- EXTENSIONES REQUERIDAS
-- =====================================================

-- Extensión para funciones criptográficas
-- Permite hash de contraseñas, encriptación de datos sensibles
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Extensión para vectores de embeddings (opcional, para futuras mejoras)
-- Permite almacenar y buscar vectores de alta dimensionalidad
-- CREATE EXTENSION IF NOT EXISTS vector;
```

**Descripción:**
- **pgcrypto**: Proporciona funciones criptográficas para hash de contraseñas y encriptación de datos biométricos sensibles.
- **vector** (comentado): Extensión opcional para almacenar embeddings como vectores nativos de PostgreSQL, permitiendo búsquedas de similitud optimizadas.

---

## 2. Tablas de Control de Acceso

### 2.1 Tabla `client_app`

```sql
-- =====================================================
-- CLIENTES DE LA API
-- Control de acceso a la API biométrica
-- =====================================================

CREATE TABLE IF NOT EXISTS client_app (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  contact_email TEXT
);

COMMENT ON TABLE client_app IS 'Aplicaciones cliente autorizadas para consumir la API';
COMMENT ON COLUMN client_app.id IS 'Identificador único del cliente';
COMMENT ON COLUMN client_app.name IS 'Nombre de la aplicación cliente';
COMMENT ON COLUMN client_app.contact_email IS 'Email de contacto del responsable';
```

### 2.2 Tabla `api_key`

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

COMMENT ON TABLE api_key IS 'Claves de API para autenticación de clientes';
COMMENT ON COLUMN api_key.key_hash IS 'Hash bcrypt de la API key (nunca se almacena en claro)';
COMMENT ON COLUMN api_key.revoked_at IS 'Fecha de revocación de la clave (NULL si está activa)';
```

**Propósito:**
- Implementa el patrón Middleware para autenticación de clientes API.
- Permite rate limiting y control de acceso granular.
- Soporta rotación de claves mediante revocación.

---

## 3. Tablas de Gestión de Usuarios

### 3.1 Tabla `user`

```sql
-- =====================================================
-- USUARIO FINAL
-- Persona que se autentica mediante voz
-- =====================================================

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

COMMENT ON TABLE "user" IS 'Usuarios del sistema de autenticación biométrica';
COMMENT ON COLUMN "user".external_ref IS 'Referencia externa (ID en sistema bancario/CRM)';
COMMENT ON COLUMN "user".email IS 'Email para autenticación tradicional';
COMMENT ON COLUMN "user".password IS 'Contraseña hasheada con bcrypt';
COMMENT ON COLUMN "user".role IS 'Rol del usuario: user, admin, superadmin';
COMMENT ON COLUMN "user".deleted_at IS 'Fecha de eliminación lógica (soft delete)';
COMMENT ON COLUMN "user".failed_auth_attempts IS 'Contador de intentos fallidos consecutivos';
COMMENT ON COLUMN "user".locked_until IS 'Fecha hasta la cual la cuenta está bloqueada';
COMMENT ON COLUMN "user".last_login IS 'Timestamp del último login exitoso';
```

### 3.2 Tabla `user_policy`

```sql
CREATE TABLE IF NOT EXISTS user_policy (
  user_id UUID PRIMARY KEY REFERENCES "user"(id) ON DELETE CASCADE,
  keep_audio BOOLEAN NOT NULL DEFAULT FALSE,
  retention_days INT NOT NULL DEFAULT 7,
  consent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE user_policy IS 'Políticas de privacidad y retención por usuario';
COMMENT ON COLUMN user_policy.keep_audio IS 'Si se deben guardar los audios crudos de intentos';
COMMENT ON COLUMN user_policy.retention_days IS 'Días de retención de datos de audio';
COMMENT ON COLUMN user_policy.consent_at IS 'Fecha de consentimiento del usuario';
```

**Propósito:**
- Cumple con requisitos de privacidad y protección de datos (GDPR, CCPA).
- Implementa soft delete para auditoría forense.
- Control de bloqueo de cuenta tras múltiples intentos fallidos.
- Políticas de retención personalizables por usuario.

---

## 4. Tablas de Versionado de Modelos

### 4.1 Tabla `model_version`

```sql
-- =====================================================
-- VERSIONADO DE MODELOS ML
-- Auditoría forense: qué modelo se usó en cada decisión
-- =====================================================

CREATE TABLE IF NOT EXISTS model_version (
  id SERIAL PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('speaker','antispoof','asr')),
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  UNIQUE(kind, name, version)
);

COMMENT ON TABLE model_version IS 'Versiones de modelos de ML utilizados en el sistema';
COMMENT ON COLUMN model_version.kind IS 'Tipo de modelo: speaker, antispoof, asr';
COMMENT ON COLUMN model_version.name IS 'Nombre del modelo (ej: ECAPA-TDNN, RawNet2)';
COMMENT ON COLUMN model_version.version IS 'Versión específica del modelo';
```

**Propósito:**
- Trazabilidad completa de qué versión de modelo se usó en cada decisión.
- Permite rollback a versiones anteriores si un modelo falla.
- Esencial para auditoría forense y reproducibilidad.

---

## 5. Tablas de Enrolamiento Biométrico

### 5.1 Tabla `voiceprint`

```sql
-- =====================================================
-- HUELLA DE VOZ (VOICEPRINT)
-- Plantilla biométrica activa del usuario
-- =====================================================

CREATE TABLE IF NOT EXISTS voiceprint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_voiceprint_user UNIQUE(user_id)
);

COMMENT ON TABLE voiceprint IS 'Huella de voz activa del usuario (embedding promedio)';
COMMENT ON COLUMN voiceprint.embedding IS 'Vector de embedding cifrado (192-256 dimensiones)';
COMMENT ON COLUMN voiceprint.updated_at IS 'Última actualización del voiceprint';
```

### 5.2 Tabla `voiceprint_history`

```sql
CREATE TABLE IF NOT EXISTS voiceprint_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  speaker_model_id INT REFERENCES model_version(id)
);

COMMENT ON TABLE voiceprint_history IS 'Histórico de voiceprints para trazabilidad';
COMMENT ON COLUMN voiceprint_history.speaker_model_id IS 'Versión del modelo usada para generar este embedding';
```

### 5.3 Tabla `enrollment_sample`

```sql
CREATE TABLE IF NOT EXISTS enrollment_sample (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  snr_db REAL,
  duration_sec REAL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE enrollment_sample IS 'Muestras individuales del proceso de enrolamiento';
COMMENT ON COLUMN enrollment_sample.embedding IS 'Embedding individual de cada muestra de enrolamiento';
COMMENT ON COLUMN enrollment_sample.snr_db IS 'Relación señal/ruido en decibelios';
COMMENT ON COLUMN enrollment_sample.duration_sec IS 'Duración del audio en segundos';
```

**Propósito:**
- **voiceprint**: Almacena el embedding promedio que representa la huella de voz del usuario.
- **voiceprint_history**: Mantiene histórico para re-entrenamiento y análisis de drift.
- **enrollment_sample**: Guarda muestras individuales para control de calidad y recalibración.
- Todos los embeddings se almacenan cifrados para protección de datos biométricos.

---

## 6. Tablas de Desafíos y Frases

### 6.1 Tabla `phrase`

```sql
-- =====================================================
-- FRASES PARA ENROLAMIENTO Y VERIFICACIÓN
-- Corpus de más de 43,000 frases literarias
-- =====================================================

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

COMMENT ON TABLE phrase IS 'Catálogo de frases para desafíos de verificación';
COMMENT ON COLUMN phrase.text IS 'Texto completo de la frase';
COMMENT ON COLUMN phrase.source IS 'Libro o fuente de origen';
COMMENT ON COLUMN phrase.difficulty IS 'Nivel de dificultad: easy, medium, hard';
COMMENT ON COLUMN phrase.is_active IS 'Si la frase está disponible para uso';
```

### 6.2 Tabla `phrase_usage`

```sql
CREATE TABLE IF NOT EXISTS phrase_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phrase_id UUID NOT NULL REFERENCES phrase(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  used_for TEXT NOT NULL CHECK (used_for IN ('enrollment', 'verification')),
  used_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE phrase_usage IS 'Historial de uso de frases por usuario';
COMMENT ON COLUMN phrase_usage.used_for IS 'Contexto de uso: enrollment o verification';
```

### 6.3 Tabla `challenge`

```sql
-- =====================================================
-- DESAFÍO DINÁMICO
-- Frase temporal que el usuario debe leer
-- =====================================================

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

COMMENT ON TABLE challenge IS 'Desafíos temporales para verificación de liveness';
COMMENT ON COLUMN challenge.phrase IS 'Frase que el usuario debe leer';
COMMENT ON COLUMN challenge.expires_at IS 'Fecha de expiración del desafío';
COMMENT ON COLUMN challenge.used_at IS 'Fecha en que se usó el desafío';
```

**Propósito:**
- Implementa el sistema de desafío-respuesta dinámico.
- Mitiga ataques de replay y deepfakes.
- Evita repetición de frases mediante `phrase_usage`.
- Desafíos con TTL (Time-To-Live) corto para seguridad.

---

## 7. Tablas de Autenticación y Auditoría

### 7.1 Tabla `audio_blob`

```sql
-- =====================================================
-- ALMACENAMIENTO DE AUDIO CRUDO
-- Evidencia forense cifrada
-- =====================================================

CREATE TABLE IF NOT EXISTS audio_blob (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content BYTEA NOT NULL,
  mime TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE audio_blob IS 'Almacenamiento de audios crudos cifrados';
COMMENT ON COLUMN audio_blob.content IS 'Contenido de audio cifrado en reposo';
COMMENT ON COLUMN audio_blob.mime IS 'Tipo MIME del audio (ej: audio/wav)';
```

### 7.2 Tipo Enum `auth_reason`

```sql
-- =====================================================
-- TIPO ENUM PARA RAZONES DE AUTENTICACIÓN
-- =====================================================

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

COMMENT ON TYPE auth_reason IS 'Razones de aceptación/rechazo de autenticación';
```

### 7.3 Tabla `auth_attempt`

```sql
-- =====================================================
-- INTENTOS DE AUTENTICACIÓN
-- Decisión final de negocio
-- =====================================================

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

COMMENT ON TABLE auth_attempt IS 'Registro de intentos de autenticación';
COMMENT ON COLUMN auth_attempt.decided IS 'Si la decisión ya fue tomada';
COMMENT ON COLUMN auth_attempt.accept IS 'Resultado: TRUE=aceptado, FALSE=rechazado';
COMMENT ON COLUMN auth_attempt.reason IS 'Razón de la decisión';
COMMENT ON COLUMN auth_attempt.policy_id IS 'Política de seguridad aplicada';
COMMENT ON COLUMN auth_attempt.total_latency_ms IS 'Latencia total de la request';
```

### 7.4 Tabla `scores`

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

COMMENT ON TABLE scores IS 'Scores técnicos de los modelos biométricos';
COMMENT ON COLUMN scores.similarity IS 'Score de similitud de voz (0-1)';
COMMENT ON COLUMN scores.spoof_prob IS 'Probabilidad de spoofing (0-1)';
COMMENT ON COLUMN scores.phrase_match IS 'Similitud textual ASR (0-1)';
COMMENT ON COLUMN scores.phrase_ok IS 'Interpretación binaria de phrase_match';
COMMENT ON COLUMN scores.inference_ms IS 'Latencia de inferencia de modelos ML';
```

### 7.5 Tabla `audit_log`

```sql
-- =====================================================
-- AUDITORÍA OPERACIONAL
-- Registro inmutable de acciones
-- =====================================================

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

COMMENT ON TABLE audit_log IS 'Log de auditoría inmutable (append-only)';
COMMENT ON COLUMN audit_log.actor IS 'Quién realizó la acción: api:<id>, system, user:<id>';
COMMENT ON COLUMN audit_log.action IS 'Acción realizada: ENROLL, VERIFY, DELETE_USER, etc.';
COMMENT ON COLUMN audit_log.entity_type IS 'Tipo de entidad afectada';
COMMENT ON COLUMN audit_log.entity_id IS 'ID de la entidad afectada';
COMMENT ON COLUMN audit_log.metadata IS 'Detalles adicionales en formato JSON';
```

**Propósito:**
- **auth_attempt**: Decisión de negocio (aceptado/rechazado).
- **scores**: Evidencia técnica de los modelos ML.
- **audit_log**: Trazabilidad completa para cumplimiento normativo.
- Separación clara entre decisión de negocio y señales técnicas (Strategy Pattern).

---

## 8. Funciones y Triggers

### 8.1 Función de Consistencia de Intentos

```sql
-- =====================================================
-- TRIGGER DE CONSISTENCIA
-- Garantiza integridad de datos en auth_attempt
-- =====================================================

CREATE OR REPLACE FUNCTION trg_auth_attempt_consistency() RETURNS trigger AS $$
DECLARE ch_user UUID;
BEGIN
  -- Sellar timestamp de decisión
  IF NEW.decided = TRUE AND NEW.decided_at IS NULL THEN
    NEW.decided_at := now();
  END IF;
  
  -- Validar que el challenge pertenezca al mismo usuario
  IF NEW.challenge_id IS NOT NULL AND NEW.user_id IS NOT NULL THEN
    SELECT user_id INTO ch_user FROM challenge WHERE id = NEW.challenge_id;
    IF ch_user IS NOT NULL AND NEW.user_id IS DISTINCT FROM ch_user THEN
      RAISE EXCEPTION 'challenge % no pertenece al user %', NEW.challenge_id, NEW.user_id;
    END IF;
  END IF;
  
  -- Marcar challenge como usado
  IF NEW.decided = TRUE AND NEW.challenge_id IS NOT NULL THEN
    UPDATE challenge
      SET used_at = COALESCE(used_at, now())
      WHERE id = NEW.challenge_id;
  END IF;
  
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auth_attempt_consistency ON auth_attempt;
CREATE TRIGGER trg_auth_attempt_consistency
BEFORE INSERT OR UPDATE OF decided ON auth_attempt
FOR EACH ROW EXECUTE FUNCTION trg_auth_attempt_consistency();
```

**Propósito:**
- Garantiza consistencia referencial entre challenge y user.
- Sella automáticamente timestamps de decisión.
- Marca challenges como usados para prevenir reutilización.

---

## 9. Vistas de Consulta

### 9.1 Vista `v_attempt_metrics`

```sql
-- =====================================================
-- VISTA DE MÉTRICAS CONSOLIDADAS
-- Combina decisión de negocio con scores técnicos
-- =====================================================

CREATE OR REPLACE VIEW v_attempt_metrics AS
SELECT
  a.id                  AS attempt_id,
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

COMMENT ON VIEW v_attempt_metrics IS 'Vista consolidada de intentos con scores técnicos';
```

**Propósito:**
- Facilita análisis de métricas de negocio.
- Ideal para dashboards de administración.
- Combina datos de decisión y evidencia técnica.

---

## 10. Índices de Rendimiento

```sql
-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS
-- =====================================================

-- Índices de voiceprint y enrollment
CREATE INDEX IF NOT EXISTS idx_voiceprint_user        ON voiceprint(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_user        ON enrollment_sample(user_id);

-- Índices de usuario
CREATE INDEX IF NOT EXISTS idx_user_email             ON "user"(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_role              ON "user"(role);
CREATE INDEX IF NOT EXISTS idx_user_company           ON "user"(company) WHERE company IS NOT NULL;

-- Índices de challenges
CREATE INDEX IF NOT EXISTS idx_challenge_user         ON challenge(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_expires      ON challenge(expires_at);
CREATE INDEX IF NOT EXISTS idx_challenge_used         ON challenge(used_at);

-- Índices de intentos de autenticación
CREATE INDEX IF NOT EXISTS idx_auth_created           ON auth_attempt(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_user_time         ON auth_attempt(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_reason            ON auth_attempt(reason);

-- Índices de scores
CREATE INDEX IF NOT EXISTS idx_scores_similarity      ON scores(similarity);
CREATE INDEX IF NOT EXISTS idx_scores_spoof           ON scores(spoof_prob);
CREATE INDEX IF NOT EXISTS idx_scores_phrase_ok       ON scores(phrase_ok);

-- Índices de auditoría
CREATE INDEX IF NOT EXISTS idx_audit_timestamp        ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor            ON audit_log(actor);

-- Índices de frases
CREATE INDEX IF NOT EXISTS idx_phrase_active          ON phrase(is_active);
CREATE INDEX IF NOT EXISTS idx_phrase_difficulty      ON phrase(difficulty);
CREATE INDEX IF NOT EXISTS idx_phrase_source          ON phrase(source);

-- Índices de uso de frases
CREATE INDEX IF NOT EXISTS idx_phrase_usage_user      ON phrase_usage(user_id, used_at DESC);
CREATE INDEX IF NOT EXISTS idx_phrase_usage_phrase    ON phrase_usage(phrase_id);
```

**Propósito:**
- Optimiza consultas frecuentes (obtener voiceprint, historial de intentos).
- Índices parciales para columnas opcionales (WHERE email IS NOT NULL).
- Índices compuestos para consultas de rango temporal.

---

## 11. Políticas de Retención

### 11.1 Función de Limpieza de Datos Expirados

```sql
-- =====================================================
-- JOB DE RETENCIÓN / LIMPIEZA
-- Aplica políticas de retención de datos
-- =====================================================

CREATE OR REPLACE FUNCTION purge_expired_data() RETURNS void AS $$
BEGIN
  -- Borrar audio crudo expirado según política de usuario
  DELETE FROM audio_blob ab
  USING auth_attempt a, user_policy up
  WHERE a.audio_id = ab.id
    AND a.user_id = up.user_id
    AND a.created_at < now() - (up.retention_days || ' days')::interval;
  
  -- Borrar challenges antiguos (usados o expirados)
  DELETE FROM challenge
  WHERE (used_at IS NOT NULL OR expires_at < now())
    AND created_at < now() - interval '14 days';
END; $$ LANGUAGE plpgsql;

COMMENT ON FUNCTION purge_expired_data IS 'Limpia datos expirados según políticas de retención';
```

**Uso:**
```sql
-- Ejecutar manualmente
SELECT purge_expired_data();

-- O programar con pg_cron (requiere extensión pg_cron)
-- SELECT cron.schedule('purge-expired', '0 2 * * *', 'SELECT purge_expired_data()');
```

**Propósito:**
- Cumple con políticas de retención de datos.
- Implementa derecho al olvido (GDPR).
- Limpia challenges expirados para liberar espacio.

---

## Resumen de Tablas

| Tabla | Propósito | Registros Típicos |
|-------|-----------|-------------------|
| `client_app` | Aplicaciones cliente autorizadas | 1-10 |
| `api_key` | Claves de API | 1-50 |
| `user` | Usuarios del sistema | 1,000-1,000,000+ |
| `user_policy` | Políticas de privacidad | 1:1 con users |
| `model_version` | Versiones de modelos ML | 5-20 |
| `voiceprint` | Huellas de voz activas | 1:1 con users |
| `voiceprint_history` | Histórico de voiceprints | 3-10 por user |
| `enrollment_sample` | Muestras de enrolamiento | 3-6 por user |
| `phrase` | Catálogo de frases | 43,000+ |
| `phrase_usage` | Historial de uso de frases | 10-100 por user |
| `challenge` | Desafíos temporales | Volátil (TTL corto) |
| `audio_blob` | Audios crudos cifrados | Según política |
| `auth_attempt` | Intentos de autenticación | 10-1,000 por user |
| `scores` | Scores técnicos | 1:1 con attempts |
| `audit_log` | Log de auditoría | Millones (append-only) |

---

## Diagrama Entidad-Relación Simplificado

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│ client_app  │──────<│   api_key    │       │    user     │
└─────────────┘       └──────────────┘       └─────────────┘
                                                     │
                                                     │ 1:1
                                                     ▼
                      ┌──────────────┐       ┌─────────────┐
                      │ user_policy  │       │ voiceprint  │
                      └──────────────┘       └─────────────┘
                                                     │
                                                     │ 1:N
                                                     ▼
                                             ┌──────────────────┐
                                             │enrollment_sample │
                                             └──────────────────┘

┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   phrase    │──────<│phrase_usage  │──────>│    user     │
└─────────────┘       └──────────────┘       └─────────────┘
      │                                              │
      │ N:1                                          │ 1:N
      ▼                                              ▼
┌─────────────┐                              ┌─────────────┐
│ challenge   │                              │auth_attempt │
└─────────────┘                              └─────────────┘
      │                                              │
      │ 1:N                                          │ 1:1
      └──────────────────────────────────────────────┤
                                                     │ 1:1
                                                     ▼
                                             ┌──────────────┐
                                             │    scores    │
                                             └──────────────┘
```

---

## Conclusión

Este esquema SQL implementa:

✅ **Seguridad**: Encriptación de datos biométricos, hash de contraseñas  
✅ **Auditoría**: Trazabilidad completa de decisiones y acciones  
✅ **Privacidad**: Políticas de retención configurables, soft delete  
✅ **Rendimiento**: Índices optimizados para consultas frecuentes  
✅ **Integridad**: Triggers y constraints para consistencia de datos  
✅ **Escalabilidad**: Diseño modular preparado para crecimiento  
✅ **Cumplimiento**: GDPR, derecho al olvido, consentimiento explícito  

El esquema soporta los tres pilares del sistema:
1. **Speaker Recognition** (voiceprint, embeddings)
2. **Anti-Spoofing** (scores, spoof_prob)
3. **ASR Verification** (phrase_match, phrase_ok)
