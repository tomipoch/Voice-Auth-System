-- Migration 001: Índices de soporte para auth_attempt (historial conectado)
-- Usados por el historial por usuario (idx_auth_user_time ya existe), por
-- búsquedas por challenge y por el filtrado por cliente de la API.

CREATE INDEX IF NOT EXISTS idx_auth_attempt_challenge ON auth_attempt(challenge_id);
CREATE INDEX IF NOT EXISTS idx_auth_attempt_client ON auth_attempt(client_id);
