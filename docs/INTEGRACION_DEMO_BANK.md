# Integración Demo-Bank con API Biométrica

## **Arquitectura de Integración**

```
┌─────────────────────┐
│  Frontend Demo-Bank │  (React + Vite)
│   localhost:5174    │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  Backend Demo-Bank  │  (Hono Server)
│   localhost:3001    │  - Maneja autenticación del banco
│                     │  - Gestiona sesiones de usuarios
│                     │  - Proxy/intermediario
└──────────┬──────────┘
           │ HTTP/REST + JWT
           ▼
┌─────────────────────┐
│  API Biométrica     │  (FastAPI)
│   localhost:8000    │  - Sistema de biometría de voz
│                     │  - Enrollment y Verification
└─────────────────────┘
```

---

## **Flujo de Autenticación**

### **1. Usuario del Banco se Autentica**

```typescript
// Frontend → Backend Demo-Bank
POST http://localhost:3001/api/auth/login
{
  "email": "demo@banco.cl",
  "password": "demo123"
}

Response:
{
  "access_token": "token_del_banco",
  "user": {
    "id": "demo-user-1",
    "email": "demo@banco.cl",
    ...
  }
}
```

### **2. Backend Demo-Bank se Autentica en API Biométrica**

```typescript
// Backend Demo-Bank → API Biométrica (caché de token)
POST http://localhost:8000/api/auth/login
{
  "email": "admin@banco-pirulete.cl",
  "password": "AdminBanco2024!"
}

Response:
{
  "access_token": "jwt_token_biometric_api",
  "token_type": "bearer",
  "expires_in": 7200
}
```

**Nota:** El backend del banco cachea este token por 120 minutos y lo reutiliza para todas las llamadas a la API biométrica.

---

## **Flujo de Enrollment (Inscripción de Voz)**

### **Paso 1: Verificar Estado de Enrollment**

```typescript
// Frontend → Backend Demo-Bank
GET http://localhost:3001/api/enrollment/status
Authorization: Bearer <token_del_banco>

// Backend Demo-Bank → API Biométrica
GET http://localhost:8000/api/enrollment/status/{user_id}
Authorization: Bearer <jwt_token_biometric_api>

Response:
{
  "is_enrolled": false,
  "enrollment_status": "not_enrolled",
  "sample_count": 0
}
```

---

### **Paso 2: Iniciar Sesión de Enrollment**

```typescript
// Frontend → Backend Demo-Bank
POST http://localhost:3001/api/enrollment/start
Authorization: Bearer <token_del_banco>

// Backend Demo-Bank → API Biométrica
POST http://localhost:8000/api/enrollment/start
Authorization: Bearer <jwt_token_biometric_api>
Content-Type: multipart/form-data

FormData:
- user_id: "uuid" (opcional, si el usuario ya existe)
- external_ref: "banco_demo-user-1"
- difficulty: "medium"
- force_overwrite: "true"

Response:
{
  "success": true,
  "enrollment_id": "uuid",
  "user_id": "uuid",
  "challenges": [
    { "id": "uuid", "text": "El sol brilla..." },
    { "id": "uuid", "text": "Las estrellas..." },
    { "id": "uuid", "text": "El viento sopla..." }
  ],
  "required_samples": 3
}
```

**Mapeo en el servidor del banco:**
```typescript
phrases: result.challenges?.map((ch) => ({ 
  id: ch.challenge_id,  // ✅ Usar 'challenge_id', no 'id'
  text: ch.phrase       // ✅ Usar 'phrase', no 'text'
}))
```

---

### **Paso 3: Enviar Muestras de Audio**

```typescript
// Frontend → Backend Demo-Bank
POST http://localhost:3001/api/enrollment/audio
Authorization: Bearer <token_del_banco>
Content-Type: multipart/form-data

FormData:
- audio: Blob (archivo WebM)
- phrase_id: "uuid"
- phrase_text: "El sol brilla..."

// Backend Demo-Bank → API Biométrica
POST http://localhost:8000/api/enrollment/add-sample
Authorization: Bearer <jwt_token_biometric_api>
Content-Type: multipart/form-data

FormData:
- enrollment_id: "uuid"
- challenge_id: "uuid"
- audio_file: Blob (WebM)

Response (muestra 1 o 2):
{
  "success": true,
  "sample_id": "uuid",
  "samples_completed": 1,
  "samples_required": 3,
  "is_complete": false,
  "next_phrase": { "id": "uuid", "text": "..." }
}

Response (muestra 3 - completa):
{
  "success": true,
  "sample_id": "uuid",
  "samples_completed": 3,
  "samples_required": 3,
  "is_complete": true
}
```

---

### **Paso 4: Completar Enrollment**

```typescript
// Cuando is_complete = true

// Backend Demo-Bank → API Biométrica
POST http://localhost:8000/api/enrollment/complete
Authorization: Bearer <jwt_token_biometric_api>
Content-Type: multipart/form-data

FormData:
- enrollment_id: "uuid"

Response:
{
  "success": true,
  "voiceprint_id": "uuid",
  "user_id": "uuid",
  "enrollment_quality": 0.95,
  "samples_used": 3,
  "message": "Enrollment completed successfully"
}
```

---

## **Flujo de Verification (Verificación de Voz)**

### **Verificación Rápida (Quick Verify)**

```typescript
// Frontend → Backend Demo-Bank
POST http://localhost:3001/api/verification/voice
Authorization: Bearer <token_del_banco>
Content-Type: multipart/form-data

FormData:
- audio: Blob (WebM)
- phrase_id: "uuid"
- phrase_text: "Texto de la frase..."

// Backend Demo-Bank → API Biométrica
POST http://localhost:8000/api/verification/quick-verify
Authorization: Bearer <jwt_token_biometric_api>
Content-Type: multipart/form-data

FormData:
- user_id: "uuid"
- audio_file: Blob (WebM)

Response:
{
  "verification_id": null,
  "user_id": "uuid",
  "is_verified": true,
  "confidence_score": 0.92,
  "similarity_score": 0.88,
  "anti_spoofing_score": 0.95,
  "phrase_match": null,
  "is_live": true,
  "threshold_used": 0.75
}
```

**Mapeo de respuesta:**
```typescript
{
  success: true,
  verified: result.is_verified,
  confidence: result.confidence_score || result.similarity_score,
  message: result.is_verified ? 'Verificación exitosa' : 'Verificación fallida',
  details: {
    speaker_score: result.similarity_score,        // ✅
    text_score: result.phrase_match ? 1.0 : 0.0,   // ✅
    spoofing_score: result.anti_spoofing_score,    // ✅ (no 'antispoofing_score')
  }
}
```

---

## **Endpoints Corregidos**

### **✅ Correcciones Implementadas:**

| Endpoint Original | Endpoint Correcto | Cambios |
|-------------------|-------------------|---------|
| Headers: `X-API-Key` | Headers: `Authorization: Bearer <token>` | Autenticación JWT |
| `challenge_id` en response | `id` en response | Mapeo correcto de challenges |
| `phrase` en response | `text` en response | Campo correcto de texto |
| `antispoofing_score` | `anti_spoofing_score` | Nombre correcto del campo |
| Sin `user_id` en enrollment/start | Con `user_id` opcional | Permite reutilizar usuarios |

---

## **Configuración del Backend Demo-Bank**

### **Archivo: `server/config.ts`**

```typescript
export const config = {
  port: 3001,
  
  biometricApi: {
    baseUrl: 'http://localhost:8000',
    // Credenciales del banco en el sistema biométrico
    adminEmail: 'admin@familia.com',
    adminPassword: 'AdminFamilia123',
  },
  
  company: {
    name: 'Banco Familia',
    clientId: 'banco-familia',
  },
};
```

**Requisitos:**
1. El banco debe tener una cuenta registrada en el sistema biométrico
2. El email y password deben ser válidos en `/api/auth/login`
3. El usuario debe tener rol `admin` o permisos suficientes

---

## **Sistema de Caché de Token**

El backend del banco implementa un sistema de caché para el token JWT:

```typescript
let biometricApiToken: string | null = null;
let biometricTokenExpiry: number = 0;

async function getBiometricApiToken(): Promise<string | null> {
  // Si el token existe y no ha expirado (con 5 min de margen)
  if (biometricApiToken && Date.now() < biometricTokenExpiry - 5 * 60 * 1000) {
    return biometricApiToken;
  }

  // Autenticar y obtener nuevo token
  const response = await fetch('/api/auth/login', { ... });
  biometricApiToken = data.access_token;
  biometricTokenExpiry = Date.now() + (data.expires_in || 7200) * 1000;
  
  return biometricApiToken;
}
```

**Ventajas:**
- ✅ Evita autenticaciones innecesarias
- ✅ Renueva automáticamente cuando expira
- ✅ Margen de seguridad de 5 minutos
- ✅ Un solo token para todas las peticiones

---

## **Gestión de Usuarios Biométricos**

### **Estrategia de Mapeo:**

```typescript
interface DemoUser {
  id: string;                    // ID interno del banco
  email: string;
  biometric_user_id?: string;    // UUID del sistema biométrico
  enrollment_id?: string;        // ID de sesión de enrollment
  is_voice_enrolled: boolean;    // Estado local
}
```

### **🔑 Creación Automática de Usuario**

Cuando un usuario del banco inicia el enrollment por primera vez:

**Flujo:**
1. 🏛️ Usuario del banco inicia sesión en demo-bank
2. ❓ Backend del banco consulta: ¿Está este usuario en la API biométrica?
3. ❌ Si **NO existe**: La API biométrica crea automáticamente el usuario
4. ✅ Si **SÍ existe**: Usa el `user_id` existente
5. 🎯 Inicia enrollment con el `user_id` (nuevo o existente)

**Implementación en `/api/enrollment/start`:**

```typescript
// El backend del banco envía:
POST http://localhost:8000/api/enrollment/start
FormData:
  - user_id: "uuid" (opcional)
  - external_ref: "banco_demo-user-1"
  - difficulty: "medium"
  - force_overwrite: "true"

// La API biométrica:
// 1. Si user_id existe -> Verifica que exista en BD
// 2. Si user_id NO existe -> Crea nuevo usuario automáticamente
// 3. Asocia external_ref="banco_demo-user-1" para tracking
// 4. Inicia sesión de enrollment

Response:
{
  "enrollment_id": "uuid-enrollment",
  "user_id": "uuid-user" // Nuevo o existente
}
```

**Backend del banco guarda el mapeo:**
```typescript
user.biometric_user_id = result.user_id;  // Guardar para futuras verificaciones
user.enrollment_id = result.enrollment_id;  // Guardar para esta sesión
```

### **🔄 Persistencia del Estado**

**Problema:** En el demo actual, el mapeo se pierde al reiniciar el servidor.

**Solución recomendada para producción:**
```sql
-- Tabla en la BD del banco
CREATE TABLE user_biometric_mapping (
  bank_user_id VARCHAR(50) PRIMARY KEY,
  biometric_user_id UUID NOT NULL,
  is_enrolled BOOLEAN DEFAULT FALSE,
  enrolled_at TIMESTAMP,
  last_verification TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## **🔄 Sincronización de Estado de Enrollment**

### **Problema: Estado No Actualizado**

Después de completar el enrollment, el frontend puede no actualizar inmediatamente el estado global, mostrando la opción "Registrar voz" cuando ya no debería aparecer.

### **Solución: Estrategia de Actualización**

#### **1. Actualizar Estado Local del Usuario**

```typescript
// En server/index.ts - Cuando enrollment se completa exitosamente
if (result.enrollment_complete) {
  // Backend del banco actualiza su estado local
  user.is_voice_enrolled = true;
  
  // Actualizar en el array de usuarios demo
  const idx = demoUsers.findIndex(u => u.id === user.id);
  if (idx >= 0) {
    demoUsers[idx].is_voice_enrolled = true;
  }
}
```

#### **2. Frontend: Revalidar Estado Después de Enrollment**

```typescript
// En EnrollmentPage.tsx
const processRecording = async (audioBlob: Blob) => {
  // ... proceso de enrollment
  
  if (result.enrollment_complete) {
    toast.success('¡Registro de voz completado!');
    
    // 🔑 IMPORTANTE: Revalidar estado antes de redirigir
    await biometricService.getEnrollmentStatus();
    
    // Redirigir al dashboard
    setTimeout(() => navigate('/dashboard'), 2000);
  }
};
```

#### **3. Dashboard: Recargar Estado al Montar**

```typescript
// En DashboardPage.tsx
useEffect(() => {
  const loadEnrollmentStatus = async () => {
    try {
      const status = await biometricService.getEnrollmentStatus();
      setEnrollmentStatus(status);
    } catch (error) {
      console.error('Error checking enrollment status:', error);
    }
  };
  
  // Cargar siempre al montar el componente
  loadEnrollmentStatus();
}, [navigate]);

// Ocultar botón de enrollment si ya está enrollado
const isEnrolled = enrollmentStatus?.is_enrolled || 
                   enrollmentStatus?.enrollment_status === 'enrolled';

{!isEnrolled && (
  <div className="bg-alert...">
    <button onClick={() => navigate('/enroll')}>
      Activar ahora
    </button>
  </div>
)}
```

#### **4. Header: Condicional para Link de Enrollment**

```typescript
// En Header.tsx
interface HeaderProps {
  showNav: boolean;
  isEnrolled: boolean;  // Recibir estado desde padre
}

export default function Header({ showNav, isEnrolled }: HeaderProps) {
  return (
    <header>
      {showNav && (
        <nav>
          {/* Solo mostrar link si NO está enrollado */}
          {!isEnrolled && (
            <Link to="/enroll">
              <Mic /> Registrar Voz
            </Link>
          )}
          
          {/* Otros links siempre visibles */}
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/transfer">Transferir</Link>
        </nav>
      )}
    </header>
  );
}
```

### **✅ Checklist de Validación**

Para asegurar que el estado se sincroniza correctamente:

- [ ] **Backend del banco actualiza `user.is_voice_enrolled = true`** cuando enrollment completa
- [ ] **API biométrica retorna `is_enrolled: true`** en `/api/enrollment/status/{user_id}`
- [ ] **Frontend verifica estado al montar cada página** (Dashboard, Profile)
- [ ] **EnrollmentPage redirige solo después de confirmar enrollment**
- [ ] **Header recibe prop `isEnrolled`** y oculta link de enrollment
- [ ] **Dashboard oculta banner de alerta** cuando `isEnrolled === true`
- [ ] **ProfilePage muestra estado "Voz registrada"** cuando está enrollado

### **🚨 Casos Edge a Considerar**

#### **Caso 1: Usuario Enrollado en Otra Sesión**
```typescript
// Si el usuario se enrolló en otro dispositivo/navegador
// El estado debe sincronizarse desde la API biométrica

useEffect(() => {
  // Consultar SIEMPRE a la API, no confiar solo en localStorage
  const checkStatus = async () => {
    const status = await biometricService.getEnrollmentStatus();
    setEnrollmentStatus(status);
  };
  
  checkStatus();
}, []);
```

#### **Caso 2: Enrollment Interrumpido**
```typescript
// Si el usuario sale de la página antes de completar
// El enrollment debe reiniciarse desde cero

if (result.samples_completed < result.samples_required) {
  // Aún no completo, puede continuar
} else {
  // Completo, marcar como enrolled
  user.is_voice_enrolled = true;
}
```

#### **Caso 3: Force Overwrite**
```typescript
// Si el usuario quiere re-enrollarse
const restartEnrollment = async () => {
  const response = await fetch('/api/enrollment/start', {
    body: formData.append('force_overwrite', 'true')
  });
  
  // Esto creará una nueva sesión y sobrescribirá la huella anterior
};
```

---

## **Manejo de Errores**

### **Error: Token Expirado (401)**

```typescript
if (response.status === 401) {
  // Limpiar token en caché
  biometricApiToken = null;
  biometricTokenExpiry = 0;
  
  // Reintentar con nuevo token
  const newToken = await getBiometricApiToken();
  // ... reintentar petición
}
```

### **Error: Sesión de Enrollment Expirada**

```typescript
if (errorText.includes('expired')) {
  user.enrollment_id = undefined;
  return {
    success: false,
    message: 'Sesión expirada, por favor intenta de nuevo',
    retry: true
  };
}
```

### **Fallback Mode (API No Disponible)**

```typescript
catch (error) {
  console.error('Error connecting to biometric API:', error);
  
  // Modo demo/fallback
  return {
    success: true,
    verified: true,
    confidence: 0.87,
    message: 'Verificación exitosa (modo demo)',
    details: { ... }
  };
}
```

---

## **Checklist de Integración**

### **✅ Antes de Producción:**

#### **Backend del Banco**
- [ ] Crear cuenta de admin para el banco en el sistema biométrico
- [ ] Configurar credenciales seguras (no usar defaults)
- [ ] Implementar almacenamiento persistente de `biometric_user_id` (BD)
- [ ] Actualizar `is_voice_enrolled` al completar enrollment
- [ ] Implementar retry logic con exponential backoff
- [ ] Configurar timeouts apropiados
- [ ] Implementar health checks de la API biométrica
- [ ] Configurar logs de auditoría

#### **API Biométrica**
- [ ] Verificar que `/api/enrollment/start` crea usuarios automáticamente
- [ ] Verificar que `/api/enrollment/status/{user_id}` retorna estado correcto
- [ ] Configurar HTTPS para comunicación segura
- [ ] Implementar rate limiting
- [ ] Verificar conversión de audio (WebM → WAV)

#### **Frontend del Banco**
- [ ] Verificar estado de enrollment al montar Dashboard
- [ ] Verificar estado de enrollment al montar Profile
- [ ] Ocultar botón "Registrar Voz" cuando `isEnrolled === true`
- [ ] Ocultar link de enrollment en Header cuando está enrollado
- [ ] Redirigir desde `/enroll` si ya está enrollado
- [ ] Mostrar estado "Voz registrada" en Profile
- [ ] Revalidar estado después de completar enrollment

#### **Pruebas de Integración**
- [ ] Probar flujo completo de enrollment (usuario nuevo)
- [ ] Probar flujo de verificación (usuario enrollado)
- [ ] Probar que usuario enrollado no ve opción de registro
- [ ] Probar que estado persiste después de logout/login
- [ ] Probar force_overwrite (re-enrollment)
- [ ] Probar manejo de errores (API caída, timeout, etc.)
- [ ] Probar sincronización entre múltiples dispositivos/sesiones

---

## **Variables de Entorno Recomendadas**

```bash
# Backend Demo-Bank (.env)
PORT=3001
BIOMETRIC_API_URL=http://localhost:8000
BIOMETRIC_ADMIN_EMAIL=admin@banco-pirulete.cl
BIOMETRIC_ADMIN_PASSWORD=AdminBanco2024!
BANK_JWT_SECRET=your-bank-secret-key
NODE_ENV=development
```

---

## **Pruebas de Integración**

### **Test 1: Autenticación**
```bash
# 1. Autenticar en el banco
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@banco.cl","password":"demo123"}'

# 2. Verificar que el backend del banco puede autenticarse en la API biométrica
# (Ver logs del servidor)
```

### **Test 2: Enrollment Completo**
```bash
# 1. Iniciar enrollment
# 2. Enviar 3 muestras de audio
# 3. Verificar que se completa automáticamente
# 4. Verificar estado enrolled
```

### **Test 3: Verificación**
```bash
# 1. Enviar audio de usuario enrollado
# 2. Verificar que is_verified = true
# 3. Verificar scores (>0.75 típicamente)
```

---

## **Logs de Monitoreo**

El backend del banco registra:

```
✅ Autenticado en API biométrica
[Enrollment] Started: { enrollment_id, user_id }
[Enrollment] Audio received: { size, type, phraseId }
[Enrollment] Sample result: { samples_completed, is_complete }
[Enrollment] Completed successfully!
[Verification] Result: { is_verified, confidence }
```

---

## **Diagrama de Secuencia Completo**

```
Frontend    Backend-Bank    API-Biométrica    Database
   │             │                │               │
   │──login──────>│                │               │
   │<─token──────┤                │               │
   │             │                │               │
   │──enrollment->│                │               │
   │             │──auth(admin)──>│               │
   │             │<──JWT token────┤               │
   │             │                │               │
   │             │──POST start────>│               │
   │             │<──enrollment_id┤──create──────>│
   │<──phrases───┤                │               │
   │             │                │               │
   │──audio#1───>│──add-sample───>│──extract─────>│
   │<──continue──┤<──sample_id────┤<──store──────┤
   │             │                │               │
   │──audio#2───>│──add-sample───>│──extract─────>│
   │<──continue──┤<──sample_id────┤<──store──────┤
   │             │                │               │
   │──audio#3───>│──add-sample───>│──extract─────>│
   │<──complete──┤<──is_complete──┤<──store──────┤
   │             │                │               │
   │             │──complete──────>│──create─────>│
   │             │<──voiceprint───┤<──voiceprint┤
   │<──success───┤                │               │
```

---

## **Contacto y Soporte**

Para más información:
- Documentación API: `/docs/API_ENDPOINTS_DOCUMENTATION.md`
- Arquitectura del sistema: `/docs/arquitectura/`
- Issues: Reportar en el repositorio del proyecto

---

**Última actualización:** Enero 2026  
**Versión:** 1.0.0
