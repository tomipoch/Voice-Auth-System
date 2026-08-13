-- =====================================================
-- Voice Biometrics DB - Definitive Schema
-- PostgreSQL 16+, pgvector, pgcrypto
-- =====================================================

-- -----------------
-- Extensions
-- -----------------

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- búsqueda por similitud/fuzzy en phrase.text (tarea 3)

-- Tabla de control del runner de migraciones (infra/db/apply_migrations.py)
CREATE TABLE IF NOT EXISTS schema_migrations (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL UNIQUE,
  checksum TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
  email TEXT UNIQUE,                   -- email for authentication
  password TEXT,                       -- bcrypt hashed password
  first_name TEXT,                     -- user's first name
  last_name TEXT,                      -- user's last name
  rut VARCHAR(12) NULL,                -- Chilean RUT (Rol Único Tributario) - Format: XXXXXXXX-X
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'superadmin')),
  company TEXT,                        -- organization affiliation
  settings JSONB NOT NULL DEFAULT '{}'::jsonb, -- per-user preferences and settings
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,              -- nullo = activo; si no nullo = usuario eliminado / anonimizado
  failed_auth_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,
  last_login TIMESTAMPTZ               -- track last login
);

COMMENT ON COLUMN "user".rut IS 'Chilean RUT (Rol Único Tributario) - Format: XXXXXXXX-X or XX.XXX.XXX-X';

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

CREATE TABLE IF NOT EXISTS voiceprint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,          -- firma biométrica actual del usuario (cifrada)
  speaker_model_id INT REFERENCES model_version(id),  -- versión del modelo speaker usado
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_voiceprint_user UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS voiceprint_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  speaker_model_id INT REFERENCES model_version(id)
);

-- Convergencia de BDs existentes al baseline (CREATE TABLE IF NOT EXISTS no añade columnas a tablas ya creadas)
ALTER TABLE voiceprint ADD COLUMN IF NOT EXISTS speaker_model_id INT REFERENCES model_version(id);
ALTER TABLE voiceprint_history ADD COLUMN IF NOT EXISTS speaker_model_id INT REFERENCES model_version(id);

CREATE TABLE IF NOT EXISTS enrollment_sample (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  embedding BYTEA NOT NULL,   -- embedding individual de esa frase (cifrado)
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
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),  -- renamed from 'at'
  actor TEXT NOT NULL,             -- 'api:<client_id>' | 'system' | 'user:<id>'
  action TEXT NOT NULL,            -- 'ENROLL','VERIFY','DELETE_USER','ROTATE_KEY',...
  entity_type TEXT,                -- tipo lógico ('user','voiceprint','auth_attempt',...)
  entity_id TEXT,                  -- id asociado
  metadata JSONB,                  -- detalles técnicos extras
  success BOOLEAN DEFAULT TRUE,    -- track if action succeeded
  error_message TEXT               -- store error details if failed
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

CREATE INDEX IF NOT EXISTS idx_enrollment_user        ON enrollment_sample(user_id);

-- User authentication and profile indexes
CREATE INDEX IF NOT EXISTS idx_user_role              ON "user"(role);
CREATE INDEX IF NOT EXISTS idx_user_company           ON "user"(company) WHERE company IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_challenge_user         ON challenge(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_expires      ON challenge(expires_at);
CREATE INDEX IF NOT EXISTS idx_challenge_used         ON challenge(used_at);

CREATE INDEX IF NOT EXISTS idx_auth_created           ON auth_attempt(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_user_time         ON auth_attempt(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_reason            ON auth_attempt(reason);
CREATE INDEX IF NOT EXISTS idx_auth_attempt_challenge ON auth_attempt(challenge_id);
CREATE INDEX IF NOT EXISTS idx_auth_attempt_client    ON auth_attempt(client_id);

CREATE INDEX IF NOT EXISTS idx_scores_similarity      ON scores(similarity);
CREATE INDEX IF NOT EXISTS idx_scores_spoof           ON scores(spoof_prob);
CREATE INDEX IF NOT EXISTS idx_scores_phrase_ok       ON scores(phrase_ok);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp        ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor            ON audit_log(actor);

-- Índices redundantes con restricciones UNIQUE o de baja utilidad (convergencia al baseline).
-- DROP es idempotente: en BDs nuevas simplemente no existirán.
DROP INDEX IF EXISTS idx_user_email;        -- redundante: UNIQUE(email)
DROP INDEX IF EXISTS idx_voiceprint_user;   -- redundante: uq_voiceprint_user
DROP INDEX IF EXISTS idx_audit_time;        -- renombrado a idx_audit_timestamp
DROP INDEX IF EXISTS idx_books_filename;    -- redundante: UNIQUE(filename)
DROP INDEX IF EXISTS idx_phrase_active;     -- reemplazado por idx_phrase_filter (parcial + idioma)
DROP INDEX IF EXISTS idx_phrase_difficulty; -- reemplazado por idx_phrase_filter (parcial + idioma)

-- (Los índices específicos de phrase - trgm y filter - se crean en la sección 15
--  después de CREATE TABLE phrase para respetar el orden de dependencias.)

-- =====================================================
-- 13. FRASES PARA ENROLAMIENTO Y VERIFICACIÓN
--     => Almacena frases extraídas de libros para usar
--        en el proceso de enrolamiento y verificación
-- =====================================================

CREATE TABLE IF NOT EXISTS phrase (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text TEXT NOT NULL,                              -- La frase completa
  source TEXT,                                      -- Nombre del libro de origen
  word_count INTEGER NOT NULL,                     -- Número de palabras
  char_count INTEGER NOT NULL,                     -- Número de caracteres
  language TEXT NOT NULL DEFAULT 'es',             -- Idioma de la frase
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,         -- Si está disponible para uso
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_phrase_length CHECK (char_count >= 20 AND char_count <= 500)
);

CREATE INDEX IF NOT EXISTS idx_phrase_source ON phrase(source);

-- =====================================================
-- 14. HISTORIAL DE USO DE FRASES
--     => Registra qué frases se han usado para cada usuario
--        para evitar repeticiones frecuentes
-- =====================================================

CREATE TABLE IF NOT EXISTS phrase_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phrase_id UUID NOT NULL REFERENCES phrase(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  used_for TEXT NOT NULL CHECK (used_for IN ('enrollment', 'verification', 'challenge')),
  used_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_phrase_usage_user ON phrase_usage(user_id, used_at DESC);
CREATE INDEX IF NOT EXISTS idx_phrase_usage_phrase ON phrase_usage(phrase_id);

-- =====================================================
-- 15. LIBROS Y NORMALIZACIÓN DE FRASES
--     => books = metadatos de los PDFs usados para extraer frases;
--        phrase.book_id / challenge.phrase_id / phrase.phoneme_score /
--        phrase.style provenían de migraciones ad-hoc y quedan
--        consolidados aquí (ALTERs: las tablas se crean antes).
-- =====================================================

CREATE TABLE IF NOT EXISTS books (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  author TEXT,
  filename TEXT NOT NULL UNIQUE,
  language TEXT NOT NULL DEFAULT 'es',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE phrase ADD COLUMN IF NOT EXISTS book_id UUID REFERENCES books(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_phrase_book_id ON phrase(book_id);

ALTER TABLE challenge ADD COLUMN IF NOT EXISTS phrase_id UUID REFERENCES phrase(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_challenge_phrase ON challenge(phrase_id);

ALTER TABLE phrase ADD COLUMN IF NOT EXISTS phoneme_score INTEGER DEFAULT 0;
ALTER TABLE phrase ADD COLUMN IF NOT EXISTS style TEXT CHECK (style IN ('narrative', 'descriptive', 'dialogue', 'poetic'));

COMMENT ON COLUMN phrase.phoneme_score IS 'Puntaje de diversidad fonémica (0-100). Mayor = fonemas más variados para mejor captura biométrica.';
COMMENT ON COLUMN phrase.style IS 'Clasificación de estilo textual: narrative, descriptive, dialogue, poetic.';

CREATE INDEX IF NOT EXISTS idx_phrase_phoneme_score ON phrase(phoneme_score);
CREATE INDEX IF NOT EXISTS idx_phrase_style ON phrase(style);

-- Índices de rendimiento para queries reales del backend (TRGM para ILIKE, parcial para filtros)
CREATE INDEX IF NOT EXISTS idx_phrase_text_trgm ON phrase USING gin (text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_phrase_filter
  ON phrase(language, difficulty) WHERE is_active = TRUE;

-- =====================================================
-- 16. REGLAS DE CALIDAD DE FRASES (configurable por admin)
--     => thresholds / rate limits / cleanup usados por
--        PhraseQualityRulesService (provenía de migración ad-hoc).
-- =====================================================

CREATE TABLE IF NOT EXISTS phrase_quality_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('threshold', 'rate_limit', 'cleanup')),
    rule_value JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES "user"(id) ON DELETE SET NULL,

    CONSTRAINT ck_rule_value_has_value CHECK (rule_value ? 'value'),
    CONSTRAINT ck_rule_value_has_description CHECK (rule_value ? 'description')
);

CREATE INDEX IF NOT EXISTS idx_phrase_quality_rules_active
  ON phrase_quality_rules(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_phrase_quality_rules_type ON phrase_quality_rules(rule_type);

CREATE OR REPLACE FUNCTION update_phrase_quality_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_phrase_quality_rules_updated_at ON phrase_quality_rules;
CREATE TRIGGER trg_phrase_quality_rules_updated_at
    BEFORE UPDATE ON phrase_quality_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_phrase_quality_rules_updated_at();

-- =====================================================
-- 17. SESIÓN DE ENROLAMIENTO PERSISTENTE
--     => sobrevive reinicios del servidor (provenía de migración ad-hoc).
-- =====================================================

CREATE TABLE IF NOT EXISTS enrollment_session (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    challenges JSONB NOT NULL,          -- arreglo de desafíos
    samples_collected INTEGER DEFAULT 0,
    challenge_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour'),
    completed_at TIMESTAMPTZ,
    CONSTRAINT enrollment_session_active_unique UNIQUE (user_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_enrollment_session_user ON enrollment_session(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_session_expires ON enrollment_session(expires_at);

COMMENT ON TABLE enrollment_session IS 'Almacenamiento persistente de sesiones de enrolamiento activas - sobrevive reinicios del servidor';

-- =====================================================
-- 18. CONFIGURACIÓN GLOBAL DEL SISTEMA (superadmin)
--     => p. ej. grabación de dataset (provenía de migración ad-hoc).
-- =====================================================

CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_system_settings_updated ON system_settings(updated_at DESC);

COMMENT ON TABLE system_settings IS 'Configuración global del sistema controlada por superadmin';

-- =====================================================
-- 19. DATOS SEMILLA (referencia reproducible)
--     => metadatos de libros, reglas de calidad, settings
--        globales y usuarios de desarrollo. Los datos de
--        runtime (37.407 frases, usuarios reales) se restauran
--        aparte desde data_dump.sql (gitignored, contiene PII).
-- =====================================================

INSERT INTO books (title, author, filename, language) VALUES
  ('1984', 'George Orwell', '1984.pdf', 'es'),
  ('El Jardín Secreto', 'Frances Hodgson Burnett', 'EL_jardin_Secreto.pdf', 'es'),
  ('Edipo Rey', 'Sófocles', 'Edipo-Rey.pdf', 'es'),
  ('El Principito', 'Antoine de Saint-Exupéry', 'El-Principito.pdf', 'es'),
  ('El Diario de Ana Frank', 'Ana Frank', 'El-diario-de-ana-frank.pdf', 'es'),
  ('La Ilíada', 'Homero', 'La-Iliada-Homero.pdf', 'es'),
  ('La Odisea', 'Homero', 'La-Odisea-de-Homero.pdf', 'es'),
  ('La Guerra de los Mundos', 'H.G. Wells', 'La-guerra-de-los-mundos.pdf', 'es'),
  ('Sub Terra', 'Baldomero Lillo', 'Sub-terra.pdf', 'es'),
  ('Veinte Mil Leguas de Viaje Submarino', 'Julio Verne', 'Veinte mil leguas de viaje submarino.pdf', 'es'),
  ('Ben Quiere a Ana', 'Peter Härtling', 'ben-quiere-a-ana.pdf', 'es'),
  ('Charlie y la Fábrica de Chocolate', 'Roald Dahl', 'charly-y-la-fabrica-de-chocolate.pdf', 'es'),
  ('Dioses y Héroes de la Mitología', 'Anónimo', 'dioses-y-heroes-de-la-mitologia.pdf', 'es'),
  ('Don Quijote de la Mancha', 'Miguel de Cervantes', 'don-quijote-de-la-mancha.pdf', 'es'),
  ('El Caso del Futbolista Enmascarado', 'Alfredo Gómez Cerdá', 'el-caso-del-futbolista-enmascarado.pdf', 'es'),
  ('El Hombre Invisible', 'H.G. Wells', 'el-hombre-invisible.pdf', 'es'),
  ('El Niño del Pijama de Rayas', 'John Boyne', 'el-niño-del-pijama-de-rayas.pdf', 'es'),
  ('Frin', 'Luis María Pescetti', 'frin.pdf', 'es'),
  ('La Máquina del Tiempo', 'H.G. Wells', 'la-maquina-del-tiempo.pdf', 'es'),
  ('Las Aventuras de Tom Sawyer', 'Mark Twain', 'las-aventuras-de-tom-sawyer.pdf', 'es'),
  ('Lejos de Frin', 'Luis María Pescetti', 'lejos-de-frin.pdf', 'es'),
  ('Matilda', 'Roald Dahl', 'matilda.pdf', 'es'),
  ('Momo', 'Michael Ende', 'momo.pdf', 'es'),
  ('Sub Sole', 'Baldomero Lillo', 'sub-sole.pdf', 'es'),
  ('Viaje al Centro de la Tierra', 'Julio Verne', 'viaje_al_centro_de_la_tierra.pdf', 'es'),
  ('La Vuelta al Mundo en 80 Días', 'Julio Verne', 'vuelta-al-mundo-en-80-dias.pdf', 'es'),
  -- Libros cuyos PDFs existen en infra/db/Libros/ pero faltaban en la migración 003
  ('Cien Años de Soledad', 'Gabriel García Márquez', 'Cien años de soldedad.pdf', 'es'),
  ('Crónica de una Muerte Anunciada', 'Gabriel García Márquez', 'CRONICA-DE-UNA-MUERTE-ANUNCIADA.pdf', 'es'),
  ('Cuentos de los Hermanos Grimm', 'Hermanos Grimm', 'cuentos_hermanos_grimm.pdf', 'es'),
  ('La Divina Comedia', 'Dante Alighieri', 'Divina comedia.pdf', 'es'),
  ('El Código Da Vinci', 'Dan Brown', 'El Código Da Vinci.pdf', 'es'),
  ('Rayuela', 'Julio Cortázar', 'Julio-Cortazar-Rayuela.pdf', 'es'),
  ('La Casa de los Espíritus', 'Isabel Allende', 'La Casa de los Espíritus.pdf', 'es'),
  ('La Comunidad del Anillo', 'J.R.R. Tolkien', 'La Comunidad del anillo.pdf', 'es'),
  ('La Sombra del Viento', 'Carlos Ruiz Zafón', 'La-Sombra-Del-Viento.pdf', 'es'),
  ('Marianela', 'Benito Pérez Galdós', 'Marianela.pdf', 'es')
ON CONFLICT (filename) DO NOTHING;

INSERT INTO phrase_quality_rules (rule_name, rule_type, rule_value) VALUES
  ('min_success_rate', 'threshold', '{"value": 0.70, "description": "Tasa mínima de éxito para mantener frase activa", "unit": "percentage"}'),
  ('min_asr_score', 'threshold', '{"value": 0.80, "description": "Score mínimo de ASR (reconocimiento de voz)", "unit": "percentage"}'),
  ('min_phrase_ok_rate', 'threshold', '{"value": 0.75, "description": "Tasa mínima de transcripción correcta", "unit": "percentage"}'),
  ('min_attempts_for_analysis', 'threshold', '{"value": 10, "description": "Intentos mínimos antes de analizar frase", "unit": "count"}'),
  ('exclude_recent_phrases', 'threshold', '{"value": 50, "description": "Excluir últimas N frases usadas por usuario", "unit": "count"}'),
  ('max_challenges_per_user', 'rate_limit', '{"value": 3, "description": "Máximo de challenges activos simultáneos por usuario", "unit": "count"}'),
  ('max_challenges_per_hour', 'rate_limit', '{"value": 20, "description": "Máximo de challenges creados por hora por usuario", "unit": "count"}'),
  ('challenge_expiry_minutes', 'cleanup', '{"value": 5, "description": "Minutos hasta que un challenge expire", "unit": "minutes"}'),
  ('cleanup_expired_after_hours', 'cleanup', '{"value": 1, "description": "Borrar challenges expirados después de N horas", "unit": "hours"}'),
  ('cleanup_used_after_hours', 'cleanup', '{"value": 24, "description": "Borrar challenges usados después de N horas", "unit": "hours"}')
ON CONFLICT (rule_name) DO NOTHING;

INSERT INTO system_settings (key, value) VALUES
  ('dataset_recording', '{"enabled": false}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Usuarios de desarrollo (solo se insertan si no existen; producción no los usa)
INSERT INTO "user" (id, email, password, first_name, last_name, role, company, external_ref, created_at)
VALUES (
  gen_random_uuid(),
  'admin@example.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OKi', -- bcrypt de 'admin123'
  'Admin', 'User', 'admin', 'Example Corp', 'admin-001', now()
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO "user" (id, email, password, first_name, last_name, role, company, external_ref, created_at)
VALUES (
  gen_random_uuid(),
  'user@example.com',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- bcrypt de 'user123'
  'Test', 'User', 'user', 'Example Corp', 'user-001', now()
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_policy (user_id, keep_audio, retention_days, consent_at)
SELECT id, FALSE, 7, now()
FROM "user"
WHERE email IN ('admin@example.com', 'user@example.com')
ON CONFLICT (user_id) DO NOTHING;

