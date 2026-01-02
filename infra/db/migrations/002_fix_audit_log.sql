-- =====================================================
-- MIGRATION: Fix Audit Log Table Schema
-- =====================================================
-- This migration fixes column names and adds missing columns
-- to align audit_log table with repository code expectations

-- Rename columns to match code expectations
ALTER TABLE audit_log 
RENAME COLUMN at TO timestamp;

ALTER TABLE audit_log 
RENAME COLUMN entity TO entity_type;

ALTER TABLE audit_log 
RENAME COLUMN meta TO metadata;

-- Add missing columns
ALTER TABLE audit_log
ADD COLUMN IF NOT EXISTS success BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Create index for timestamp queries (performance)
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Verify the changes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'audit_log'
ORDER BY ordinal_position;
