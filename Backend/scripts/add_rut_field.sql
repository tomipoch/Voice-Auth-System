-- Add RUT field to user table
-- RUT (Rol Único Tributario) is the Chilean national ID

ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS rut VARCHAR(12) UNIQUE;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_rut ON "user"(rut);

-- Add comment
COMMENT ON COLUMN "user".rut IS 'Chilean national ID (RUT) in format XX.XXX.XXX-Y';

-- Add first_name and last_name columns if they don't exist
ALTER TABLE "user"
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT;

-- Migrate existing name data to first_name/last_name
UPDATE "user"
SET 
  first_name = SPLIT_PART(name, ' ', 1),
  last_name = SUBSTRING(name FROM POSITION(' ' IN name) + 1)
WHERE first_name IS NULL AND name IS NOT NULL AND name != '';

-- Add settings column as JSONB if it doesn't exist
ALTER TABLE "user"
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;
