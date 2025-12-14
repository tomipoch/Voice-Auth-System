# Guía de Deployment - Sistema de Biometría por Voz

## Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Deployment Local (Desarrollo)](#deployment-local-desarrollo)
3. [Deployment con Docker](#deployment-con-docker)
4. [Deployment en Producción](#deployment-en-producción)
5. [Configuración de Base de Datos](#configuración-de-base-de-datos)
6. [Modelos de Machine Learning](#modelos-de-machine-learning)
7. [Variables de Entorno](#variables-de-entorno)
8. [Monitoreo y Logs](#monitoreo-y-logs)
9. [Troubleshooting](#troubleshooting)
10. [CI/CD](#cicd)

---

## Requisitos del Sistema

### Hardware Mínimo

**Desarrollo**:
- CPU: 4 cores
- RAM: 8 GB
- Disco: 20 GB libres
- GPU: Opcional (mejora rendimiento de ML)

**Producción**:
- CPU: 8+ cores
- RAM: 16+ GB
- Disco: 50+ GB libres
- GPU: Recomendado para mejor rendimiento

### Software

- **Python**: 3.11+
- **PostgreSQL**: 16+ con extensión pgvector
- **Redis**: 7+ (opcional, para rate limiting)
- **Docker**: 24+ (para deployment containerizado)
- **Docker Compose**: 2.20+
- **FFmpeg**: Para procesamiento de audio
- **Git**: Para control de versiones

---

## Deployment Local (Desarrollo)

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd Proyecto/Backend
```

### 2. Configurar Entorno Virtual

```bash
# Crear virtual environment
python3.11 -m venv venv

# Activar
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Actualizar pip
pip install --upgrade pip
```

### 3. Instalar Dependencias

```bash
# Dependencias de producción
pip install -r requirements.txt

# Dependencias de desarrollo (opcional)
pip install -r requirements-dev.txt
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
nano .env
```

Variables esenciales:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=your_secure_password

# API
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your_secret_key_here

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Configurar Base de Datos

```bash
# Crear base de datos
createdb voice_biometrics

# Ejecutar script de inicialización
psql voice_biometrics < ../Database/init.sql

# Verificar extensión pgvector
psql voice_biometrics -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 6. Descargar Modelos ML

Los modelos se descargan automáticamente al iniciar el servidor por primera vez. Se guardan en:
```
Backend/models/
├── speaker-recognition/
│   └── ecapa_tdnn/
├── text-verification/
│   └── lightweight_asr/
└── anti-spoofing/
    ├── aasist/
    ├── rawnet2/
    └── nes2net/
```

### 7. Iniciar Servidor

```bash
# Opción 1: Script de inicio
./start_server.sh

# Opción 2: Directamente con Python
python -m src.main

# Opción 3: Con uvicorn (desarrollo)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Verificar Instalación

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## Deployment con Docker

### 1. Estructura de Docker

El proyecto incluye:
- `Dockerfile`: Multi-stage build para optimizar tamaño
- `docker-compose.yml`: Orquestación de servicios

**Servicios incluidos**:
- `postgres`: PostgreSQL 16 con pgvector
- `api`: FastAPI application
- `pgadmin`: Interfaz web para DB (opcional)

### 2. Build de Imagen

```bash
# Build de imagen
docker build -t voice-biometrics-api:latest .

# Verificar imagen
docker images | grep voice-biometrics
```

### 3. Deployment con Docker Compose

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ver estado
docker-compose ps

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

### 4. Configuración de Volúmenes

Los volúmenes persistentes incluyen:
```yaml
volumes:
  postgres_data:     # Datos de PostgreSQL
  pgadmin_data:      # Configuración de pgAdmin
```

Volúmenes montados:
```yaml
- ./models:/app/models      # Modelos ML
- ./logs:/app/logs          # Logs de aplicación
```

### 5. Acceso a Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | voice_user / voice_password |
| pgAdmin | http://localhost:5050 | admin@example.com / admin |

### 6. Health Checks

Todos los servicios incluyen health checks:

```bash
# Verificar salud de servicios
docker-compose ps

# Health check manual de API
curl http://localhost:8000/health

# Health check de PostgreSQL
docker exec voice_biometrics_db pg_isready -U voice_user
```

---

## Deployment en Producción

### 1. Preparación del Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo apt install docker-compose-plugin

# Agregar usuario a grupo docker
sudo usermod -aG docker $USER
```

### 2. Configuración de Seguridad

**Variables de Entorno de Producción**:
```env
# NUNCA usar valores por defecto en producción
DB_PASSWORD=<strong_random_password>
SECRET_KEY=<strong_random_secret>
JWT_SECRET_KEY=<strong_random_jwt_secret>

# Configuración de producción
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING

# CORS restrictivo
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Rate limiting
RATE_LIMIT_ENABLED=True
MAX_REQUESTS_PER_MINUTE=60
```

**Generar secretos seguros**:
```bash
# Secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Configuración de Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# NO exponer puertos de DB/Redis directamente
# Usar solo dentro de red Docker
```

### 4. Configuración de Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/voice-biometrics
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Proxy settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si se usa)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts para audio processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Max upload size para audio files
    client_max_body_size 10M;
}
```

### 5. SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d api.yourdomain.com

# Auto-renovación (ya configurado por defecto)
sudo certbot renew --dry-run
```

### 6. Docker Compose para Producción

Crear `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    # NO exponer puerto externamente

  api:
    image: voice-biometrics-api:latest
    restart: always
    ports:
      - "127.0.0.1:8000:8000"  # Solo localhost
    env_file:
      - .env.production
    depends_on:
      - postgres
    volumes:
      - ./models:/app/models:ro  # Read-only
      - ./logs:/app/logs
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

volumes:
  postgres_data:

networks:
  backend:
    driver: bridge
```

Deployment:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 7. Backups Automatizados

```bash
# Script de backup: /opt/backups/backup-db.sh
#!/bin/bash
BACKUP_DIR="/opt/backups/voice-biometrics"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Backup de PostgreSQL
docker exec voice_biometrics_db pg_dump -U voice_user voice_biometrics | gzip > $BACKUP_FILE

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completado: $BACKUP_FILE"
```

Configurar cron:
```bash
# Editar crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * /opt/backups/backup-db.sh >> /var/log/voice-biometrics-backup.log 2>&1
```

---

## Configuración de Base de Datos

### Schema Inicial

El archivo `Database/init.sql` contiene:
- Creación de extensión pgvector
- Tablas principales (users, phrases, voiceprints, etc.)
- Índices optimizados
- Constraints y relaciones

### Migraciones

Para cambios en el schema:

```bash
# 1. Crear backup
pg_dump voice_biometrics > backup_before_migration.sql

# 2. Aplicar migración
psql voice_biometrics < migrations/001_add_new_column.sql

# 3. Verificar
psql voice_biometrics -c "\d+ table_name"
```

### Optimización

```sql
-- Vacuum y analyze periódico
VACUUM ANALYZE;

-- Reindex si es necesario
REINDEX DATABASE voice_biometrics;

-- Estadísticas de uso
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Modelos de Machine Learning

### Descarga Automática

Los modelos se descargan automáticamente al iniciar:
- **ECAPA-TDNN**: Speaker recognition
- **Wav2Vec2**: ASR (Automatic Speech Recognition)
- **AASIST, RawNet2, Nes2Net**: Anti-spoofing

### Descarga Manual

Si necesitas pre-descargar:

```bash
cd Backend
python scripts/download_models.py
```

### Estructura de Modelos

```
models/
├── speaker-recognition/
│   └── ecapa_tdnn/
│       ├── embedding_model.ckpt
│       ├── classifier.ckpt
│       └── hyperparams.yaml
├── text-verification/
│   └── lightweight_asr/
│       ├── wav2vec2.ckpt
│       ├── asr.ckpt
│       └── tokenizer.ckpt
└── anti-spoofing/
    ├── aasist/
    ├── rawnet2/
    └── nes2net/
```

### Tamaño de Modelos

- Total: ~2-3 GB
- Descarga inicial: 10-15 minutos (depende de conexión)
- Los modelos se cachean localmente

---

## Variables de Entorno

### Archivo .env Completo

```env
# ===================
# Database
# ===================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_biometrics
DB_USER=voice_user
DB_PASSWORD=your_secure_password

# ===================
# API Configuration
# ===================
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development  # development | production
DEBUG=True

# ===================
# Security
# ===================
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===================
# CORS
# ===================
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# ===================
# Redis (Optional)
# ===================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ===================
# ML Models
# ===================
MODEL_CACHE_DIR=./models
DEVICE=cpu  # cpu | cuda

# ===================
# Audio Processing
# ===================
MAX_AUDIO_SIZE_MB=10
SUPPORTED_AUDIO_FORMATS=wav,mp3,ogg,flac

# ===================
# Rate Limiting
# ===================
RATE_LIMIT_ENABLED=True
MAX_REQUESTS_PER_MINUTE=60

# ===================
# Logging
# ===================
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
LOG_FILE=./logs/app.log
```

---

## Monitoreo y Logs

### Logs de Aplicación

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Logs de Docker
docker-compose logs -f api

# Logs de errores
grep ERROR logs/app.log

# Logs de requests
grep "HTTP" logs/app.log
```

### Estructura de Logs

```
logs/
├── app.log          # Logs generales
├── error.log        # Solo errores
└── access.log       # Access logs
```

### Logs de Aplicación

### Health Check

```bash
# Health check básico
curl http://localhost:8000/health

# Respuesta esperada
{
  "status": "healthy",
  "service": "voice-biometrics-api",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos

```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Verificar conexión
psql -h localhost -U voice_user -d voice_biometrics

# Verificar extensión pgvector
psql voice_biometrics -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### 2. Modelos ML No Se Descargan

```bash
# Verificar conexión a internet
ping huggingface.co

# Descargar manualmente
python scripts/download_models.py

# Verificar permisos
ls -la models/
```

#### 3. Puerto 8000 Ya en Uso

```bash
# Encontrar proceso usando el puerto
lsof -i :8000

# Matar proceso
kill -9 <PID>

# O cambiar puerto en .env
API_PORT=8001
```

#### 4. Error de Memoria (OOM)

```bash
# Verificar uso de memoria
docker stats

# Aumentar límites en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G
```

#### 5. Audio Processing Timeout

```nginx
# Aumentar timeouts en Nginx
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### Logs de Debug

```bash
# Activar modo debug
export DEBUG=True
export LOG_LEVEL=DEBUG

# Reiniciar servidor
./start_server.sh
```

---

## CI/CD

### GitHub Actions (Ejemplo)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: pytest tests/ --cov=src
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t voice-biometrics-api:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push voice-biometrics-api:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/voice-biometrics
            docker-compose pull
            docker-compose up -d
```

### Deployment Manual

```bash
# 1. SSH al servidor
ssh user@server

# 2. Pull latest changes
cd /opt/voice-biometrics
git pull origin main

# 3. Rebuild y restart
docker-compose build
docker-compose up -d

# 4. Verificar
docker-compose ps
curl http://localhost:8000/health
```

---

## Checklist de Deployment

### Pre-Deployment

- [ ] Tests pasando (82%+)
- [ ] Variables de entorno configuradas
- [ ] Secretos generados (no usar defaults)
- [ ] Base de datos inicializada
- [ ] Modelos ML descargados
- [ ] Backups configurados
- [ ] SSL certificados instalados
- [ ] Firewall configurado
- [ ] Nginx configurado
- [ ] Monitoreo configurado

### Post-Deployment

- [ ] Health check OK
- [ ] API docs accesibles
- [ ] Logs sin errores críticos
- [ ] Métricas funcionando
- [ ] Backups automáticos funcionando
- [ ] SSL válido
- [ ] Rate limiting funcionando
- [ ] CORS configurado correctamente

---

## Recursos Adicionales

- **API Documentation**: http://localhost:8000/docs
- **Testing Guide**: [testing_guide.md](testing_guide.md)
- **API Reference**: [api_documentation.md](api_documentation.md)
- **System Assessment**: [system_assessment.md](system_assessment.md)

---

## Soporte

Para problemas o preguntas:
1. Revisar logs: `docker-compose logs -f api`
2. Verificar health: `curl http://localhost:8000/health`
3. Consultar documentación de API
4. Revisar issues en repositorio

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0.0
