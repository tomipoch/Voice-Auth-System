# 📋 Cheatsheet de Comandos - Voice Biometrics API

## 🐳 Docker

### Gestión de Contenedores
```bash
# Iniciar todos los servicios
cd Backend
docker-compose up -d

# Ver estado de contenedores
docker-compose ps
docker ps

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (limpieza completa)
docker-compose down -v

# Ver logs de un servicio específico
docker-compose logs -f voice_biometrics_db
docker-compose logs -f voice_biometrics_api

# Reiniciar un servicio
docker-compose restart voice_biometrics_db
```

### Base de Datos PostgreSQL
```bash
# Ejecutar script SQL en la base de datos
cd Proyecto  # Directorio raíz
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < Database/init.sql

# Conectarse a PostgreSQL desde terminal
docker exec -it voice_biometrics_db psql -U voice_user -d voice_biometrics

# Comandos dentro de psql
\dt              # Listar tablas
\d+ phrase       # Describir tabla phrase
\q               # Salir

# Ejecutar consulta SQL directa
docker exec voice_biometrics_db psql -U voice_user -d voice_biometrics -c "SELECT COUNT(*) FROM phrase;"
```

### Redis
```bash
# Conectarse a Redis CLI
docker exec -it voice_biometrics_redis redis-cli

# Comandos dentro de redis-cli
PING            # Verificar conexión
KEYS *          # Ver todas las llaves
GET key_name    # Obtener valor
EXIT            # Salir
```

### Limpieza y Mantenimiento
```bash
# Limpiar contenedores detenidos
docker container prune

# Limpiar imágenes sin usar
docker image prune

# Ver uso de disco de Docker
docker system df

# Limpieza completa (cuidado!)
docker system prune -a --volumes
```

## 🐍 Backend (FastAPI)

### Entorno Virtual
```bash
# Activar entorno virtual
cd Backend
source venv/bin/activate

# Desactivar
deactivate

# Crear nuevo entorno virtual (si es necesario)
python3 -m venv venv
```

### Dependencias
```bash
# Instalar dependencias
pip install -r requirements.txt

# Actualizar requirements.txt
pip freeze > requirements.txt

# Instalar dependencia específica
pip install nombre-paquete==version
```

### Servidor de Desarrollo
```bash
# Método 1: Script directo
cd Backend
./start_server.sh

# Método 2: Comando manual
cd Backend
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Método 3: Con variables de entorno explícitas
SKIP_AUTH=true DEVELOPMENT_MODE=true uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Servidor sin auto-reload (producción)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Scripts Útiles
```bash
# Extraer frases de PDFs
cd Backend
source venv/bin/activate
python scripts/extract_phrases.py

# Crear usuarios de prueba (si existe)
python scripts/create_users.py

# Ejecutar tests
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

### Variables de Entorno
```bash
# Ver variables actuales
cat Backend/.env

# Editar variables
nano Backend/.env
# o
code Backend/.env

# Variables importantes:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=voice_biometrics
# DB_USER=voice_user
# DB_PASSWORD=voice_password
# SKIP_AUTH=true
# DEVELOPMENT_MODE=true
```

## 🌐 API - Testing

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Login (obtener token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@voicebio.com","password":"SuperAdmin2024!"}'

# Obtener frases aleatorias (con token)
TOKEN="tu_token_aqui"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/random?count=3&difficulty=medium"

# Estadísticas de frases
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/phrases/stats

# Listar frases
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/list?limit=10&difficulty=easy"
```

### httpie (alternativa más legible)
```bash
# Instalar
pip install httpie

# Health check
http localhost:8000/health

# Login
http POST localhost:8000/api/auth/login \
  email=superadmin@voicebio.com \
  password=SuperAdmin2024!

# Obtener frases
http localhost:8000/api/phrases/random \
  Authorization:"Bearer $TOKEN" \
  count==3 difficulty==medium
```

## 📦 Postman

### Importar Colección
```bash
# Archivos a importar:
Backend/Voice_Biometrics_API.postman_collection.json
Backend/Voice_Biometrics_Local.postman_environment.json

# Pasos:
1. Abrir Postman
2. File → Import
3. Seleccionar ambos archivos
4. Seleccionar environment "Voice Biometrics - Local"
5. Ejecutar "Login - SuperAdmin" para obtener token
```

### Usuarios de Prueba
```
SuperAdmin:
- Email: superadmin@voicebio.com
- Password: SuperAdmin2024!

Admin:
- Email: admin@empresa.com
- Password: AdminEmpresa2024!

User:
- Email: user@empresa.com
- Password: User2024!
```

## 🔧 Utilidades del Sistema

### Procesos y Puertos
```bash
# Ver qué proceso usa un puerto
lsof -i :8000
lsof -i :5432

# Matar proceso por PID
kill -9 PID

# Matar proceso por nombre
pkill -f "uvicorn src.main:app"

# Ver todos los procesos Python
ps aux | grep python

# Ver procesos de Docker
ps aux | grep docker
```

### Logs y Debugging
```bash
# Ver logs del servidor (si se redirigió)
tail -f /tmp/uvicorn.log

# Ver logs en tiempo real con grep
tail -f logs/app.log | grep ERROR

# Limpiar logs
> logs/app.log
```

### Git
```bash
# Ver estado
git status

# Agregar cambios
git add .
git add archivo_especifico.py

# Commit
git commit -m "Descripción del cambio"

# Ver historial
git log --oneline

# Ver cambios no commiteados
git diff

# Descartar cambios
git checkout -- archivo.py
git restore archivo.py
```

## 📊 Base de Datos - Queries Útiles

### Conectado a PostgreSQL
```sql
-- Contar frases por dificultad
SELECT difficulty, COUNT(*) 
FROM phrase 
WHERE is_active = true 
GROUP BY difficulty;

-- Ver frases más recientes
SELECT text, difficulty, source, created_at 
FROM phrase 
ORDER BY created_at DESC 
LIMIT 10;

-- Buscar frases por texto
SELECT id, text, difficulty 
FROM phrase 
WHERE text ILIKE '%buscar%' 
LIMIT 10;

-- Ver uso de frases por usuario
SELECT p.text, pu.used_for, pu.used_at 
FROM phrase_usage pu
JOIN phrase p ON pu.phrase_id = p.id
WHERE pu.user_id = 'uuid-del-usuario'
ORDER BY pu.used_at DESC;

-- Frases más usadas
SELECT p.text, COUNT(*) as usage_count
FROM phrase_usage pu
JOIN phrase p ON pu.phrase_id = p.id
GROUP BY p.id, p.text
ORDER BY usage_count DESC
LIMIT 10;

-- Limpiar tabla
TRUNCATE TABLE phrase_usage CASCADE;
DELETE FROM phrase WHERE source = 'nombre-libro';
```

## 🚀 Flujo de Trabajo Típico

### Inicio del Día
```bash
# 1. Abrir Docker Desktop (si no está corriendo)
open -a Docker

# 2. Levantar servicios
cd Backend
docker-compose up -d

# 3. Verificar que todo esté corriendo
docker-compose ps

# 4. Iniciar servidor de desarrollo
./start_server.sh
# o en otra terminal:
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Reinicio Completo (Limpieza)
```bash
# 1. Detener todo
docker-compose down -v
pkill -f "uvicorn"

# 2. Recrear base de datos
docker-compose up -d
sleep 10  # Esperar a que PostgreSQL inicie

# 3. Ejecutar scripts de inicialización
cd ..  # Ir a directorio raíz del proyecto
docker exec -i voice_biometrics_db psql -U voice_user -d voice_biometrics < Database/init.sql

# 4. Cargar frases
cd Backend
source venv/bin/activate
python scripts/extract_phrases.py

# 5. Iniciar servidor
./start_server.sh
```

### Testing Rápido
```bash
# Verificar salud del sistema
curl http://localhost:8000/health

# Ver estadísticas de frases
curl http://localhost:8000/api/phrases/stats

# Obtener 3 frases fáciles
curl "http://localhost:8000/api/phrases/random?count=3&difficulty=easy"
```

## 🐛 Troubleshooting

### Puerto ocupado
```bash
lsof -i :8000
kill -9 PID_DEL_PROCESO
```

### Docker no inicia
```bash
# Reiniciar Docker Desktop
killall Docker && open -a Docker

# Esperar 10 segundos y verificar
docker ps
```

### Base de datos no conecta
```bash
# Verificar que el contenedor esté corriendo
docker ps | grep postgres

# Ver logs
docker-compose logs voice_biometrics_db

# Reiniciar contenedor
docker-compose restart voice_biometrics_db
```

### Servidor no recarga cambios
```bash
# Matar proceso y reiniciar
pkill -f "uvicorn"
cd Backend
./start_server.sh
```

### Problemas con dependencias
```bash
# Reinstalar dependencias
cd Backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📝 Notas Importantes

- **Puerto 8000**: Servidor FastAPI
- **Puerto 5432**: PostgreSQL
- **Puerto 6379**: Redis
- **Puerto 5050**: PgAdmin (admin@example.com / admin)
- **Puerto 9091**: Prometheus

- Siempre activar el entorno virtual antes de ejecutar scripts Python
- Docker debe estar corriendo antes de `docker-compose up`
- El servidor auto-recarga con `--reload` al detectar cambios
- Las variables de entorno se cargan desde `Backend/.env`
