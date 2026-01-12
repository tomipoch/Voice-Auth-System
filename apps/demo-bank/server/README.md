# Demo Bank - Backend Server

Backend intermediario del Banco Demo que maneja autenticación local y se comunica con la API Biométrica.

## 🗄️ **Base de Datos**

El servidor utiliza **SQLite** con `better-sqlite3` para persistir datos de usuarios y sesiones.

### **Ubicación:**
```
apps/demo-bank/data/demo-bank.db
```

### **Tablas:**

#### **users**
Almacena usuarios del banco con información de mapeo biométrico.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | TEXT | ID único del usuario (PK) |
| `email` | TEXT | Email único |
| `password` | TEXT | Contraseña (plain text - solo demo) |
| `first_name` | TEXT | Nombre |
| `last_name` | TEXT | Apellido |
| `rut` | TEXT | RUT chileno único |
| `balance` | REAL | Saldo de la cuenta |
| `account_number` | TEXT | Número de cuenta único |
| `biometric_user_id` | TEXT | UUID del usuario en la API biométrica |
| `enrollment_id` | TEXT | ID de sesión de enrollment activa |
| `is_voice_enrolled` | INTEGER | 0 = no enrollado, 1 = enrollado |
| `created_at` | TEXT | Timestamp de creación |
| `updated_at` | TEXT | Timestamp de última actualización |

#### **sessions**
Gestiona tokens de sesión con expiración.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `token` | TEXT | Token de sesión (PK) |
| `user_id` | TEXT | ID del usuario (FK) |
| `created_at` | TEXT | Timestamp de creación |
| `expires_at` | TEXT | Timestamp de expiración |

#### **transactions**
Registro de transacciones (preparado para uso futuro).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | ID autoincremental (PK) |
| `user_id` | TEXT | ID del usuario (FK) |
| `type` | TEXT | Tipo de transacción |
| `amount` | REAL | Monto |
| `description` | TEXT | Descripción |
| `recipient_account` | TEXT | Cuenta destino |
| `recipient_name` | TEXT | Nombre destinatario |
| `created_at` | TEXT | Timestamp |

## 📊 **Usuarios Demo Precargados**

### **Usuario 1 - demo@banco.cl**
```
Email: demo@banco.cl
Password: demo123
RUT: 12345678-9
Balance: $1,850,420
Biometric User ID: 85504b66-b04f-48a7-a513-3af8c55f9cfb
Estado: No enrollado inicialmente
```

### **Usuario 2 - juan@banco.cl**
```
Email: juan@banco.cl
Password: juan123
RUT: 98765432-1
Balance: $850,000
Biometric User ID: a593fd09-8c2e-49a4-8823-38e77ef5fe0b
Estado: Enrollado (ya tiene voiceprint)
```

## 🔄 **Flujo de Sincronización**

### **1. Login del Usuario**
```typescript
POST /api/auth/login
Body: { email, password }

→ Verifica credenciales en SQLite
→ Crea sesión con token (expira en 24h)
→ Retorna token + datos de usuario
```

### **2. Verificar Estado de Enrollment**
```typescript
GET /api/enrollment/status
Header: Authorization Bearer <token>

→ Obtiene user.biometric_user_id de SQLite
→ Consulta GET /api/enrollment/status/{biometric_user_id} a la API
→ Si is_enrolled, actualiza is_voice_enrolled = 1 en SQLite
→ Retorna estado actualizado
```

### **3. Iniciar Enrollment**
```typescript
POST /api/enrollment/start

→ Envía user_id o external_ref a la API biométrica
→ API crea usuario automáticamente si no existe
→ Actualiza biometric_user_id y enrollment_id en SQLite
→ Retorna challenges/phrases
```

### **4. Completar Enrollment**
```typescript
POST /api/enrollment/audio (3 veces)

→ Envía audio a la API biométrica
→ Cuando is_complete = true:
   - Llama POST /api/enrollment/complete
   - Actualiza is_voice_enrolled = 1 en SQLite
   - Limpia enrollment_id
```

## 🚀 **Iniciar el Servidor**

```bash
cd apps/demo-bank
bun run server
# o
npm run server
```

El servidor iniciará en `http://localhost:3001`

## 📝 **Logs de Inicialización**

Al iniciar, verás:
```
✅ Base de datos demo-bank inicializada en: /path/to/data/demo-bank.db
Demo Bank API listening on http://localhost:3001
```

## 🔍 **Consultar la Base de Datos**

### **Usando SQLite CLI:**
```bash
sqlite3 apps/demo-bank/data/demo-bank.db

# Ver usuarios
SELECT id, email, biometric_user_id, is_voice_enrolled FROM users;

# Ver sesiones activas
SELECT token, user_id, expires_at FROM sessions;

# Ver estado de enrollment
SELECT 
  u.email, 
  u.is_voice_enrolled,
  u.biometric_user_id,
  u.enrollment_id
FROM users u;
```

## 🔧 **Mantenimiento**

### **Resetear Base de Datos:**
```bash
rm -rf apps/demo-bank/data/demo-bank.db*
bun run server
# La base de datos se recreará automáticamente
```

### **Limpiar Sesiones Expiradas:**
Las sesiones se limpian automáticamente cada hora mediante un intervalo.

## 📚 **Queries Disponibles**

El módulo `database.ts` exporta queries preparados:

```typescript
// Usuarios
userQueries.getByEmail.get(email)
userQueries.getById.get(id)
userQueries.getByBiometricId.get(biometric_user_id)
userQueries.updateBalance.run(balance, user_id)
userQueries.updateBiometricId.run(biometric_user_id, enrollment_id, user_id)
userQueries.updateEnrollmentStatus.run(is_enrolled, user_id)
userQueries.clearEnrollmentId.run(user_id)

// Sesiones
sessionQueries.create.run(token, user_id, expires_at)
sessionQueries.getByToken.get(token)
sessionQueries.delete.run(token)
sessionQueries.deleteExpired.run()

// Transacciones
transactionQueries.create.run(user_id, type, amount, description, recipient_account, recipient_name)
transactionQueries.getByUser.get(user_id)
```

## 🔐 **Seguridad**

⚠️ **IMPORTANTE**: Esta es una aplicación demo:

- Las contraseñas se almacenan en texto plano (NO usar en producción)
- Los tokens son aleatorios simples (usar JWT en producción)
- No hay rate limiting (implementar en producción)
- CORS permite localhost (configurar apropiadamente en producción)

## 📖 **Documentación Relacionada**

- [Documentación de Integración](/docs/INTEGRACION_DEMO_BANK.md)
- [Endpoints de la API Biométrica](/docs/API_ENDPOINTS_DOCUMENTATION.md)
