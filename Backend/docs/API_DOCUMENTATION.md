# 📚 Documentación de la API - Voice Biometrics

## Información General

**Base URL**: `http://localhost:8000`  
**Versión**: 1.0.0  
**Autenticación**: JWT Bearer Token (para endpoints protegidos)

## 📑 Tabla de Contenidos

1. [Autenticación](#autenticación)
2. [Enrollment](#enrollment)
3. [Verification](#verification)
4. [Gestión de Frases](#gestión-de-frases)
5. [Administración](#administración)
6. [Challenges](#challenges)
7. [Health Check](#health-check)
8. [Códigos de Error](#códigos-de-error)
9. [Rate Limiting](#rate-limiting)

---

## 🔐 Autenticación

### Login

Obtiene un token JWT para autenticación.

**Endpoint**: `POST /api/auth/login`

**Request Body**:
```json
{
  "email": "superadmin@voicebio.com",
  "password": "SuperAdmin2024!"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid-del-usuario",
    "email": "superadmin@voicebio.com",
    "full_name": "Super Admin",
    "role": "superadmin"
  }
}
```

**Mecanismo de Bloqueo de Cuentas:**
- Después de 5 intentos fallidos, la cuenta se bloquea durante 15 minutos.

---

### Register

Registra un nuevo usuario en el sistema.

**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
  "name": "Nuevo Usuario",
  "email": "nuevo@empresa.com",
  "password": "Password123!"
}
```

**Response**: `200 OK`
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-generado"
}
```

---

## 🚀 Enrollment

### Iniciar Enrollment

Inicia el proceso de enrollment y obtiene las frases que el usuario debe leer.

**Endpoint**: `POST /api/v1/enrollment/start`

**Request Body**: `multipart/form-data`
- `external_ref` (string, opcional): Referencia externa del usuario.
- `user_id` (string, opcional): UUID del usuario.
- `difficulty` (string, opcional): Dificultad de las frases (easy, medium, hard). Default: `medium`.

**Response**: `200 OK`
```json
{
  "enrollment_id": "uuid-del-enrollment",
  "user_id": "uuid-del-usuario",
  "phrases": [
    {
      "id": "uuid-de-la-frase",
      "text": "Texto de la frase"
    }
  ],
  "required_samples": 3
}
```

### Añadir Muestra de Enrollment

Añade una muestra de voz al proceso de enrollment.

**Endpoint**: `POST /api/v1/enrollment/add-sample`

**Request Body**: `multipart/form-data`
- `enrollment_id` (string, requerido): ID de la sesión de enrollment.
- `phrase_id` (string, requerido): ID de la frase leída.
- `audio_file` (file, requerido): Archivo de audio.

**Response**: `200 OK`
```json
{
  "sample_id": "uuid-de-la-muestra",
  "samples_completed": 1,
  "samples_required": 3,
  "is_complete": false,
  "next_phrase": {
    "id": "uuid-de-la-siguiente-frase",
    "text": "Texto de la siguiente frase"
  }
}
```

### Completar Enrollment

Completa el proceso de enrollment y crea la huella de voz final.

**Endpoint**: `POST /api/v1/enrollment/complete`

**Request Body**: `multipart/form-data`
- `enrollment_id` (string, requerido): ID de la sesión de enrollment.

**Response**: `200 OK`
```json
{
  "voiceprint_id": "uuid-de-la-huella-de-voz",
  "user_id": "uuid-del-usuario",
  "quality_score": 0.95,
  "samples_used": 3
}
```

### Obtener Estado de Enrollment

Obtiene el estado de enrollment de un usuario.

**Endpoint**: `GET /api/v1/enrollment/status/{user_id}`

**Response**: `200 OK`
```json
{
  "status": "enrolled",
  "voiceprint_id": "uuid-de-la-huella-de-voz",
  "created_at": "2025-11-20T20:00:00Z",
  "samples_count": 3,
  "required_samples": 3,
  "phrases_used": []
}
```

---

## 🔎 Verification

### Verificar Voz

Verifica la voz de un usuario contra su huella de voz.

**Endpoint**: `POST /api/v2/verification/verify`

**Request Body**: `multipart/form-data`
- `user_id` (string, requerido): UUID del usuario.
- `audio_file` (file, requerido): Archivo de audio.

**Response**: `200 OK`
```json
{
  "is_verified": true,
  "similarity": 0.98,
  "spoof_probability": 0.01
}
```

---

## 📝 Gestión de Frases

... (sin cambios)

---

## 👥 Administración

... (sin cambios)

---

## 🎯 Challenges

... (sin cambios)

---

## ❤️ Health Check

... (sin cambios)

---

## ⚠️ Códigos de Error

El sistema utiliza un mecanismo de manejo de errores centralizado.

| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 400 | Bad Request | Datos de entrada inválidos (ej. `ValueError`). |
| 401 | Unauthorized | Token inválido o expirado. |
| 403 | Forbidden | Sin permisos para esta acción. |
| 404 | Not Found | Recurso no encontrado. |
| 422 | Unprocessable Entity | Validación fallida (FastAPI). |
| 500 | Internal Server Error | Error inesperado en el servidor. |

**Formato de Error Genérico:**
```json
{
  "detail": "Descripción del error"
}
```

---

## 📊 Rate Limiting

Todos los endpoints tienen un límite de **100 peticiones por minuto**.

**Headers de respuesta**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1700000000
```
