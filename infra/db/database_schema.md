# Base de datos — Voice Biometrics

## Visión general
PostgreSQL 16 (imagen `pgvector/pgvector:pg16`) con extensiones `pgcrypto` (cifrado
de embeddings/contraseñas) y `pg_trgm` (búsqueda por similitud de frases).
Esquema completo en `infra/db/init.sql` (baseline idempotente, fuente de verdad) + migraciones
`NNN_*.sql` aplicadas por `infra/db/apply_migrations.py` y registradas en `schema_migrations`.

## Inventario de archivos en `infra/`

### Scripts Python (`infra/db/*.py`)

| Archivo | Estado en git | Qué hace |
|---|---|---|
| `apply_migrations.py` | ✅ trackeado | **Runner de migraciones**: aplica `migrations/*.sql` pendientes en orden lexicográfico, cada una en su propia transacción, y las registra en `schema_migrations` con checksum SHA-256. Falla si una migración ya aplicada fue editada. Soporta `--dry-run` y `--dir`. Conexión vía `DATABASE_URL` o variables `DB_*`. Lo ejecuta el contenedor `api` al arrancar y el conftest de pytest en `voice_biometrics_test`. |

### Scripts del pipeline de frases (`infra/db/tools/`)

| Archivo | Estado en git | Qué hace |
|---|---|---|
| `extract_phrases.py` | ✅ trackeado | **Extracción PDF → TXT**: limpia el texto (artefactos PDF, OCR, correcciones), filtra por calidad (30-500 chars, ≥8 palabras, `phoneme_score >= 80`), balancea estilos (narrative:resto 1:1) y genera `frases_por_libro/<libro>.txt` con secciones `## EASY/MEDIUM/HARD` ordenadas por phoneme_score desc. **No pisa TXT existentes** (`--force` para regenerar); `--output-dir`, `--min-phoneme-score`. Requiere `PyMuPDF` (en requirements-dev). No toca la BD: solo PDFs en `Libros/`. |
| `register_books.py` | ✅ trackeado | **Registro de libros en BD** (para usuarios externos sin los seeds): upsert idempotente de cada `Libros/*.pdf` en `books` (`ON CONFLICT (filename) DO NOTHING`; `--update` para refrescar título). `--dry-run` disponible. |
| `import_phrases_from_txt.py` | ✅ trackeado | **Importación TXT → BD**: parsea `N. [score\|style] frase`, persiste `phoneme_score` y `style`, y vincula `phrase.book_id` resolviendo el nombre del TXT contra `books.filename` (auto-crea el libro si falta; `--no-create-books` para exigir registro previo). Mantiene `--dry-run` y `--no-clear`. |
| `assign_books_to_phrases.py` | ✅ trackeado | **One-off histórico (2025)**: asigna `book_id` y `source` a las frases existentes que quedaron sin libro, distribuyéndolas uniformemente entre los `books` (solución temporal porque se perdió el mapping original de extracción). |

### Archivos SQL

| Archivo | Estado en git | Qué hace |
|---|---|---|
| `init.sql` | ✅ trackeado | **Baseline completo e idempotente** (fuente de verdad): extensiones `pgcrypto` + `pg_trgm`, las 20 tablas, enum `auth_reason`, vista `v_attempt_metrics`, 3 funciones + 2 triggers, índices y seeds de referencia (36 libros, 10 reglas de calidad, `system_settings`, usuarios dev). Corre vía `docker-entrypoint-initdb.d` en volúmenes nuevos y en el conftest de tests. |
| `migrations/001_add_auth_attempt_indexes.sql` | ✅ trackeado | **Migración activa**: índices `idx_auth_attempt_challenge` y `idx_auth_attempt_client` (ver §índices; ya replicados en `init.sql` para BDs nuevas). |
| `migrations/README.md` | ✅ trackeado | Convenciones del runner: numeración `NNN_*`, forward-only, idempotencia, checksum. |
| `data_dump.sql` | ❌ gitignored (PII) | `pg_dump` del entorno real: 37.407 frases + usuarios + datos de runtime. Restaurar tras crear el esquema (ver §Restauración). |
| `Libros/*.pdf` | ❌ gitignored (copyright) | Libros fuente de las frases (provistos por el usuario; no están en el repo). |
| `frases_por_libro/*.txt` | ❌ gitignored | Extracciones de frases por libro (intermedio entre `extract_to_txt.py` e `import_phrases_from_txt.py`). |

### Flujo de población de frases (usuario externo)

```
1. Coloque sus libros .pdf en Libros/                          (carpeta propia, gitignored)
2. (Opcional) python tools/register_books.py ───────────────▶ books        (upsert idempotente)
3. python tools/extract_phrases.py ─────────────────────────▶ frases_por_libro/*.txt
4. Revise/ordene los TXT (## EASY/MEDIUM/HARD, "N. [score|style] frase")
5. python tools/import_phrases_from_txt.py ─────────────────▶ phrase (score/style/book_id)
   (auto-crea libros faltantes; --no-create-books para exigir el paso 2)
```

Los **datos de runtime** (frases reales, usuarios) NO vienen de estos scripts: se restauran desde
`data_dump.sql`. Los scripts solo se usan para re-extraer/regenerar frases desde los libros.

## Estructura
20 tablas + vista `v_attempt_metrics` + enum `auth_reason` + 3 funciones + 2 triggers.

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
