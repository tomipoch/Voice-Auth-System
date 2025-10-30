-- =====================================================
-- Voice Biometrics DB - Definitive Schema
-- PostgreSQL 16+, pgvector, pgcrypto
-- =====================================================

-- -----------------
-- Extensions
-- -----------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- 1. CLIENTES DE LA API (control de acceso a la API)
--    => Se usa en el Middleware Pattern para autenticar
--       y rate-limitear quién consume la API biométrica.
-- =====================================================

CREATE TABLE IF NOT EXISTS client_app (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  contact_email TEXT
);

CREATE TABLE IF NOT EXISTS api_key (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES client_app(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL UNIQUE,                 -- hash de la API key (bcrypt/pgcrypto), nunca la key en claro
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ,
  CONSTRAINT ck_api_key_not_revoked
    CHECK (revoked_at IS NULL OR revoked_at > created_at)
);

-- =====================================================
-- 2. USUARIO FINAL (la persona que se autentica por voz)
--    + POLÍTICA DE RETENCIÓN / PRIVACIDAD
--    => Cumple con requisitos de consentimiento, cifrado
--       y derecho al olvido descritos en la Propuesta. :contentReference[oaicite:1]{index=1}
-- =====================================================

CREATE TABLE IF NOT EXISTS "user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref TEXT UNIQUE,            -- id en el sistema bancario / core / CRM
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ               -- nullo = activo; si no nullo = usuario eliminado / anonimizado
);

CREATE TABLE IF NOT EXISTS user_policy (
  user_id UUID PRIMARY KEY REFERENCES "user"(id) ON DELETE CASCADE,
  keep_audio BOOLEAN NOT NULL DEFAULT FALSE,   -- ¿guardamos audio crudo de intentos?
  retention_days INT NOT NULL DEFAULT 7,       -- retención personalizada
  consent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 3. VERSIONADO DE MODELOS
--    => Para auditoría forense: con qué modelo de voz,
--       anti-spoofing y ASR se tomó cada decisión. :contentReference[oaicite:2]{index=2}
-- =====================================================

CREATE TABLE IF NOT EXISTS model_version (
  id SERIAL PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('speaker','antispoof','asr')),
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  UNIQUE(kind, name, version)
);

-- =====================================================
-- 4. ENROLAMIENTO Y FIRMA DE VOZ
--    => "voiceprint" = plantilla activa del usuario
--       (embedding promedio / firma biométrica),
--       "voiceprint_history" = histórico para trazabilidad,
--       "enrollment_sample" = muestras crudas usadas
--       en el enrolamiento (4-6 frases, control de calidad). :contentReference[oaicite:3]{index=3}
-- =====================================================

-- Ajusta vector(256) al tamaño real del embedding (ECAPA-TDNN, x-vector, etc.)
CREATE TABLE IF NOT EXISTS voiceprint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding vector(256) NOT NULL,          -- firma biométrica actual del usuario
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  speaker_model_id INT REFERENCES model_version(id),  -- qué modelo generó esta firma
  CONSTRAINT uq_voiceprint_user UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS voiceprint_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding vector(256) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  speaker_model_id INT REFERENCES model_version(id)
);

CREATE TABLE IF NOT EXISTS enrollment_sample (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding vector(256) NOT NULL,   -- embedding individual de esa frase
  snr_db REAL,                      -- calidad de señal/ruido
  duration_sec REAL,                -- duración útil hablada
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 5. DESAFÍO DINÁMICO / LIVENESS POR FRASE
--    => Texto aleatorio que el usuario debe leer.
--       Mitiga replay/deepfake porque fuerza prueba viva. :contentReference[oaicite:4]{index=4}
-- =====================================================

CREATE TABLE IF NOT EXISTS challenge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
  phrase TEXT NOT NULL,                       -- frase que el usuario debe leer
  expires_at TIMESTAMPTZ NOT NULL,            -- no reutilizable después de cierto tiempo
  used_at TIMESTAMPTZ,                        -- se marca cuando fue consumida en un intento real
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_challenge_time
    CHECK (
      expires_at > created_at AND
      (used_at IS NULL OR used_at >= created_at)
    )
);

-- =====================================================
-- 6. ALMACENAMIENTO DE AUDIO CRUDO / EVIDENCIA
--    => Audio cifrado asociado a un intento.
--       Esto soporta peritaje antifraude y retención
--       configurable por usuario/política. :contentReference[oaicite:5]{index=5}
-- =====================================================

CREATE TABLE IF NOT EXISTS audio_blob (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content BYTEA NOT NULL,          -- audio cifrado en reposo
  mime TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 7. INTENTOS DE AUTENTICACIÓN
--    => auth_attempt = decisión final de negocio
--       (aceptado / rechazado / por qué),
--       más trazabilidad de cliente y política de riesgo.
--    => scores = señales técnicas crudas de biometría
--       (similaridad, spoofing, frase leída, latencia).
--
--    Esta separación DIRECTA refleja:
--    - Strategy Pattern (política de decisión)
--    - Builder Pattern (composición paso a paso del resultado)
--    - Facade biométrica (provee los scores)
--    - AuditRecorderFacade (persiste todo)
--    Todo esto está descrito en tu flujo técnico. :contentReference[oaicite:6]{index=6}
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

CREATE TABLE IF NOT EXISTS auth_attempt (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  user_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
  client_id UUID REFERENCES client_app(id) ON DELETE SET NULL,
  challenge_id UUID REFERENCES challenge(id) ON DELETE SET NULL,
  audio_id UUID REFERENCES audio_blob(id) ON DELETE SET NULL,

  decided BOOLEAN NOT NULL DEFAULT FALSE,      -- ¿ya se resolvió?
  accept BOOLEAN,                               -- TRUE = autenticado exitosamente
  reason auth_reason,                           -- por qué (spoof, low_similarity, etc.)

  policy_id TEXT,                               -- política/estrategia de riesgo usada
                                                -- ej: 'bank_strict_v1', 'demo_relaxed'

  total_latency_ms INT,                         -- latencia end-to-end de la request /verify
                                                -- (útil para SLA bancario)

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ,

  CONSTRAINT ck_accept_consistency CHECK (
    (decided = FALSE AND accept IS NULL) OR
    (decided = TRUE  AND accept IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS scores (
  attempt_id UUID PRIMARY KEY REFERENCES auth_attempt(id) ON DELETE CASCADE,

  similarity REAL NOT NULL,                     -- score de similitud de voz (speaker verification)
  spoof_prob REAL NOT NULL,                     -- prob. de audio falsificado/replay/deepfake
  phrase_match REAL NOT NULL,                   -- similitud textual/ASR (0..1)
  phrase_ok BOOLEAN,                            -- interpretación binaria: ¿dijo la frase correcta?

  inference_ms INT,                             -- latencia de los modelos biométricos (no todo el request)

  speaker_model_id INT REFERENCES model_version(id),
  antispoof_model_id INT REFERENCES model_version(id),
  asr_model_id INT REFERENCES model_version(id)
);

-- =====================================================
-- 8. AUDITORÍA OPERACIONAL
--    => Registro de acciones relevantes
--       (ENROLL, VERIFY, DELETE_USER, etc.),
--       quién las hizo y contra qué entidad.
--       Soporta exigencias de Riesgo y Fraude. :contentReference[oaicite:7]{index=7}
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  at TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT NOT NULL,             -- 'api:<client_id>' | 'system' | 'user:<id>'
  action TEXT NOT NULL,            -- 'ENROLL','VERIFY','DELETE_USER','ROTATE_KEY',...
  entity TEXT,                     -- tipo lógico ('user','voiceprint','auth_attempt',...)
  entity_id TEXT,                  -- id asociado
  meta JSONB                       -- detalles técnicos extras
);

-- =====================================================
-- 9. TRIGGERS DE CONSISTENCIA / TRAZABILIDAD
--    => Sella decisión, asegura integridad entre
--       challenge y user, marca challenge como usado,
--       etc. Eso mantiene evidencia forense coherente.
-- =====================================================

CREATE OR REPLACE FUNCTION trg_auth_attempt_consistency() RETURNS trigger AS $$
DECLARE ch_user UUID;
BEGIN
  -- Si marcamos decidido y no hay timestamp, lo sellamos
  IF NEW.decided = TRUE AND NEW.decided_at IS NULL THEN
    NEW.decided_at := now();
  END IF;

  -- Validar que el challenge pertenezca al mismo user
  IF NEW.challenge_id IS NOT NULL AND NEW.user_id IS NOT NULL THEN
    SELECT user_id INTO ch_user FROM challenge WHERE id = NEW.challenge_id;
    IF ch_user IS NOT NULL AND NEW.user_id IS DISTINCT FROM ch_user THEN
      RAISE EXCEPTION 'challenge % no pertenece al user %', NEW.challenge_id, NEW.user_id;
    END IF;
  END IF;

  -- Si se decidió, marcamos el challenge como usado (si no lo estaba)
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

-- =====================================================
-- 10. VISTAS DE APOYO
--     => Vista de métricas por intento: combina decisión
--        final con señales técnicas y latencia. Ideal para
--        el área de Riesgo/Fraude y para dashboards.
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

-- =====================================================
-- 11. JOB DE RETENCIÓN / LIMPIEZA
--     => Aplica política de retención por usuario:
--        elimina audio crudo expirado y desafíos viejos.
--        Esto cumple con "retención limitada y derecho
--        al olvido / privacidad" descrito en la Propuesta. :contentReference[oaicite:8]{index=8}
-- =====================================================

CREATE OR REPLACE FUNCTION purge_expired_data() RETURNS void AS $$
BEGIN
  -- Borrar audio crudo pasado el período de retención definido por cada usuario
  DELETE FROM audio_blob ab
  USING auth_attempt a, user_policy up
  WHERE a.audio_id = ab.id
    AND a.user_id = up.user_id
    AND a.created_at < now() - (up.retention_days || ' days')::interval;

  -- Borrar challenges viejos (ya usados o expirados hace rato)
  DELETE FROM challenge
  WHERE (used_at IS NOT NULL OR expires_at < now())
    AND created_at < now() - interval '14 days';
END; $$ LANGUAGE plpgsql;

-- =====================================================
-- 12. ÍNDICES
--     => performance de búsquedas comunes:
--        - obtener voiceprint de un usuario
--        - ver historial/enrolamiento
--        - revisar intentos recientes de auth de un user
--        - análisis de riesgo por spoof_prob alta, etc.
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_voiceprint_user        ON voiceprint(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_user        ON enrollment_sample(user_id);

CREATE INDEX IF NOT EXISTS idx_challenge_user         ON challenge(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_expires      ON challenge(expires_at);
CREATE INDEX IF NOT EXISTS idx_challenge_used         ON challenge(used_at);

CREATE INDEX IF NOT EXISTS idx_auth_created           ON auth_attempt(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_user_time         ON auth_attempt(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_reason            ON auth_attempt(reason);

CREATE INDEX IF NOT EXISTS idx_scores_similarity      ON scores(similarity);
CREATE INDEX IF NOT EXISTS idx_scores_spoof           ON scores(spoof_prob);
CREATE INDEX IF NOT EXISTS idx_scores_phrase_ok       ON scores(phrase_ok);

CREATE INDEX IF NOT EXISTS idx_audit_time             ON audit_log(at);
CREATE INDEX IF NOT EXISTS idx_audit_actor            ON audit_log(actor);
