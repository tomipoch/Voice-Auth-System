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
│   ├── backend/         # API FastAPI + PostgreSQL
│   ├── frontend/        # UI React + Vite + Tailwind
│   └── demo-bank/       # Demo "Banco Pirulete" (integración con el API)
├── infra/
│   ├── db/              # Schema SQL + migraciones + datos de libros
│   ├── deployment/      # Dockerfile multi-stage del backend
│   └── evaluation/      # Dataset de evaluación (PII, gitignored)
├── docs/
│   ├── arquitectura/    # Arquitectura, ML, backend, DB, frontend
│   ├── manuales/        # Guías de usuario y admin
│   ├── informe/         # Informe de tesis + interpretación de gráficos
│   ├── API_ENDPOINTS_DOCUMENTATION.md
│   └── ANEXOS/          # Anexos de tesis
├── evaluation/          # Scripts y resultados de evaluación
├── docker-compose.yml   # (en apps/backend/)
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

El sistema necesita libros de dominio público en `Database/Libros/`
(no commiteados por derechos de autor). Pasos:

1. Coloque libros `.pdf` o `.txt` en `Database/Libros/`.
2. El script de extracción de frases (`scripts/extract_phrases.py`)
   **no está incluido en el repo**; se ejecuta dentro del contenedor
   de la API para producir las frases. Solo `assign_books_to_phrases.py`
   está commiteado.
3. La migración `003` siembra solo los metadatos en la tabla `books`
   (título, autor, idioma, total_frases); las frases en sí no se
   generan sin los libros.
4. Para restaurar las 37.407 frases pre-generadas use el dump
   local `Database/data_dump.sql` (gitignored por PII —

contiene RUTs). No está en el repo; manténgalo sólo en una copia
   local fuera de Git.

Si su instalación requiere el dump, regenérelas ejecutando
`scripts/extract_phrases.py` (omitido) contra los PDFs de su
proyecto local, o restaure el dump desde su backup personal.

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
