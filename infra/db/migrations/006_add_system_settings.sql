-- Migration: Add system_settings table for storing global configuration
-- This allows superadmin to control features like dataset recording

CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(255)
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_system_settings_updated ON system_settings(updated_at DESC);

-- Insert default values
INSERT INTO system_settings (key, value) VALUES 
    ('dataset_recording', '{"enabled": false}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Comment
COMMENT ON TABLE system_settings IS 'Global system settings controlled by superadmin';
