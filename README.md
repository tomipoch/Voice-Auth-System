# 🎙️ Voice Biometrics Authentication System

Sistema completo de autenticación biométrica por voz con backend FastAPI y frontend Angular.

## 📋 Documentación del Proyecto

### 🚀 Inicio Rápido
- **[Comandos Útiles](COMMANDS_CHEATSHEET.md)** - Todos los comandos necesarios en un solo lugar
- **[Backend README](Backend/README.md)** - Guía de inicio rápido del backend
- **[Frontend README](App/README.md)** - Guía de inicio rápido del frontend

### 📚 Documentación Técnica
- **[API Documentation](Backend/API_DOCUMENTATION.md)** - Documentación completa de la API con ejemplos de uso
- **[Cleanup Log](CLEANUP_LOG.md)** - Registro de limpieza y optimizaciones del proyecto

## 🏗️ Estructura del Proyecto

```
Proyecto/
├── Backend/                # API FastAPI + PostgreSQL
│   ├── src/               # Código fuente
│   ├── scripts/           # Scripts de utilidad
│   ├── tests/             # Tests
│   ├── docker-compose.yml # Servicios Docker
│   └── README.md          # Documentación del backend
│
├── App/                   # Frontend Angular
│   ├── src/              # Código fuente
│   ├── public/           # Archivos estáticos
│   └── README.md         # Documentación del frontend
│
├── Database/             # Scripts SQL e init
│   ├── init.sql         # Schema de base de datos
│   └── Libros/          # PDFs para extracción de frases
│
└── Documentación/
    ├── API_DOCUMENTATION.md      # Docs de API
    ├── COMMANDS_CHEATSHEET.md    # Referencia de comandos
    └── CLEANUP_LOG.md            # Log de cambios
```

## ⚡ Inicio Rápido

### 1. Backend
```bash
cd Backend
docker-compose up -d
./start_server.sh
```

**URL**: http://localhost:8000  
**Docs**: http://localhost:8000/docs

### 2. Frontend
```bash
cd App
npm install
npm run dev
```

**URL**: http://localhost:5173

### 3. Servicios Docker
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **PgAdmin**: localhost:5050
- **Prometheus**: localhost:9091

## 🔑 Usuarios de Prueba

| Email | Password | Rol |
|-------|----------|-----|
| superadmin@voicebio.com | SuperAdmin2024! | SuperAdmin |
| admin@empresa.com | AdminEmpresa2024! | Admin |
| user@empresa.com | User2024! | User |

## 📡 Endpoints Principales

### Autenticación
- `POST /api/auth/login` - Login con JWT
- `POST /api/auth/register` - Registro de usuario

### Gestión de Frases
- `GET /api/phrases/random` - Obtener frases aleatorias
- `GET /api/phrases/stats` - Estadísticas de frases
- `GET /api/phrases/list` - Listar frases

### Administración
- `GET /api/admin/stats` - Estadísticas del sistema
- `GET /api/admin/users` - Listar usuarios

**Ver documentación completa**: [API_DOCUMENTATION.md](Backend/API_DOCUMENTATION.md)

## 🧪 Testing

### Postman
Importar colecciones incluidas:
- `Backend/Voice_Biometrics_API.postman_collection.json`
- `Backend/Voice_Biometrics_Local.postman_environment.json`

### Comandos Rápidos
```bash
# Health check del backend
curl http://localhost:8000/health

# Login y obtener token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@voicebio.com","password":"SuperAdmin2024!"}'

# Obtener frases aleatorias
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/random?count=3"
```

## 🗄️ Base de Datos

### Inicializar
```bash
cd Backend
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < ../Database/init.sql
```

### Cargar Frases (43,459 frases de 26 libros)
```bash
cd Backend
source venv/bin/activate
python scripts/extract_phrases.py
```

**Distribución de frases**:
- Fáciles (5-10 palabras): ~6,637
- Medias (11-20 palabras): ~25,063
- Difíciles (21-30 palabras): ~11,759

## 🛠️ Tecnologías

### Backend
- **FastAPI** - Framework web asíncrono
- **PostgreSQL 16+** - Base de datos con pgvector
- **Redis** - Cache y sesiones
- **Docker** - Contenedores
- **asyncpg** - Driver PostgreSQL asíncrono
- **JWT** - Autenticación con tokens

### Frontend
- **Angular 18+** - Framework frontend
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Estilos
- **Vite** - Build tool

## 📂 Características Principales

✅ Sistema de frases dinámicas (43,459 frases de libros clásicos)  
✅ Autenticación JWT con roles (SuperAdmin, Admin, User)  
✅ API RESTful documentada con ejemplos  
✅ Colección Postman lista para usar  
✅ Docker Compose para desarrollo  
✅ Base de datos PostgreSQL con extensiones  
✅ Sistema de caché con Redis  
✅ Monitoreo con Prometheus  
✅ Admin panel con PgAdmin  

## 🔄 Flujo de Trabajo Típico

### Desarrollo Diario
```bash
# 1. Iniciar servicios
cd Backend && docker-compose up -d

# 2. Verificar servicios
docker-compose ps

# 3. Iniciar backend
./start_server.sh

# 4. Iniciar frontend (en otra terminal)
cd ../App && npm run dev
```

### Reinicio Completo
```bash
# Limpiar todo
cd Backend
docker-compose down -v

# Recrear servicios
docker-compose up -d

# Reinicializar base de datos
cd ..
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < Database/init.sql

# Cargar frases
cd Backend && source venv/bin/activate
python scripts/extract_phrases.py
```

## 📖 Documentación Adicional

- **[Commands Cheatsheet](COMMANDS_CHEATSHEET.md)** - Referencia completa de todos los comandos
- **[API Documentation](Backend/API_DOCUMENTATION.md)** - Guía completa de la API con ejemplos
- **[Backend README](Backend/README.md)** - Documentación específica del backend
- **[Frontend README](App/README.md)** - Documentación específica del frontend
- **Swagger UI**: http://localhost:8000/docs (cuando el backend esté corriendo)

## 🐛 Troubleshooting

Ver sección de troubleshooting en [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md#-troubleshooting)

### Problemas Comunes

**Puerto ocupado**:
```bash
lsof -i :8000
kill -9 PID
```

**Docker no inicia**:
```bash
killall Docker && open -a Docker
```

**Base de datos no conecta**:
```bash
docker-compose logs voice_biometrics_db
docker-compose restart voice_biometrics_db
```

## 📞 Soporte

Para problemas o dudas:
1. Revisar [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)
2. Ver logs: `docker-compose logs -f`
3. Verificar servicios: `docker-compose ps`
4. Consultar [API_DOCUMENTATION.md](Backend/API_DOCUMENTATION.md)

## 📄 Licencia

Este proyecto es parte de un trabajo de tesis universitaria.

---

**Última actualización**: 20 de noviembre de 2025
