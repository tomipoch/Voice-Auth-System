-- =====================================================
-- Migration: Add Phrase Quality Rules System
-- Description: Adds configurable rules for phrase quality
--              analysis and challenge management
-- Date: 2024-12-01
-- =====================================================

-- 1. Create phrase_quality_rules table
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

-- Index for active rules lookup
CREATE INDEX idx_phrase_quality_rules_active ON phrase_quality_rules(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_phrase_quality_rules_type ON phrase_quality_rules(rule_type);

-- 2. Insert default rules
INSERT INTO phrase_quality_rules (rule_name, rule_type, rule_value) VALUES
-- Threshold rules (for phrase quality analysis)
('min_success_rate', 'threshold', '{"value": 0.70, "description": "Tasa mínima de éxito para mantener frase activa", "unit": "percentage"}'),
('min_asr_score', 'threshold', '{"value": 0.80, "description": "Score mínimo de ASR (reconocimiento de voz)", "unit": "percentage"}'),
('min_phrase_ok_rate', 'threshold', '{"value": 0.75, "description": "Tasa mínima de transcripción correcta", "unit": "percentage"}'),
('min_attempts_for_analysis', 'threshold', '{"value": 10, "description": "Intentos mínimos antes de analizar frase", "unit": "count"}'),
('exclude_recent_phrases', 'threshold', '{"value": 50, "description": "Excluir últimas N frases usadas por usuario", "unit": "count"}'),

-- Rate limit rules (for challenge creation)
('max_challenges_per_user', 'rate_limit', '{"value": 3, "description": "Máximo de challenges activos simultáneos por usuario", "unit": "count"}'),
('max_challenges_per_hour', 'rate_limit', '{"value": 20, "description": "Máximo de challenges creados por hora por usuario", "unit": "count"}'),

-- Cleanup rules (for maintenance)
('challenge_expiry_minutes', 'cleanup', '{"value": 5, "description": "Minutos hasta que un challenge expire", "unit": "minutes"}'),
('cleanup_expired_after_hours', 'cleanup', '{"value": 1, "description": "Borrar challenges expirados después de N horas", "unit": "hours"}'),
('cleanup_used_after_hours', 'cleanup', '{"value": 24, "description": "Borrar challenges usados después de N horas", "unit": "hours"}');

-- 3. Add phrase_id column to challenge table
ALTER TABLE challenge 
ADD COLUMN IF NOT EXISTS phrase_id UUID REFERENCES phrase(id) ON DELETE SET NULL;

-- Index for phrase lookup in challenges
CREATE INDEX IF NOT EXISTS idx_challenge_phrase ON challenge(phrase_id);

-- 4. Update phrase_usage constraint to support 'challenge' type
ALTER TABLE phrase_usage 
DROP CONSTRAINT IF EXISTS phrase_usage_used_for_check;

ALTER TABLE phrase_usage
ADD CONSTRAINT phrase_usage_used_for_check 
CHECK (used_for IN ('enrollment', 'verification', 'challenge'));

-- 5. Create trigger to update updated_at timestamp
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

-- 6. Add audit log entry for this migration
INSERT INTO audit_log (actor, action, entity_type, entity_id, metadata, success)
VALUES (
    'system',
    'MIGRATION',
    'phrase_quality_rules',
    'migration_001',
    '{"migration": "001_add_phrase_quality_rules", "description": "Added phrase quality rules system"}'::jsonb,
    TRUE
);

-- =====================================================
-- Verification queries (run these to verify migration)
-- =====================================================

-- Check that table was created
-- SELECT COUNT(*) FROM phrase_quality_rules;

-- Check that default rules were inserted
-- SELECT rule_name, rule_type, rule_value->>'value' as value, rule_value->>'description' as description
-- FROM phrase_quality_rules
-- ORDER BY rule_type, rule_name;

-- Check that challenge table was modified
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'challenge' AND column_name = 'phrase_id';

-- Check that phrase_usage constraint was updated
-- SELECT conname, pg_get_constraintdef(oid) 
-- FROM pg_constraint 
-- WHERE conname = 'phrase_usage_used_for_check';
