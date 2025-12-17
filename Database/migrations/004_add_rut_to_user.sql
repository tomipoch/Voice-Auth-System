-- Migration: Add RUT column to user table
-- Date: 2025-12-16
-- Description: Adds RUT (Chilean national ID) column to user table for Chilean users

-- Add RUT column (nullable, max 12 characters for format XX.XXX.XXX-X)
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS rut VARCHAR(12) NULL;

-- Optional: Add comment to column
COMMENT ON COLUMN "user".rut IS 'Chilean RUT (Rol Único Tributario) - Format: XXXXXXXX-X or XX.XXX.XXX-X';

-- Optional: Create index for RUT lookups (if needed in the future)
-- CREATE INDEX IF NOT EXISTS idx_user_rut ON "user"(rut) WHERE rut IS NOT NULL;
