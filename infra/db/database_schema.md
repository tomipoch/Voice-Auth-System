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
| `enrollment_session` | Sesiones de enrolamiento persistentes | Inactiva (código usa memoria) |
| `system_settings` | Configuración global (ej. grabación de dataset) | Inactiva |
| `client_app` | Clientes de la API (patrón middleware) | Inactiva |
| `api_key` | API keys con hash por cliente | Inactiva |
| `auth_attempt` | Decisión final de negocio de cada verificación | Inactiva |
| `scores` | Señales técnicas (similitud, spoof, ASR, latencia) | Inactiva |
| `audio_blob` | Audio crudo cifrado (evidencia forense) | Inactiva |
| `model_version` | Versiones de modelos ML usados en decisiones | Inactiva |
| `v_attempt_metrics` | Vista Riesgo/Fraude sobre auth_attempt+scores | Inactiva |

## Análisis de tablas sin uso en el backend (decisión: conservar)

1. **`client_app` + `api_key`** — propósito original: el "Middleware Pattern" de la
   propuesta (clientes externos consumiendo la API biométrica con su propia key,
   auth + rate-limit por cliente). Hoy la API autentica con JWT de usuario y
   rate-limita global con slowapi; nunca se implementó el patrón por cliente.
   Recomendación: conservar (2 tablas pequeñas); si se necesita exposición
   multiusuario de la API, implementar el middleware que las use.

2. **`auth_attempt` + `scores`** — propósito: separar la decisión de negocio
   (aceptado/rechazado + motivo) de las señales técnicas crudas (similaridad,
   spoof_prob, phrase_match, latencia) para peritaje antifraude (área Riesgo y
   Fraude). Hoy el historial de verificaciones se reconstruye parseando
   `audit_log.metadata` (`VerificationService.get_verification_history`).
   Recomendación: es el candidato más valioso a conectar a futuro — persistir aquí
   cada verificación daría historial estructurado y consultable sin parseo.

3. **`audio_blob`** — propósito: evidencia de audio cifrado en reposo con retención
   configurable (`user_policy.keep_audio`/`retention_days`) y purga
   (`purge_expired_data()`). Hoy el audio se guarda en disco bajo
   `evaluation/dataset/` cuando la grabación de dataset está activa (respetando
   `keep_audio`). Recomendación: conservar; alternativa futura: blob storage con
   referencia en `auth_attempt`.

4. **`model_version`** — propósito: trazabilidad forense de qué versión de cada
   modelo (speaker/antispoof/asr) tomó cada decisión. `voiceprint.speaker_model_id`
   existe (y se corrigió su persistencia) pero nadie registra versiones de modelos.
   Recomendación: conservar; tarea futura: registrar los modelos reales al arrancar
   (`model_manager.py`) para que los nuevos voiceprints queden etiquetados.

5. **Columnas/tablas huérfanas** — `phrase.phoneme_score`, `phrase.style`
   (clasificación fonémica/estilística para análisis de calidad), `enrollment_session`
   (persistir sesiones de enrolamiento entre reinicios) y `system_settings`
   (flag de grabación de dataset vía superadmin). Ninguna es leída por el código
   hoy. Se conservan por decisión del proyecto.

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
