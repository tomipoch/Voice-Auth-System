# Voice Biometrics API - Backend

Sistema de autenticación biométrica por voz con FastAPI y PostgreSQL.

## 🚀 Inicio Rápido

### 1. Iniciar Servicios
```bash
# Iniciar Docker y base de datos
docker-compose up -d

# Iniciar servidor de desarrollo
./start_server.sh
```

### 2. Probar la API
```bash
# Health check
curl http://localhost:8000/health

# Ver documentación interactiva
open http://localhost:8000/docs

# Ver documentación completa con ejemplos
open Backend/API_DOCUMENTATION.md
```

## 📁 Estructura del Proyecto

```
Backend/
├── src/
│   ├── api/              # Endpoints REST
│   ├── application/      # Lógica de aplicación
│   ├── domain/          # Modelos y reglas de negocio
│   ├── infrastructure/  # Persistencia y adaptadores
│   └── shared/          # Utilidades compartidas
├── scripts/             # Scripts de utilidad
├── tests/              # Pruebas
└── docker-compose.yml  # Configuración de servicios
```

## 🔧 Configuración

### Variables de Entorno (`.env`)
```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=voice_password

# Desarrollo
DEVELOPMENT_MODE=true
SKIP_AUTH=true
```

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/login` - Login con JWT
- `POST /api/auth/register` - Registro de usuario

### Frases
- `GET /api/phrases/random` - Obtener frases aleatorias
- `GET /api/phrases/stats` - Estadísticas de frases
- `GET /api/phrases/list` - Listar frases

### Administración
- `GET /api/admin/stats` - Estadísticas del sistema
- `GET /api/admin/users` - Listar usuarios

### Health
- `GET /health` - Estado del servidor

## 🐳 Docker

### Servicios Disponibles
- **PostgreSQL**: Puerto 5432
- **PgAdmin**: Puerto 5050 (admin@example.com / admin)

### Comandos Útiles
```bash
# Ver logs
docker-compose logs -f

# Reiniciar servicio
docker-compose restart voice_biometrics_db

# Limpiar todo
docker-compose down -v
```

## 🗃️ Base de Datos

### Inicializar
```bash
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < ../Database/init.sql
```

### Cargar Frases
```bash
source venv/bin/activate
python scripts/extract_phrases.py
```

## 🧪 Testing

### Postman
Importar colecciones en Postman:
- `Voice_Biometrics_API.postman_collection.json`
- `Voice_Biometrics_Local.postman_environment.json`

### Usuarios de Prueba
- **SuperAdmin**: superadmin@voicebio.com / SuperAdmin2024!
- **Admin**: admin@empresa.com / AdminEmpresa2024!
- **User**: user@empresa.com / User2024!

## 📚 Documentación

- **Documentación Completa de la API**: Ver `API_DOCUMENTATION.md`
- **Comandos Útiles**: Ver `../COMMANDS_CHEATSHEET.md` 
- **Documentación Interactiva**: http://localhost:8000/docs

## 🛠️ Desarrollo

### Instalar Dependencias
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ejecutar Tests
```bash
pytest tests/
```

### Linting
```bash
pip install -r requirements-dev.txt
black src/
flake8 src/
```
