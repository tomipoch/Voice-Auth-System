# Plan de Corrección: Pérdida de Sesión al Recargar Página

**Fecha:** 2 de diciembre de 2025  
**Estado:** Análisis Completo - Pendiente Implementación  
**Prioridad:** ALTA 🔴

---

## 📋 Problema Identificado

Los usuarios inician sesión exitosamente y aparecen en el dashboard, pero al recargar la página (F5 o Ctrl+R), la sesión se pierde y son redirigidos al login.

---

## 🔍 Análisis de Causas Raíz

### 1. **Problema en la Inicialización del AuthContext** ⚠️

**Ubicación:** `App/src/context/AuthContext.tsx` (líneas 93-157)

**Causa Principal:**
El useEffect de inicialización está ejecutando la lógica de verificación del token, pero existe un problema en el flujo de datos:

```tsx
// Línea 93-110
useEffect(() => {
  const initAuth = async () => {
    dispatch({ type: actionTypes.SET_LOADING, payload: true });

    const token = authStorage.getAccessToken();
    const user = authStorage.getUser();

    if (token && user) {
      try {
        // Para tokens dev: restaura la sesión
        if (token.startsWith('dev-token-') || token.startsWith('admin-token-')) {
          dispatch({
            type: actionTypes.LOGIN_SUCCESS,
            payload: { user: user, token },
          });
        }
        // Para tokens reales: verifica con el servidor
        else {
          const profile = await authService.getProfile();
          // ⚠️ PROBLEMA: Si falla, limpia todo
        }
      } catch {
        authStorage.clearAuth(); // 🚨 Esto limpia todo al recargar
        dispatch({ type: actionTypes.LOGOUT });
      }
    }
  };
  initAuth();
}, []);
```

**Problemas Detectados:**

1. **Catch sin diferenciación de errores**: El bloque catch limpia la sesión ante CUALQUIER error (red caída, timeout, servidor no disponible)
2. **Sin reintentos**: No hay mecanismo de retry si falla la verificación
3. **Comportamiento inconsistente**: Los tokens dev funcionan, los reales no persisten correctamente
4. **Race condition potencial**: Si el componente se monta/desmonta rápido, puede quedar en estado inconsistente

---

### 2. **Problema en la Estructura del Token Response** 🔑

**Ubicación:** `Backend/src/api/auth_controller.py` (líneas 146-177)

**Causa Secundaria:**
El backend retorna el user_id en el campo `sub` del JWT, pero el frontend espera el email:

```python
# Backend - auth_controller.py línea 82-96
payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
email: str = payload.get("sub")  # Espera email
if email is None:
    raise auth_error

# Pero al crear el token (línea 150-152):
access_token = create_access_token(
    data={"sub": str(user["id"]), "role": user.get("role", "user")},  # Envía user_id
    expires_delta=access_token_expires
)
```

**Impacto:**
- Discrepancia entre lo que se guarda en el token (user_id) y lo que se espera (email)
- Puede causar fallos en la validación del token en recargas

---

### 3. **Interceptor de API Demasiado Agresivo** 🔄

**Ubicación:** `App/src/services/api.ts` (líneas 56-70)

**Causa Terciaria:**
El interceptor de errores limpia la autenticación ante un 401:

```typescript
if (error.response?.status === 401) {
  authStorage.clearAuth();  // 🚨 Limpia inmediatamente
  
  if (!window.location.pathname.includes('/login')) {
    toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
    window.location.href = '/login';  // Redirección forzada
  }
}
```

**Problemas:**
- **Sin verificación del contexto**: Limpia incluso si es un error temporal de red
- **Sin retry automático**: No intenta refrescar el token
- **Redirección forzada**: `window.location.href` recarga toda la página
- **Pérdida de estado**: No guarda dónde estaba el usuario

---

### 4. **Falta de Implementación de Refresh Token** 🔄

**Ubicación:** Múltiples archivos

**Observación:**
Existe infraestructura para refresh tokens pero NO está implementada:

```typescript
// storage.ts tiene los métodos:
setRefreshToken(token: string): boolean
getRefreshToken(): string | null

// Pero apiServices.ts NO tiene endpoint de refresh
// Y api.ts NO intenta refrescar tokens expirados
```

**Impacto:**
- Sin refresh automático de tokens
- Sesión expira después de 30 minutos sin forma de renovarla
- Usuario obligado a hacer login completo nuevamente

---

### 5. **Problema de Sincronización entre Tabs** 🪟

**Ubicación:** Todo el contexto de autenticación

**Causa Adicional:**
No hay listener de localStorage para sincronizar sesiones entre pestañas:

```typescript
// La documentación en SECURITY.md menciona esto (línea 373):
window.addEventListener('storage', (e) => {
  if (e.key === 'logout') {
    window.location.href = '/login';
  }
});

// Pero NO está implementado en AuthContext.tsx
```

**Impacto:**
- Logout en una pestaña no afecta otras
- Login en una pestaña no actualiza otras
- Estado inconsistente entre tabs

---

## 🎯 Soluciones Propuestas

### **Solución 1: Mejorar Manejo de Errores en initAuth** ✅

**Prioridad:** CRÍTICA  
**Complejidad:** Baja  
**Impacto:** Alto

**Cambios en:** `App/src/context/AuthContext.tsx`

**Implementación:**
```typescript
useEffect(() => {
  const initAuth = async () => {
    dispatch({ type: actionTypes.SET_LOADING, payload: true });

    const token = authStorage.getAccessToken();
    const user = authStorage.getUser();

    if (token && user) {
      try {
        // Tokens de desarrollo: skip verificación
        if (token.startsWith('dev-token-') || token.startsWith('admin-token-')) {
          dispatch({
            type: actionTypes.LOGIN_SUCCESS,
            payload: { user, token },
          });
        } 
        // Tokens reales: verificar con servidor
        else {
          try {
            const profile = await authService.getProfile();
            dispatch({
              type: actionTypes.LOGIN_SUCCESS,
              payload: { user: profile, token },
            });
          } catch (error) {
            // ✅ MEJORA: Diferenciar tipos de error
            if (error.response?.status === 401) {
              // Token realmente inválido o expirado
              authStorage.clearAuth();
              dispatch({ type: actionTypes.LOGOUT });
              toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
            } else {
              // Error de red o servidor - MANTENER sesión local
              console.warn('Error verificando token, usando datos locales:', error);
              dispatch({
                type: actionTypes.LOGIN_SUCCESS,
                payload: { user, token },
              });
              // Intentar reconectar en background
              setTimeout(() => authService.getProfile().catch(() => {}), 5000);
            }
          }
        }
      } catch (error) {
        console.error('Error crítico en initAuth:', error);
        dispatch({ type: actionTypes.SET_LOADING, payload: false });
      }
    } else {
      dispatch({ type: actionTypes.SET_LOADING, payload: false });
    }
  };

  initAuth();
}, []);
```

**Beneficios:**
- ✅ Mantiene sesión ante errores temporales de red
- ✅ Solo limpia sesión con errores 401 confirmados
- ✅ Retry automático en background
- ✅ Mejor experiencia de usuario

---

### **Solución 2: Implementar Sistema de Refresh Token** ✅

**Prioridad:** ALTA  
**Complejidad:** Media  
**Impacto:** Muy Alto

**Cambios en:** 
- `Backend/src/api/auth_controller.py` (nuevo endpoint)
- `App/src/services/apiServices.ts` (nuevo método)
- `App/src/services/api.ts` (interceptor mejorado)

**Implementación Backend:**
```python
# auth_controller.py
@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Crear nuevo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user["id"]), "role": user.get("role", "user")},
            expires_delta=access_token_expires
        )
        
        # Retornar nuevo token
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user["id"]),
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user["email"],
                "role": user.get("role", "user"),
            }
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

**Implementación Frontend - apiServices.ts:**
```typescript
// Agregar al objeto authService:
refreshToken: async (): Promise<AuthResponse> => {
  const refreshToken = authStorage.getRefreshToken();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await api.post<AuthResponse>('/auth/refresh', {
    refresh_token: refreshToken
  });
  
  // Guardar nuevo token
  authStorage.setAccessToken(response.data.access_token);
  
  return response.data;
},
```

**Implementación Frontend - api.ts (Interceptor mejorado):**
```typescript
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

// Interceptor de respuesta mejorado
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Esperar a que termine el refresh en curso
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Intentar refrescar el token
        const { access_token } = await authService.refreshToken();
        
        authStorage.setAccessToken(access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        processQueue(null, access_token);
        
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        
        // Si falla el refresh, hacer logout
        authStorage.clearAuth();
        
        if (!window.location.pathname.includes('/login')) {
          toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

**Beneficios:**
- ✅ Renovación automática de tokens expirados
- ✅ Sin interrupciones para el usuario
- ✅ Manejo de múltiples requests simultáneos
- ✅ Logout solo cuando refresh también falla

---

### **Solución 3: Corregir JWT Backend (sub field)** ✅

**Prioridad:** MEDIA  
**Complejidad:** Baja  
**Impacto:** Medio

**Cambios en:** `Backend/src/api/auth_controller.py`

**Problema Actual:**
```python
# Línea 82-96 - ESPERA email
email: str = payload.get("sub")

# Línea 150-152 - ENVÍA user_id
access_token = create_access_token(
    data={"sub": str(user["id"]), ...}
)
```

**Opción A - Usar email consistentemente:**
```python
# Crear token con email (RECOMENDADO)
access_token = create_access_token(
    data={
        "sub": user["email"],  # ✅ Cambiar a email
        "user_id": str(user["id"]),
        "role": user.get("role", "user")
    },
    expires_delta=access_token_expires
)

# Validar con email (mantener)
async def get_current_user(credentials, user_repo):
    payload = jwt.decode(...)
    email: str = payload.get("sub")  # ✅ Ya coincide
    user = await user_repo.get_user_by_email(email)
```

**Opción B - Usar user_id consistentemente:**
```python
# Validar con user_id
async def get_current_user(credentials, user_repo):
    payload = jwt.decode(...)
    user_id: str = payload.get("sub")  # ✅ Cambiar a user_id
    user = await user_repo.get_user_by_id(user_id)  # ✅ Cambiar método
```

**Recomendación:** Opción A (email) es más estándar y seguro.

---

### **Solución 4: Sincronización entre Pestañas** ✅

**Prioridad:** MEDIA  
**Complejidad:** Baja  
**Impacto:** Medio

**Cambios en:** `App/src/context/AuthContext.tsx`

**Implementación:**
```typescript
// Agregar dentro del AuthProvider, después del useEffect de initAuth
useEffect(() => {
  // Sincronizar sesión entre pestañas
  const handleStorageChange = (e: StorageEvent) => {
    // Detectar logout en otra pestaña
    if (e.key === 'voiceauth_logout_signal') {
      authStorage.clearAuth();
      dispatch({ type: actionTypes.LOGOUT });
      toast.info('Sesión cerrada en otra pestaña');
      window.location.href = '/login';
    }
    
    // Detectar login en otra pestaña
    if (e.key === 'voiceauth_login_signal') {
      const token = authStorage.getAccessToken();
      const user = authStorage.getUser();
      
      if (token && user && !state.isAuthenticated) {
        dispatch({
          type: actionTypes.LOGIN_SUCCESS,
          payload: { user, token },
        });
        toast.info('Sesión iniciada en otra pestaña');
      }
    }
    
    // Detectar cambios en token/user directamente
    if (e.key === authConfig.tokenKey || e.key === 'voiceauth_user') {
      const newToken = authStorage.getAccessToken();
      const newUser = authStorage.getUser();
      
      if (!newToken || !newUser) {
        // Se eliminó el token/user
        dispatch({ type: actionTypes.LOGOUT });
      } else if (!state.isAuthenticated) {
        // Se agregó token/user
        dispatch({
          type: actionTypes.LOGIN_SUCCESS,
          payload: { user: newUser, token: newToken },
        });
      }
    }
  };

  window.addEventListener('storage', handleStorageChange);
  
  return () => {
    window.removeEventListener('storage', handleStorageChange);
  };
}, [state.isAuthenticated]);

// Modificar función logout para notificar a otras pestañas
const logout = async () => {
  try {
    await authService.logout();
  } catch (error) {
    console.error('❌ Error during logout:', error);
  } finally {
    // Notificar a otras pestañas
    localStorage.setItem('voiceauth_logout_signal', Date.now().toString());
    localStorage.removeItem('voiceauth_logout_signal');
    
    authStorage.clearAuth();
    dispatch({ type: actionTypes.LOGOUT });
    toast.success('Sesión cerrada exitosamente');
  }
};

// Modificar función login para notificar a otras pestañas
const login = async (credentials) => {
  // ... código existente de login ...
  
  // Después de dispatch de LOGIN_SUCCESS:
  localStorage.setItem('voiceauth_login_signal', Date.now().toString());
  localStorage.removeItem('voiceauth_login_signal');
  
  return { success: true };
};
```

**Beneficios:**
- ✅ Sincronización automática entre pestañas
- ✅ Logout en todas las pestañas simultáneamente
- ✅ Login reflejado en todas las pestañas
- ✅ Mejor seguridad y experiencia de usuario

---

### **Solución 5: Agregar Indicadores de Estado de Conexión** ✅

**Prioridad:** BAJA  
**Complejidad:** Baja  
**Impacto:** Bajo (UX)

**Cambios en:** Nuevo componente `App/src/components/ui/ConnectionStatus.tsx`

**Implementación:**
```typescript
import { useEffect, useState } from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const ConnectionStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.success('Conexión restaurada', { icon: '🟢' });
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast.error('Sin conexión a internet', { icon: '🔴', duration: Infinity });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 bg-red-500 text-white py-2 px-4 text-center z-50 flex items-center justify-center gap-2">
      <WifiOff className="w-4 h-4" />
      <span>Sin conexión - Usando datos locales</span>
    </div>
  );
};
```

**Uso en App.jsx:**
```jsx
import { ConnectionStatus } from './components/ui/ConnectionStatus';

function App() {
  return (
    <>
      <ConnectionStatus />
      {/* resto del app */}
    </>
  );
}
```

---

## 📊 Plan de Implementación

### **Fase 1: Correcciones Críticas (1-2 días)** 🔴

**Objetivo:** Resolver el problema inmediato de pérdida de sesión

1. ✅ **Mejorar manejo de errores en initAuth** (Solución 1)
   - Tiempo estimado: 2 horas
   - Testing: 1 hora
   - Deploy: Inmediato

2. ✅ **Corregir JWT Backend** (Solución 3)
   - Tiempo estimado: 1 hora
   - Testing: 1 hora
   - Deploy: Requiere reinicio del backend

**Resultado esperado:** La sesión persistirá al recargar la página

---

### **Fase 2: Mejoras de Estabilidad (2-3 días)** 🟡

**Objetivo:** Mejorar la experiencia y prevenir problemas futuros

3. ✅ **Implementar Refresh Token** (Solución 2)
   - Backend: 3 horas
   - Frontend: 4 horas
   - Testing: 2 horas
   - Deploy: Coordinado

4. ✅ **Sincronización entre pestañas** (Solución 4)
   - Tiempo estimado: 2 horas
   - Testing: 1 hora
   - Deploy: Con refresh token

**Resultado esperado:** Sistema robusto con renovación automática

---

### **Fase 3: Polish y UX (1 día)** 🟢

**Objetivo:** Mejorar feedback al usuario

5. ✅ **Indicador de conexión** (Solución 5)
   - Tiempo estimado: 1 hora
   - Testing: 30 minutos
   - Deploy: Con anteriores

**Resultado esperado:** Usuario informado del estado de su conexión

---

## 🧪 Plan de Testing

### **Tests Manuales Requeridos**

#### Test 1: Persistencia Básica
```
1. Login con credenciales válidas
2. Navegar al dashboard
3. Recargar página (F5)
✅ Verificar: Usuario sigue autenticado
✅ Verificar: No hay redirección al login
✅ Verificar: Datos del usuario visibles
```

#### Test 2: Token Expirado
```
1. Login con credenciales válidas
2. Esperar 30 minutos (o modificar expiracion a 1 minuto para testing)
3. Hacer una acción que requiera API
✅ Verificar: Token se refresca automáticamente
✅ Verificar: Acción se completa exitosamente
✅ Verificar: No se pierde la sesión
```

#### Test 3: Error de Red
```
1. Login con credenciales válidas
2. Desconectar red (WiFi off)
3. Recargar página
✅ Verificar: Sesión se mantiene con datos locales
✅ Verificar: Indicador de "sin conexión" visible
4. Reconectar red
✅ Verificar: Indicador desaparece
✅ Verificar: Datos se sincronizan
```

#### Test 4: Multiple Tabs
```
1. Abrir app en Tab 1
2. Login en Tab 1
3. Abrir Tab 2 con la misma URL
✅ Verificar: Tab 2 muestra usuario autenticado
4. Logout en Tab 1
✅ Verificar: Tab 2 también cierra sesión
```

#### Test 5: Tokens Desarrollo vs Producción
```
1. Login con dev@test.com (token desarrollo)
2. Recargar página
✅ Verificar: Sesión persiste sin verificación servidor
3. Login con usuario real
4. Recargar página
✅ Verificar: Sesión persiste CON verificación servidor
```

### **Tests Automatizados Sugeridos**

```typescript
// App/src/test/__tests__/auth-persistence.test.tsx
describe('Auth Persistence', () => {
  it('should restore session from localStorage on mount', async () => {
    // Setup
    localStorage.setItem('voiceauth_token', 'mock-token');
    localStorage.setItem('voiceauth_user', JSON.stringify({
      id: '1',
      name: 'Test User',
      email: 'test@test.com'
    }));

    // Render
    render(<App />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });

  it('should handle invalid token gracefully', async () => {
    // Setup invalid token
    localStorage.setItem('voiceauth_token', 'invalid-token');
    
    // Mock API error
    server.use(
      rest.get('/api/auth/profile', (req, res, ctx) => {
        return res(ctx.status(401));
      })
    );

    // Render
    render(<App />);

    // Assert - should redirect to login
    await waitFor(() => {
      expect(screen.getByText('Iniciar Sesión')).toBeInTheDocument();
    });
  });

  it('should retry verification on network error', async () => {
    // Setup
    localStorage.setItem('voiceauth_token', 'valid-token');
    
    // Mock network error then success
    let callCount = 0;
    server.use(
      rest.get('/api/auth/profile', (req, res, ctx) => {
        callCount++;
        if (callCount === 1) {
          return res.networkError('Connection failed');
        }
        return res(ctx.json({ name: 'Test User' }));
      })
    );

    // Render
    render(<App />);

    // Assert - should maintain session and retry
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });
});
```

---

## 📈 Métricas de Éxito

### **KPIs a Monitorear**

1. **Tasa de Persistencia de Sesión**
   - Objetivo: > 99% de sesiones persisten tras reload
   - Medición: Analytics o logs

2. **Tasa de Refresh Token Exitoso**
   - Objetivo: > 95% de refreshes exitosos
   - Medición: Logs del backend

3. **Errores de Autenticación**
   - Objetivo: Reducción del 80% en errores 401
   - Medición: Error tracking

4. **Tiempo de Recuperación ante Errores de Red**
   - Objetivo: < 5 segundos para reconexión
   - Medición: Performance monitoring

5. **Satisfacción del Usuario**
   - Objetivo: Eliminación de quejas por "logout inesperado"
   - Medición: Feedback directo

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Tokens nunca expiran en cliente
**Impacto:** Medio  
**Probabilidad:** Media  
**Mitigación:** 
- Implementar máximo de intentos de refresh (3)
- Force logout después de X días sin uso
- Validación periódica en background

### Riesgo 2: Race conditions en múltiples tabs
**Impacto:** Bajo  
**Probabilidad:** Baja  
**Mitigación:**
- Usar locks con timestamps en localStorage
- Cooldown de 1 segundo para eventos storage

### Riesgo 3: Tokens almacenados en localStorage (seguridad)
**Impacto:** Alto  
**Probabilidad:** Baja  
**Mitigación Futura:**
- Migrar a httpOnly cookies (requiere cambios backend)
- Implementar encriptación de tokens en localStorage
- Rotación automática de tokens

### Riesgo 4: Backend no disponible durante despliegue
**Impacto:** Bajo  
**Probabilidad:** Media  
**Mitigación:**
- Despliegue en horario de bajo tráfico
- Health checks antes de cambiar rutas
- Rollback plan preparado

---

## 🔄 Proceso de Rollout

### Ambiente de Desarrollo
1. Implementar cambios
2. Testing manual completo
3. Testing automatizado
4. Code review

### Ambiente de Staging (si existe)
1. Deploy completo
2. Testing de integración
3. Testing de carga
4. Monitoring 24h

### Ambiente de Producción
1. Deploy backend primero (nuevo endpoint /refresh)
2. Verificar health check
3. Deploy frontend con feature flag
4. Monitoreo intensivo 1 hora
5. Habilitar feature flag gradualmente (10% → 50% → 100%)
6. Monitoreo post-deploy 24h

### Plan de Rollback
```bash
# Si hay problemas críticos:
1. Revertir feature flag a 0%
2. Rollback frontend si es necesario
3. Investigar logs
4. Fix en dev
5. Re-deploy
```

---

## 📝 Checklist de Implementación

### Backend
- [ ] Crear endpoint `/auth/refresh`
- [ ] Modificar `create_access_token` para usar email en `sub`
- [ ] Agregar logs para debugging de tokens
- [ ] Testing del endpoint de refresh
- [ ] Documentar cambios en API_DOCUMENTATION.md

### Frontend - Fase 1 (Crítico)
- [ ] Modificar `AuthContext.tsx` - mejorar manejo de errores
- [ ] Agregar diferenciación de errores 401 vs network
- [ ] Agregar retry automático en background
- [ ] Testing manual de persistencia
- [ ] Testing en diferentes navegadores

### Frontend - Fase 2 (Mejoras)
- [ ] Implementar `refreshToken()` en apiServices.ts
- [ ] Modificar interceptor en api.ts para refresh automático
- [ ] Implementar queue de requests durante refresh
- [ ] Agregar sincronización entre pestañas
- [ ] Testing de refresh automático
- [ ] Testing multi-tab

### Frontend - Fase 3 (Polish)
- [ ] Crear componente ConnectionStatus
- [ ] Integrar en App.jsx
- [ ] Agregar toasts informativos
- [ ] Testing de UX

### Testing
- [ ] Escribir tests automatizados
- [ ] Testing manual completo (todos los escenarios)
- [ ] Testing en móviles
- [ ] Testing de performance

### Documentación
- [ ] Actualizar README con cambios
- [ ] Actualizar SECURITY.md con mejoras
- [ ] Documentar troubleshooting común
- [ ] Actualizar CHANGELOG

---

## 🎓 Lecciones Aprendidas (Para Futuro)

1. **Siempre diferenciar tipos de errores** en bloques catch
2. **Implementar refresh tokens desde el inicio** del proyecto
3. **Testing de persistencia debe ser prioritario** en auth
4. **Logs detallados son cruciales** para debugging de autenticación
5. **Considerar múltiples tabs/dispositivos** desde el diseño

---

## 📚 Referencias

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Refresh Token Flow](https://oauth.net/2/grant-types/refresh-token/)
- [Web Storage API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API)
- [React Authentication Patterns](https://kentcdodds.com/blog/authentication-in-react-applications)

---

## 👥 Equipo y Responsabilidades

- **Backend Lead**: Implementar endpoint de refresh
- **Frontend Lead**: Modificar AuthContext y api.ts
- **QA**: Ejecutar plan de testing completo
- **DevOps**: Coordinar deploys y rollback plan

---

## ✅ Próximos Pasos Inmediatos

1. **Revisar y aprobar este plan** con el equipo
2. **Crear tickets en el sistema de tracking** (Jira/GitHub Issues)
3. **Asignar responsables** a cada tarea
4. **Comenzar Fase 1** (correcciones críticas)
5. **Daily standup** para monitorear progreso

---

**Documento creado por:** GitHub Copilot  
**Fecha:** 2 de diciembre de 2025  
**Versión:** 1.0  
**Estado:** Listo para Implementación 🚀
