-- =====================================================
-- MIGRATION: Add User Authentication and Profile Columns
-- =====================================================
-- This migration adds the necessary columns to the user table
-- to support email/password authentication and user profiles

-- Add authentication and profile columns
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS email TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS password TEXT,
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'superadmin')),
ADD COLUMN IF NOT EXISTS company TEXT,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Create index for email lookups (frequently used for login)
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email) WHERE email IS NOT NULL;

-- Create index for role-based queries
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);

-- Create index for company-based queries
CREATE INDEX IF NOT EXISTS idx_user_company ON "user"(company) WHERE company IS NOT NULL;

-- Update existing users to have default values if needed
-- (This is safe to run even if there are no existing users)
UPDATE "user" 
SET role = 'user' 
WHERE role IS NULL;

-- Insert a default admin user for testing (password: 'admin123')
-- Password hash is bcrypt hash of 'admin123'
INSERT INTO "user" (id, email, password, first_name, last_name, role, company, external_ref, created_at)
VALUES (
  gen_random_uuid(),
  'admin@example.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OKi', -- bcrypt hash of 'admin123'
  'Admin',
  'User',
  'admin',
  'Example Corp',
  'admin-001',
  now()
)
ON CONFLICT (email) DO NOTHING;

-- Insert a default regular user for testing (password: 'user123')
INSERT INTO "user" (id, email, password, first_name, last_name, role, company, external_ref, created_at)
VALUES (
  gen_random_uuid(),
  'user@example.com',
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- bcrypt hash of 'user123'
  'Test',
  'User',
  'user',
  'Example Corp',
  'user-001',
  now()
)
ON CONFLICT (email) DO NOTHING;

-- Create user policies for test users
INSERT INTO user_policy (user_id, keep_audio, retention_days, consent_at)
SELECT id, FALSE, 7, now()
FROM "user"
WHERE email IN ('admin@example.com', 'user@example.com')
ON CONFLICT (user_id) DO NOTHING;
