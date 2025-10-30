-- Seed data for development and testing

-- Insert model versions
INSERT INTO model_version (kind, name, version) VALUES
('speaker', 'ecapa_tdnn', '1.0.0'),
('antispoof', 'rawnet2', '1.0.0'),
('asr', 'whisper_base', '1.0.0');

-- Insert demo client applications
INSERT INTO client_app (id, name, contact_email) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Demo Banking App', 'dev@demobank.com'),
('550e8400-e29b-41d4-a716-446655440002', 'Test Mobile App', 'dev@testapp.com');

-- Insert demo API keys (these are for development only!)
INSERT INTO api_key (id, client_id, key_hash, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440010', 
 '550e8400-e29b-41d4-a716-446655440001',
 'demo-bank-key-12345', -- In production, this would be a proper bcrypt hash
 now()),
('550e8400-e29b-41d4-a716-446655440011',
 '550e8400-e29b-41d4-a716-446655440002', 
 'demo-app-key-67890',  -- In production, this would be a proper bcrypt hash
 now());

-- Insert demo users
INSERT INTO "user" (id, external_ref, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440020', 'demo-user-001', now()),
('550e8400-e29b-41d4-a716-446655440021', 'demo-user-002', now());

-- Insert user policies
INSERT INTO user_policy (user_id, keep_audio, retention_days, consent_at) VALUES
('550e8400-e29b-41d4-a716-446655440020', false, 7, now()),
('550e8400-e29b-41d4-a716-446655440021', true, 30, now());

-- Note: Voiceprints and actual biometric data would be created through the API
-- during enrollment process, not inserted directly into the database