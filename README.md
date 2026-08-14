# VoiceAuth - Voice Biometrics Authentication System

Sistema de autenticación biométrica por voz desarrollado como proyecto de tesis.

> **Licencia:** [MIT](LICENSE) — Copyright (c) 2026 Tomás Poblete Chamorro.

## 🚀 Inicio Rápido

### Backend
```bash
cd apps/backend
docker-compose up -d      # Iniciar PostgreSQL + pgAdmin
./start_server.sh         # Iniciar servidor
```
**API**: http://localhost:8000 | **Docs**: http://localhost:8000/docs

### Frontend
```bash
cd apps/frontend
bun install && bun dev
```
**App**: http://localhost:5173

### Base de Datos
```bash
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < infra/db/init.sql
```

## 📁 Estructura

```
Voice-Auth-System/
├── apps/
│   ├── backend/         # API FastAPI + PostgreSQL (+ Dockerfile)
│   ├── frontend/        # UI React + Vite + Tailwind
│   └── demo-bank/       # Demo "Banco Pirulete" (integración con el API)
├── infra/
│   ├── db/              # Schema SQL + migraciones + herramientas de libros
│   └── evaluation/      # Dataset de evaluación (PII, gitignored)
├── docs/
│   ├── arquitectura/    # Arquitectura, ML, backend, DB, frontend
│   ├── manuales/        # Guías de usuario y admin
│   ├── informe/         # Informe de tesis + interpretación de gráficos
│   ├── API_ENDPOINTS_DOCUMENTATION.md
│   └── ANEXOS/          # Anexos de tesis
├── docker-compose.yml   # Stack completo (PostgreSQL + API + pgAdmin)
├── .env.example         # Variables de entorno (raíz)
└── LICENSE              # MIT
```

## 🔑 Usuarios de Prueba

> Los hashes bcrypt viven en [`apps/backend/scripts/create_admin_users.sql`](apps/backend/scripts/create_admin_users.sql);
> las contraseñas legibles se documentan en
> [`apps/backend/README.md`](apps/backend/README.md) y
> [`docs/arquitectura/SETUP.md`](docs/arquitectura/SETUP.md). No se commitean en el repo.

| Email | Rol | Empresa |
|-------|-----|---------|
| `admin@familia.com` | admin | familia |
| `superadmin@sistema.com` | superadmin | sistema |

## 📚 Base de datos de libros (necesaria)

El sistema necesita libros de dominio público en `infra/db/Libros/`
(no commiteados por derechos de autor). Para un usuario externo sin la
BD de libros, el pipeline completo está trackeado en `infra/db/tools/`:

1. Coloque sus libros `.pdf` en `infra/db/Libros/`.
2. (Opcional) Registre los libros en la tabla `books`:

       python infra/db/tools/register_books.py            # upsert idempotente

3. Extraiga las frases — genera un TXT por libro en
   `infra/db/frases_por_libro/`, agrupado por dificultad
   (`## EASY/MEDIUM/HARD`) y ordenado por score fonémico desc.
   No reemplaza TXT existentes (`--force` para regenerar):

       python infra/db/tools/extract_phrases.py            # requiere PyMuPDF (requirements-dev)

4. Revise y corrija los TXT (formato `N. [score|style] frase`).
5. Importe las frases a la base de datos (persiste score/style y
   vincula `book_id`; auto-crea libros faltantes):

       python infra/db/tools/import_phrases_from_txt.py    # [--dry-run] [--no-clear]

Alternativa: para restaurar las 37.407 frases pre-generadas use el
dump local `infra/db/data_dump.sql` (gitignored por PII — contiene
RUTs). No está en el repo; manténgalo sólo en una copia local fuera
de Git.

## 🛠️ Tecnologías

- **Backend**: FastAPI, PostgreSQL 16 (pgvector), Docker
- **Frontend**: React 19, TypeScript, Tailwind CSS (con `rolldown-vite` como bundler)
- **ML**: SpeechBrain (ECAPA-TDNN), Anti-spoofing (AASIST + RawNet2)
- **Demo Bank**: Hono + better-sqlite3
- **Bundler**: `rolldown-vite` (alias npm sobre `vite` declarado en `apps/frontend/package.json` `overrides`)

## 📚 Documentación

- [Backend README](apps/backend/README.md)
- [Frontend README](apps/frontend/README.md)
- [Arquitectura](docs/arquitectura/)
- [Manuales](docs/manuales/)
- [Informe de tesis](docs/informe/)
- [Anexos](docs/ANEXOS/)
- [API endpoints](docs/API_ENDPOINTS_DOCUMENTATION.md)

---
**Proyecto de Tesis** — Universidad
