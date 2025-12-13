# Guía de Testing - Correcciones de Persistencia de Sesión

**Fecha:** 2 de diciembre de 2025  
**Cambios Implementados:** Fase 1, 2 y 3 completas

---

## 🎯 Cambios Implementados

### ✅ Fase 1 - Correcciones Críticas
1. **Mejorado manejo de errores en AuthContext**
   - Diferencia entre errores 401 (token inválido) y errores de red
   - Mantiene sesión local ante fallos temporales
   - Retry automático en background

2. **Corregido JWT Backend**
   - Campo `sub` ahora usa email consistentemente
   - Agregado `user_id` como campo adicional
   - Incluye `refresh_token` en respuestas

### ✅ Fase 2 - Sistema de Refresh Token
3. **Endpoint de refresh en Backend**
   - `POST /api/auth/refresh` para renovar tokens
   - Validación de refresh token
   - Generación de nuevos access tokens

4. **Interceptor automático en Frontend**
   - Detecta tokens expirados (401)
   - Intenta refresh automáticamente
   - Queue de requests durante refresh
   - Solo limpia sesión si refresh falla

5. **Sincronización entre pestañas**
   - Listener de localStorage
   - Login/logout se replica en todas las tabs
   - Cambios de token detectados automáticamente

### ✅ Fase 3 - Mejoras de UX
6. **Componente ConnectionStatus**
   - Banner cuando no hay conexión
   - Toasts de conexión/desconexión
   - Indicador visual del estado

---

## 🧪 Plan de Testing Manual

### Test 1: Persistencia Básica ⭐ CRÍTICO

**Objetivo:** Verificar que la sesión persiste al recargar

**Pasos:**
```
1. Abrir http://localhost:5173
2. Login con credenciales válidas:
   - Email: dev@test.com
   - Password: 123456
3. Verificar llegada al dashboard
4. Presionar F5 o Ctrl+R (recargar página)
```

**Resultado Esperado:**
- ✅ Usuario sigue autenticado después de reload
- ✅ No hay redirección al login
- ✅ Datos del usuario visibles en sidebar/header
- ✅ Dashboard muestra información correcta

**Resultado Anterior (bug):**
- ❌ Usuario era redirigido al login
- ❌ Sesión se perdía completamente

---

### Test 2: Persistencia con Error de Red ⭐ CRÍTICO

**Objetivo:** Verificar que la sesión se mantiene aunque el servidor no responda

**Pasos:**
```
1. Login exitoso con dev@test.com
2. En DevTools > Network, activar "Offline"
3. Recargar página (F5)
```

**Resultado Esperado:**
- ✅ Banner rojo aparece: "Sin conexión - Usando datos locales"
- ✅ Usuario sigue autenticado con datos locales
- ✅ Dashboard muestra información (puede estar desactualizada)
- ✅ Toast indica "Sin conexión a internet"
- ✅ Después de 5 segundos, intenta reconectar en background

**Resultado Anterior (bug):**
- ❌ Sesión se limpiaba al detectar error de red
- ❌ Redirección forzada al login

---

### Test 3: Token Expirado con Refresh Automático ⭐ NUEVO

**Objetivo:** Verificar que tokens expirados se renuevan automáticamente

**Pasos:**
```
1. Login con usuario real (no dev):
   - Usar Backend real con base de datos
   - Usuario: admin@test.com / Password: 123456 (si existe)
   
2. Esperar 30 minutos (tiempo de expiración del token)
   O MEJOR: Modificar temporalmente en Backend:
   ACCESS_TOKEN_EXPIRE_MINUTES = 1  # 1 minuto
   
3. Después de expirar, hacer clic en cualquier link
   (Ej: Perfil, Configuración, etc.)
```

**Resultado Esperado:**
- ✅ Request falla inicialmente con 401
- ✅ Sistema automáticamente llama a /auth/refresh
- ✅ Nuevo token se guarda en localStorage
- ✅ Request original se reintenta exitosamente
- ✅ Usuario NO ve interrupciones
- ✅ No hay redirección al login

**Logs en Consola:**
```
❌ API Response Error: status: 401, url: /api/auth/profile
🔄 Token refreshed successfully
✅ API Response: status: 200, url: /api/auth/profile
```

---

### Test 4: Refresh Token Inválido

**Objetivo:** Verificar logout cuando el refresh también falla

**Pasos:**
```
1. Login exitoso
2. Abrir DevTools > Application > Local Storage
3. Modificar manualmente 'voiceauth_refresh_token' a un valor inválido
4. Esperar a que expire el access token (o forzar 401)
5. Hacer una acción que requiera API
```

**Resultado Esperado:**
- ✅ Intenta refresh automáticamente
- ✅ Refresh falla (401)
- ✅ Limpia toda la sesión (token + user)
- ✅ Muestra toast: "Sesión expirada. Por favor, inicia sesión nuevamente."
- ✅ Redirige a /login

---

### Test 5: Sincronización entre Pestañas ⭐ NUEVO

**Objetivo:** Verificar que login/logout se sincronizan entre tabs

**Pasos - Login:**
```
1. Abrir Tab 1: http://localhost:5173
2. NO hacer login todavía
3. Abrir Tab 2 en la misma URL
4. En Tab 2: Login con dev@test.com
5. Observar Tab 1
```

**Resultado Esperado:**
- ✅ Tab 1 detecta el login automáticamente
- ✅ Tab 1 muestra toast: "Sesión iniciada en otra pestaña"
- ✅ Tab 1 muestra el dashboard autenticado
- ✅ Ambas tabs sincronizadas

**Pasos - Logout:**
```
1. Con ambas tabs autenticadas
2. En Tab 1: Hacer logout
3. Observar Tab 2
```

**Resultado Esperado:**
- ✅ Tab 2 detecta el logout automáticamente
- ✅ Tab 2 muestra toast: "Sesión cerrada en otra pestaña"
- ✅ Tab 2 redirige a /login
- ✅ Ambas tabs sincronizadas

---

### Test 6: Indicador de Conexión ⭐ NUEVO

**Objetivo:** Verificar componente ConnectionStatus

**Pasos:**
```
1. Login y navegar al dashboard
2. Abrir DevTools > Network
3. Activar "Offline"
4. Esperar 2 segundos
5. Desactivar "Offline"
```

**Resultado Esperado al activar Offline:**
- ✅ Banner rojo aparece en la parte superior
- ✅ Texto: "Sin conexión - Usando datos locales"
- ✅ Ícono de WiFi desconectado visible
- ✅ Toast rojo permanente: "Sin conexión a internet"

**Resultado Esperado al desactivar Offline:**
- ✅ Banner desaparece
- ✅ Toast verde temporal: "Conexión restaurada"
- ✅ Sistema intenta sincronizar datos

---

### Test 7: Navegación con Tokens Dev

**Objetivo:** Verificar que tokens de desarrollo siguen funcionando

**Pasos:**
```
1. Login con dev@test.com
2. Navegar por varias páginas:
   - Dashboard
   - Perfil
   - Configuración
   - Enrollment
3. Recargar página en cada una
```

**Resultado Esperado:**
- ✅ Todas las páginas cargan correctamente
- ✅ Sesión persiste en todas las recargas
- ✅ Logs indican: "Dev Auth initialized (skip server verification)"
- ✅ No se hacen llamadas a /auth/profile para verificar

---

### Test 8: Backend Real vs Mock

**Objetivo:** Verificar funcionamiento con backend real

**Pre-requisitos:**
```bash
# Terminal 1 - Iniciar backend
cd Backend
python -m uvicorn src.main:app --reload

# Terminal 2 - Verificar que está corriendo
curl http://localhost:8000/api/health
```

**Pasos:**
```
1. En App/.env, verificar:
   VITE_API_BASE_URL=http://localhost:8000
   VITE_ENABLE_MOCK_DATA=false

2. Login con usuario real de la base de datos
3. Recargar página
4. Esperar a que expire el token (o forzar)
5. Hacer una acción
```

**Resultado Esperado:**
- ✅ Login exitoso con usuario real
- ✅ Sesión persiste al recargar
- ✅ Verificación con servidor exitosa
- ✅ Logs muestran: "Server Auth initialized"
- ✅ Refresh token funciona al expirar

---

## 🔧 Herramientas para Testing

### Chrome DevTools

**Console:**
```javascript
// Ver tokens almacenados
localStorage.getItem('voiceauth_token')
localStorage.getItem('voiceauth_refresh_token')
localStorage.getItem('voiceauth_user')

// Simular token expirado
// (Borrar access token pero mantener refresh)
localStorage.removeItem('voiceauth_token')

// Ver todos los items de auth
Object.keys(localStorage).filter(k => k.startsWith('voiceauth'))
```

**Network Tab:**
- Filtrar por: `/auth/`
- Verificar headers: `Authorization: Bearer ...`
- Ver payloads de refresh
- Simular offline mode

**Application Tab:**
- Local Storage > http://localhost:5173
- Editar/eliminar tokens manualmente
- Ver cookies (si se implementan en futuro)

---

## 📊 Métricas a Validar

### Antes de las Correcciones
- ❌ Persistencia de sesión: ~0% (siempre fallaba)
- ❌ Errores 401 en reload: 100%
- ❌ Usuarios frustrados: Alto
- ❌ Tiempo promedio de sesión: Bajo (constantes re-logins)

### Después de las Correcciones (Esperado)
- ✅ Persistencia de sesión: >99%
- ✅ Errores 401 en reload: <1% (solo tokens realmente inválidos)
- ✅ Refresh exitoso: >95%
- ✅ Sincronización entre tabs: 100%
- ✅ Satisfacción del usuario: Alta

---

## 🐛 Troubleshooting Común

### Problema: Sesión aún se pierde al recargar

**Diagnóstico:**
```javascript
// En consola del navegador
console.log('Token:', localStorage.getItem('voiceauth_token'))
console.log('User:', localStorage.getItem('voiceauth_user'))
```

**Causas posibles:**
1. localStorage bloqueado (modo incógnito)
2. Extensiones del navegador limpiando storage
3. Backend no está corriendo
4. Variables de entorno incorrectas

**Solución:**
- Verificar que localStorage esté habilitado
- Probar en navegador limpio (sin extensiones)
- Confirmar backend en http://localhost:8000
- Revisar App/.env

---

### Problema: Refresh token no funciona

**Diagnóstico:**
```bash
# Verificar endpoint de refresh
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "TOKEN_AQUI"}'
```

**Causas posibles:**
1. Endpoint no implementado (verificar backend)
2. Refresh token expirado (7 días)
3. Token mal formado

**Solución:**
- Hacer login nuevo (genera nuevo refresh token)
- Verificar logs del backend
- Confirmar que modelo TokenResponse incluye refresh_token

---

### Problema: Banner de conexión no desaparece

**Diagnóstico:**
```javascript
// En consola
navigator.onLine  // Debe ser true cuando hay conexión
```

**Causas posibles:**
1. Event listener no se desmonta correctamente
2. Estado local del componente atascado

**Solución:**
- Forzar reload completo (Ctrl+Shift+R)
- Revisar logs de ConnectionStatus
- Verificar que el componente se monte solo una vez

---

## 📝 Checklist de Validación Final

Antes de dar por completado el testing:

- [ ] Test 1: Persistencia básica ✅
- [ ] Test 2: Error de red no limpia sesión ✅
- [ ] Test 3: Refresh token automático ✅
- [ ] Test 4: Logout cuando refresh falla ✅
- [ ] Test 5: Sincronización entre tabs ✅
- [ ] Test 6: Indicador de conexión ✅
- [ ] Test 7: Tokens dev funcionan ✅
- [ ] Test 8: Backend real funciona ✅

**Testing en Diferentes Navegadores:**
- [ ] Chrome ✅
- [ ] Firefox ✅
- [ ] Safari ✅
- [ ] Edge ✅

**Testing en Dispositivos:**
- [ ] Desktop ✅
- [ ] Tablet ✅
- [ ] Mobile ✅

---

## 🚀 Próximos Pasos Después del Testing

Si todos los tests pasan:

1. **Commit de los cambios:**
```bash
git add .
git commit -m "fix: Resolver pérdida de sesión al recargar página

- Mejorado manejo de errores en AuthContext (diferencia 401 vs red)
- Corregido JWT backend (sub con email)
- Implementado sistema de refresh token automático
- Agregada sincronización entre pestañas
- Creado componente ConnectionStatus

Fixes #[ISSUE_NUMBER]"
```

2. **Merge a develop/main:**
```bash
git push origin feature/session-persistence-fix
# Crear Pull Request
```

3. **Deploy a staging:**
```bash
# Según proceso del equipo
```

4. **Monitoreo post-deploy:**
- Verificar logs de errores
- Monitorear tasa de refresh exitoso
- Revisar feedback de usuarios

---

## 📚 Documentación Actualizada

Los siguientes documentos se crearon/actualizaron:

1. ✅ `docs/SESSION_PERSISTENCE_FIX_PLAN.md` - Plan completo
2. ✅ `docs/SESSION_PERSISTENCE_TESTING.md` - Esta guía de testing
3. 🔄 `Backend/docs/API_DOCUMENTATION.md` - Agregar endpoint `/auth/refresh`
4. 🔄 `App/README.md` - Actualizar sección de autenticación
5. 🔄 `docs/COMPLETE_SYSTEM_SUMMARY.md` - Incluir mejoras

---

**Guía creada por:** GitHub Copilot  
**Fecha:** 2 de diciembre de 2025  
**Versión:** 1.0  
**Estado:** Lista para Testing 🧪
