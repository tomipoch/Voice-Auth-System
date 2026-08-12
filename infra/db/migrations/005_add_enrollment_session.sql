-- Migration: Add enrollment_session table for persisting enrollment sessions
-- This ensures sessions survive server restarts

CREATE TABLE IF NOT EXISTS enrollment_session (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    challenges JSONB NOT NULL,  -- Array of challenge objects
    samples_collected INTEGER DEFAULT 0,
    challenge_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour'),
    completed_at TIMESTAMPTZ,
    CONSTRAINT enrollment_session_active_unique UNIQUE (user_id) DEFERRABLE INITIALLY DEFERRED
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_enrollment_session_user ON enrollment_session(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_session_expires ON enrollment_session(expires_at);

-- Comment
COMMENT ON TABLE enrollment_session IS 'Persistent storage for active enrollment sessions - survives server restarts';
