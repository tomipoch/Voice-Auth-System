-- Cleanup job for expired data
-- Run this periodically to maintain database performance and compliance

-- 1. Clean up expired challenges
DELETE FROM challenge 
WHERE (used_at IS NOT NULL OR expires_at < now())
  AND created_at < now() - interval '14 days';

-- 2. Clean up expired audio blobs based on user retention policies
DELETE FROM audio_blob ab
USING auth_attempt a, user_policy up
WHERE a.audio_id = ab.id
  AND a.user_id = up.user_id
  AND a.created_at < now() - (up.retention_days || ' days')::interval;

-- 3. Clean up old enrollment samples (keep only recent ones)
DELETE FROM enrollment_sample
WHERE created_at < now() - interval '90 days';

-- 4. Clean up old audit logs (keep 1 year)
DELETE FROM audit_log
WHERE at < now() - interval '1 year';

-- 5. Vacuum tables for performance
VACUUM ANALYZE challenge;
VACUUM ANALYZE audio_blob;
VACUUM ANALYZE enrollment_sample;
VACUUM ANALYZE audit_log;