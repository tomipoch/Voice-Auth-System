-- =====================================================
-- Rollback Migration: Remove Phrase Quality Rules System
-- Description: Reverts changes from 001_add_phrase_quality_rules.sql
-- Date: 2024-12-01
-- =====================================================

-- 1. Drop trigger and function
DROP TRIGGER IF EXISTS trg_phrase_quality_rules_updated_at ON phrase_quality_rules;
DROP FUNCTION IF EXISTS update_phrase_quality_rules_updated_at();

-- 2. Revert phrase_usage constraint
ALTER TABLE phrase_usage 
DROP CONSTRAINT IF EXISTS phrase_usage_used_for_check;

ALTER TABLE phrase_usage
ADD CONSTRAINT phrase_usage_used_for_check 
CHECK (used_for IN ('enrollment', 'verification'));

-- 3. Remove phrase_id column from challenge
ALTER TABLE challenge 
DROP COLUMN IF EXISTS phrase_id;

-- 4. Drop phrase_quality_rules table
DROP TABLE IF EXISTS phrase_quality_rules CASCADE;

-- 5. Add audit log entry for rollback
INSERT INTO audit_log (actor, action, entity_type, entity_id, metadata, success)
VALUES (
    'system',
    'ROLLBACK',
    'phrase_quality_rules',
    'rollback_001',
    '{"migration": "rollback_001", "description": "Rolled back phrase quality rules system"}'::jsonb,
    TRUE
);

-- =====================================================
-- Verification (run these to verify rollback)
-- =====================================================

-- Verify table was dropped
-- SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'phrase_quality_rules';

-- Verify challenge column was removed
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'challenge' AND column_name = 'phrase_id';
