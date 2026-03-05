-- =====================================================
-- Voice Biometrics Database - Schema for Diagram
-- Simplified version: Only tables, columns, PKs, and FKs
-- =====================================================

-- ENUM Type
CREATE TYPE auth_reason AS ENUM (
    'ok', 'low_similarity', 'spoof', 'bad_phrase', 'expired_challenge', 'error'
);

-- =====================================================
-- 1. CLIENT_APP - API Clients
-- =====================================================
CREATE TABLE client_app (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact_email TEXT
);

-- =====================================================
-- 2. API_KEY - Client Authentication
-- =====================================================
CREATE TABLE api_key (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES client_app(id),
    key_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);

-- =====================================================
-- 3. USER - End Users
-- =====================================================
CREATE TABLE "user" (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    first_name TEXT,
    last_name TEXT,
    rut VARCHAR(12),
    role TEXT, -- 'user', 'admin', 'superadmin'
    company TEXT,
    external_ref TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ,
    failed_auth_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login TIMESTAMPTZ,
    settings JSONB
);

-- =====================================================
-- 4. USER_POLICY - Privacy/Retention Settings
-- =====================================================
CREATE TABLE user_policy (
    user_id UUID PRIMARY KEY REFERENCES "user"(id),
    keep_audio BOOLEAN NOT NULL DEFAULT FALSE,
    retention_days INTEGER NOT NULL DEFAULT 7,
    consent_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 5. MODEL_VERSION - ML Model Tracking
-- =====================================================
CREATE TABLE model_version (
    id SERIAL PRIMARY KEY,
    kind TEXT NOT NULL, -- 'speaker', 'antispoof', 'asr'
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    UNIQUE(kind, name, version)
);

-- =====================================================
-- 6. VOICEPRINT - Active Voice Signature
-- =====================================================
CREATE TABLE voiceprint (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES "user"(id),
    embedding BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 7. VOICEPRINT_HISTORY - Historical Signatures
-- =====================================================
CREATE TABLE voiceprint_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id),
    embedding BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    speaker_model_id INTEGER REFERENCES model_version(id)
);

-- =====================================================
-- 8. ENROLLMENT_SAMPLE - Enrollment Audio Samples
-- =====================================================
CREATE TABLE enrollment_sample (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id),
    embedding BYTEA NOT NULL,
    snr_db REAL,
    duration_sec REAL,
    created_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 9. BOOKS - Source Books for Phrases
-- =====================================================
CREATE TABLE books (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    filename TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL DEFAULT 'es',
    created_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 10. PHRASE - Challenge Phrases
-- =====================================================
CREATE TABLE phrase (
    id UUID PRIMARY KEY,
    text TEXT NOT NULL,
    source TEXT,
    word_count INTEGER NOT NULL,
    char_count INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT 'es',
    difficulty TEXT, -- 'easy', 'medium', 'hard'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    book_id UUID REFERENCES books(id)
);

-- =====================================================
-- 11. PHRASE_USAGE - Phrase Usage Tracking
-- =====================================================
CREATE TABLE phrase_usage (
    id UUID PRIMARY KEY,
    phrase_id UUID NOT NULL REFERENCES phrase(id),
    user_id UUID NOT NULL REFERENCES "user"(id),
    used_for TEXT NOT NULL, -- 'enrollment', 'verification', 'challenge'
    used_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 12. PHRASE_QUALITY_RULES - Quality Configuration
-- =====================================================
CREATE TABLE phrase_quality_rules (
    id UUID PRIMARY KEY,
    rule_name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL, -- 'threshold', 'rate_limit', 'cleanup'
    rule_value JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES "user"(id)
);

-- =====================================================
-- 13. CHALLENGE - Dynamic Liveness Challenges
-- =====================================================
CREATE TABLE challenge (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    phrase TEXT NOT NULL,
    phrase_id UUID REFERENCES phrase(id),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 14. AUDIO_BLOB - Encrypted Audio Storage
-- =====================================================
CREATE TABLE audio_blob (
    id UUID PRIMARY KEY,
    content BYTEA NOT NULL,
    mime TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

-- =====================================================
-- 15. AUTH_ATTEMPT - Authentication Decisions
-- =====================================================
CREATE TABLE auth_attempt (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    client_id UUID REFERENCES client_app(id),
    challenge_id UUID REFERENCES challenge(id),
    audio_id UUID REFERENCES audio_blob(id),
    decided BOOLEAN NOT NULL DEFAULT FALSE,
    accept BOOLEAN,
    reason auth_reason,
    policy_id TEXT,
    total_latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ
);

-- =====================================================
-- 16. SCORES - Biometric Analysis Scores
-- =====================================================
CREATE TABLE scores (
    attempt_id UUID PRIMARY KEY REFERENCES auth_attempt(id),
    similarity REAL NOT NULL,
    spoof_prob REAL NOT NULL,
    phrase_match REAL NOT NULL,
    phrase_ok BOOLEAN,
    inference_ms INTEGER,
    speaker_model_id INTEGER REFERENCES model_version(id),
    antispoof_model_id INTEGER REFERENCES model_version(id),
    asr_model_id INTEGER REFERENCES model_version(id)
);

-- =====================================================
-- 17. AUDIT_LOG - Operational Audit Trail
-- =====================================================
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    metadata JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);
