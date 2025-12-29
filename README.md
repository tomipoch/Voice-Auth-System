# VoiceAuth - Voice Biometrics Authentication System

Sistema de autenticación biométrica por voz desarrollado como proyecto de tesis.

## 🚀 Inicio Rápido

### Backend
```bash
cd Backend
docker-compose up -d      # Iniciar PostgreSQL + pgAdmin
./start_server.sh         # Iniciar servidor
```
**API**: http://localhost:8000 | **Docs**: http://localhost:8000/docs

### Frontend
```bash
cd App
bun install && bun dev
```
**App**: http://localhost:5173

### Base de Datos
```bash
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < Database/init.sql
```

## 📁 Estructura

```
Proyecto/
├── App/           # Frontend React + Vite + Tailwind
├── Backend/       # API FastAPI + PostgreSQL
├── Database/      # Schema SQL + migraciones
├── evaluation/    # Evaluación biométrica del sistema
└── docs/          # Documentación técnica
    ├── backend/   # Arquitectura y API
    ├── frontend/  # Documentación UI
    ├── database/  # Schema y modelos
    └── ANEXOS/    # Anexos de tesis
```

## 🔑 Usuarios de Prueba

| Email | Password | Rol |
|-------|----------|-----|
| superadmin@voicebio.com | SuperAdmin2024! | SuperAdmin |
| admin@empresa.com | AdminEmpresa2024! | Admin |
| user@empresa.com | User2024! | User |

## 🛠️ Tecnologías

- **Backend**: FastAPI, PostgreSQL 16, Redis, Docker
- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **ML**: SpeechBrain (ECAPA-TDNN, Wav2Vec2), Anti-spoofing ensemble

## 📚 Documentación

- [Backend README](Backend/README.md)
- [Frontend README](App/README.md)
- [Documentación técnica](docs/)

---
**Proyecto de Tesis** - Universidad
