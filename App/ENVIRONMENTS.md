# VoiceAuth - Configuración de Ambientes

Este proyecto está configurado con múltiples ambientes (development, staging, production) para facilitar el desarrollo y despliegue.

## 📁 Estructura de Configuración

```
App/
├── .env                    # Variables base (no modificar)
├── .env.development        # Configuración de desarrollo
├── .env.staging           # Configuración de staging (opcional)
├── .env.production        # Configuración de producción
├── .env.local             # Override local (no se sube a git)
├── scripts/
│   └── check-env.cjs      # Script de verificación de ambiente
└── package.json           # Comandos npm configurados
```

## 🛠️ Comandos Disponibles

### Desarrollo
```bash
npm run dev                # Desarrollo estándar
npm run dev:local          # Desarrollo con config local específica  
npm run dev:watch          # Desarrollo con watch mode
npm run dev:network        # Desarrollo accesible desde red
npm run start             # Alias para npm run dev
npm run start:dev         # Desarrollo explícito
```

### Build
```bash
npm run build             # Build para producción
npm run build:dev         # Build para desarrollo
npm run build:staging     # Build para staging
npm run build:prod        # Build para producción (explícito)
npm run build:analyze     # Build + análisis de bundle
```

### Preview
```bash
npm run preview           # Preview del build de producción
npm run preview:dev       # Preview del build de desarrollo
npm run preview:staging   # Preview del build de staging
npm run preview:prod      # Preview del build de producción
```

### Utilidades
```bash
npm run lint              # Linter
npm run lint:fix          # Auto-fix de linter
npm run clean             # Limpiar cache de Vite
npm run clean:cache       # Limpiar solo cache
npm run clean:all         # Limpieza completa
npm run typecheck         # Verificación de tipos TypeScript
npm run env:check [env]   # Verificar configuración de ambiente
npm run env:copy          # Copiar .env.example a .env.local
npm run install:fresh     # Instalación limpia
```

### Deploy
```bash
npm run deploy:dev        # Deploy a desarrollo
npm run deploy:staging    # Deploy a staging  
npm run deploy:prod       # Deploy a producción
```

## 🔧 Variables de Entorno por Ambiente

### Desarrollo (.env.development)
- **Debug**: Habilitado
- **Mock Data**: Habilitado
- **API**: http://localhost:8000
- **Logs**: Detallados
- **Analytics**: Deshabilitado

### Producción (.env.production)
- **Debug**: Deshabilitado
- **Mock Data**: Deshabilitado
- **API**: https://api.voiceauth.com (cambiar por URL real)
- **Logs**: Solo errores
- **Analytics**: Habilitado
- **HTTPS**: Habilitado

## 📋 Variables Principales

| Variable | Desarrollo | Producción | Descripción |
|----------|------------|------------|-------------|
| `VITE_APP_NAME` | VoiceAuth (DEV) | VoiceAuth | Nombre de la app |
| `VITE_DEBUG` | true | false | Modo debug |
| `VITE_API_BASE_URL` | localhost:8000 | api.domain.com | URL del API |
| `VITE_ENABLE_MOCK_DATA` | true | false | Datos mock |
| `VITE_ENABLE_ANALYTICS` | false | true | Analytics |
| `VITE_ENABLE_CONSOLE_LOGS` | true | false | Logs en consola |
| `VITE_STORAGE_PREFIX` | voiceauth_dev_ | voiceauth_ | Prefijo storage |

## 🚀 Configuración Inicial

### 1. Instalar dependencias
```bash
npm install
```

### 2. Verificar configuración
```bash
npm run env:check development
npm run env:check production
```

### 3. Configurar ambiente local (opcional)
```bash
npm run env:copy
# Editar .env.local según necesidades
```

### 4. Ejecutar en desarrollo
```bash
npm run dev
```

## 🔍 Verificación de Ambiente

El script `check-env.cjs` valida:
- ✅ Existencia de archivos de configuración
- ✅ Variables requeridas por ambiente
- ✅ Formato de URLs
- ⚠️ Configuraciones problemáticas (debug en prod, etc.)

```bash
# Verificar desarrollo
npm run env:check development

# Verificar producción  
npm run env:check production
```

## 🎯 Buenas Prácticas

### Desarrollo
1. **Usar .env.local** para configuraciones específicas de tu máquina
2. **No subir .env.local** al repositorio (está en .gitignore)
3. **Verificar ambiente** antes de hacer commits importantes
4. **Usar mock data** durante desarrollo para no depender del backend

### Producción
1. **Configurar variables** directamente en el servidor/CI/CD
2. **Nunca hardcodear** secretos en código
3. **Verificar configuración** antes de desplegar
4. **Monitorear** errores y rendimiento

### Staging
1. **Usar datos de prueba** similares a producción
2. **Probar configuraciones** antes de ir a producción
3. **Validar** integraciones y servicios externos

## 📱 Configuración por Servicio

### Storage Local
- **Prefijo automático** por ambiente
- **Migración** entre versiones
- **Limpieza** automática de datos obsoletos

### API
- **Timeouts** configurables por ambiente
- **Retry** automático en requests
- **Logging** detallado en desarrollo

### Autenticación
- **Tokens** con expiración configurable
- **Storage** seguro con prefijos
- **Refresh** automático de tokens

## 🐛 Troubleshooting

### Puerto en uso
```bash
# El servidor cambiará automáticamente al siguiente puerto disponible
# Puerto por defecto: 5173, alternativo: 5174, etc.
```

### Variables no se cargan
1. Verificar sintaxis en archivos .env
2. Reiniciar servidor de desarrollo
3. Verificar que variables empiecen con `VITE_`

### Build falla
1. Ejecutar verificación de ambiente: `npm run env:check production`
2. Limpiar cache: `npm run clean`
3. Reinstalar dependencias: `npm run install:fresh`

### Storage no funciona
1. Verificar configuración de prefijos
2. Limpiar localStorage manualmente
3. Verificar modo del navegador (privado puede causar problemas)

## 🔄 Flujo de Trabajo Recomendado

### Desarrollo Diario
```bash
git pull                           # Actualizar código
npm run env:check development      # Verificar configuración  
npm run dev                       # Iniciar desarrollo
```

### Antes de Deploy
```bash
npm run lint                      # Verificar código
npm run typecheck                 # Verificar tipos
npm run env:check production      # Verificar config producción
npm run build:prod               # Probar build
npm run preview:prod             # Probar build localmente
```

### CI/CD Pipeline
```bash
npm run env:check $ENVIRONMENT    # Verificar configuración
npm run build:$ENVIRONMENT       # Build para ambiente
npm run test                     # Ejecutar tests (cuando estén configurados)
```

## 📞 Soporte

Si tienes problemas con la configuración:

1. 🔍 Ejecuta `npm run env:check [ambiente]` para diagnóstico
2. 📋 Revisa este README para buenas prácticas
3. 🧹 Prueba `npm run clean && npm install` para limpiar
4. 💬 Consulta con el equipo de desarrollo

---

**Nota**: Este sistema de configuración está diseñado para ser escalable y maintible. Cada ambiente tiene sus propias características optimizadas para su uso específico.