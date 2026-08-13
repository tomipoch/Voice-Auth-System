# Base de datos — Voice Biometrics

## Visión general
PostgreSQL 16 (imagen `pgvector/pgvector:pg16`) con extensiones `pgcrypto` (cifrado
de embeddings/contraseñas) y `pg_trgm` (búsqueda por similitud de frases).
Esquema completo en `infra/db/init.sql` (baseline idempotente, fuente de verdad) + migraciones
`NNN_*.sql` aplicadas por `infra/db/apply_migrations.py` y registradas en `schema_migrations`.

## Estructura
21 tablas + vista `v_attempt_metrics` + enum `auth_reason` + 3 funciones/triggers.

| Tabla | Propósito | Estado |
|---|---|---|
| `"user"` | Usuario final (login, perfil, soft-delete, lockout) | Activa |
| `user_policy` | Retención de audio y consentimiento por usuario | Activa |
| `voiceprint` | Firma biométrica activa (embedding cifrado, modelo speaker) | Activa |
| `voiceprint_history` | Histórico de voiceprints (trazabilidad de re-enrolamiento) | Activa |
| `enrollment_sample` | Muestras individuales del enrolamiento | Activa |
| `challenge` | Desafíos de frase dinámica (liveness) | Activa |
| `phrase` | Frases para enrolamiento/verificación (37.407 en datos reales) | Activa |
| `phrase_usage` | Frases ya usadas por usuario (evitar repetición) | Activa |
| `phrase_quality_rules` | Reglas configurables (umbrales/rate-limit/cleanup) | Activa |
| `books` | Metadatos de los libros fuente de las frases | Activa |
| `audit_log` | Bitácora operacional (ENROLL, VERIFY, LOGIN, ...) | Activa |
| `schema_migrations` | Control del runner de migraciones | Activa |
| `enrollment_session` | Sesiones de enrolamiento persistentes | Activa |
| `system_settings` | Configuración global (ej. grabación de dataset) | Activa |
| `client_app` | Clientes de la API (patrón middleware) | Activa |
| `api_key` | API keys con hash por cliente | Activa |
| `auth_attempt` | Decisión final de negocio de cada verificación | Activa |
| `scores` | Señales técnicas (similitud, spoof, ASR, latencia) | Activa |
| `audio_blob` | Audio crudo cifrado (evidencia forense) | Activa |
| `model_version` | Versiones de modelos ML usados en decisiones | Activa |
| `v_attempt_metrics` | Vista Riesgo/Fraude sobre auth_attempt+scores | Activa |

## Tablas inactivas conectadas (2026-08)

Tras esta conexión, las 8 tablas "inactivas" del baseline ya están cableadas al
backend. Resumen por tabla:

1. **`auth_attempt` + `scores` + `audio_blob`** — `VerificationService`
   (`apps/backend/src/application/verification_service.py`) persiste cada
   intento de los 3 flujos (single, multi, quick) con su razón (`auth_reason`),
   `policy_id` ('single'|'multi'|'quick'), `total_latency_ms` y los IDs de los
   modelos ML usados (`speaker_model_id`/`antispoof_model_id`/`asr_model_id`).
   Audio en `audio_blob` solo cuando `user_policy.keep_audio=true`. El historial
   `GET /api/verification/user/{id}/history` se sirve desde `auth_attempt` +
   `scores` con el MISMO shape que consumía el frontend (los intentos previos a
   esta conexión solo viven en `audit_log`). Repos:
   `VerificationAttemptRepositoryPort` (`src/domain/repositories/`) +
   `PostgresVerificationAttemptRepository` (asyncpg, `audio_blob` + `auth_attempt`
   + `scores` en una transacción).

2. **`model_version`** — `ModelManager` se registra en `model_version` durante
   el `lifespan` de la app (`main.py`); el `model_type='antispoofing'` interno
   se mapea al CHECK del enum `kind='antispoof'`. `VerificationService` resuelve
   `get_model_id(kind)` para etiquetar cada `auth_attempt`.

3. **`enrollment_session`** — `EnrollmentService` persiste cada `start_enrollment`,
   `add_enrollment_sample` y marca `mark_completed` al terminar. `get_session` es
   ahora `async` y la recupera desde el repo tras un reinicio. UNIQUE por
   `user_id` se gestiona con `SELECT FOR UPDATE` + `DELETE` + `INSERT` dentro de
   una transacción (no `ON CONFLICT`, porque la constraint es `DEFERRABLE`).
   Repos: `EnrollmentSessionRepositoryPort` +
   `PostgresEnrollmentSessionRepository`.

4. **`system_settings`** — `dataset_recording` flag (enabled/session_id/session_dir/
   started_at) vive aquí; `DatasetRecordingController` lo lee/escribe en start/
   stop/status. El `lifespan` restaura la sesión activa antes de aceptar requests.
   Repos: `SystemSettingsRepositoryPort` +
   `PostgresSystemSettingsRepository`.

5. **`client_app` + `api_key`** — clientes externos usan `X-API-Key` opcional
   (no rompe JWT). `api_key.key_hash` se calcula con SHA-256 de la key cruda
   (nunca se persiste la key). CRUD admin en `/api/admin/clients` (POST/GET,
   `/rotate`, DELETE) con `require_admin_user`. `VerificationService` recibe
   `client_id` opcional y lo persiste en `auth_attempt.client_id`. Repos:
   `ClientAppRepositoryPort` + `PostgresClientAppRepository`.

Migración nueva: `001_add_auth_attempt_indexes.sql` (índices
`idx_auth_attempt_challenge` y `idx_auth_attempt_client`, replicados en
`init.sql` para BDs nuevas).

## Índices y optimización
- `idx_phrase_text_trgm` (GIN trigram) — acelera `ILIKE '%..%'` del admin sobre 37k frases.
- `idx_phrase_filter` (parcial, `language, difficulty WHERE is_active`) — filtros de `find_random`.
- `idx_audit_metadata_gin` (GIN JSONB) — búsquedas `metadata->>'user_id'` del historial.
- `idx_audit_entity` (`entity_type, entity_id, timestamp DESC`) — consultas de logs por entidad.
- Redundantes eliminados: `idx_user_email`, `idx_books_filename`, `idx_voiceprint_user`
  (duplican UNIQUEs), `idx_audit_time` (unificado en `idx_audit_timestamp`),
  `idx_phrase_active`, `idx_phrase_difficulty` (reemplazados por el índice parcial
  sobre idioma+dificultad+activo).

## Flujo de migraciones
1. `init.sql` = baseline completo e idempotente (esquema + seeds de referencia).
2. Cambios nuevos: `infra/db/migrations/NNN_descripcion.sql` (numeración única).
3. `python infra/db/apply_migrations.py` aplica pendientes en orden, en transacción,
   y las registra en `schema_migrations` con checksum SHA-256.
4. Editar una migración aplicada falla (checksum); nunca se edita: se agrega otra.
5. El contenedor `api` ejecuta el runner al arrancar; el conftest de pytest lo aplica
   en `voice_biometrics_test`.

## Restauración de datos
`infra/db/data_dump.sql` (gitignored — contiene PII): 37.407 frases, usuarios,
audit_log, voiceprints, etc. Restaurar después de crear el esquema:

    docker compose exec -T postgres psql -U voice_user -d voice_biometrics < infra/db/data_dump.sql

Los libros (`infra/db/Libros/*.pdf`) no están en el repo por derechos de autor.
