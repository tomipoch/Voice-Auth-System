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

| Email | Password | Rol |
|-------|----------|-----|
| superadmin@voicebio.com | SuperAdmin2024! | SuperAdmin |
| admin@empresa.com | AdminEmpresa2024! | Admin |
| user@empresa.com | User2024! | User |

## 🛠️ Tecnologías

- **Backend**: FastAPI, PostgreSQL 16 (pgvector), Docker
- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **ML**: SpeechBrain (ECAPA-TDNN), Anti-spoofing (AASIST + RawNet2)
- **Demo Bank**: Hono + better-sqlite3

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
