# Voice Biometrics API

Sistema de autenticación biométrica por voz con FastAPI y PostgreSQL.

## 🚀 Inicio Rápido

```bash
# 1. Crear entorno virtual
python3.11 -m venv venv && source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Iniciar servicios (PostgreSQL + pgAdmin)
docker-compose up -d

# 5. Iniciar servidor
./start_server.sh
```

## 📁 Estructura

```
Backend/
├── src/              # Código fuente (Clean Architecture)
│   ├── api/          # Endpoints REST
│   ├── application/  # Lógica de aplicación
│   ├── domain/       # Modelos y reglas de negocio
│   ├── infrastructure/  # Persistencia y adaptadores
│   └── shared/       # Utilidades compartidas
├── tests/            # Pruebas unitarias y de integración
├── scripts/          # Scripts de utilidad
├── models/           # Modelos ML (descarga automática)
└── docs/             # Documentación técnica
```

## 🔧 Configuración

Variables esenciales en `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=voice_password
DEVELOPMENT_MODE=true
```

## 📡 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servidor |
| POST | `/api/auth/login` | Login con JWT |
| POST | `/api/auth/register` | Registro de usuario |
| GET | `/api/phrases/random` | Obtener frases aleatorias |
| GET | `/api/admin/stats` | Estadísticas del sistema |

**Documentación interactiva**: http://localhost:8000/docs

## 🐳 Docker

```bash
docker-compose up -d      # Iniciar servicios
docker-compose logs -f    # Ver logs
docker-compose down -v    # Detener y limpiar
```

**Servicios**:
- PostgreSQL: `localhost:5432`
- pgAdmin: `localhost:5050` (admin@example.com / admin)

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest tests/ --cov=src

# Linting
black src/ && flake8 src/
```

## 📚 Documentación

Ver [docs/](docs/) para documentación técnica detallada. La
descripción técnica canónica (capas de Clean Architecture,
puertos del dominio, decisiones de infraestructura) vive en
[`docs/arquitectura/TECHNICAL_ARCHITECTURE.md`](../../docs/arquitectura/TECHNICAL_ARCHITECTURE.md) — ese es el documento de referencia para entender la estructura del backend. Esta README se enfoca en cómo arrancarlo.
