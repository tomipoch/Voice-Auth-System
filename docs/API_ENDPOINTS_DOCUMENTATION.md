# **Documentación Completa de Endpoints del Backend**

## **Tabla de Contenidos**
1. [Autenticación](#autenticación)
2. [Enrollment (Inscripción de Voz)](#enrollment)
3. [Verification (Verificación de Voz)](#verification)
4. [Challenges (Desafíos)](#challenges)
5. [Phrases (Frases)](#phrases)
6. [Admin](#admin)
7. [Superadmin](#superadmin)
8. [Evaluation](#evaluation)
9. [Dataset Recording](#dataset-recording)

---

## **Autenticación**
**Prefijo:** `/api/auth`

### **POST** `/api/auth/login`
Autentica un usuario y devuelve un token JWT.

**Datos de entrada:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Datos de salida:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 7200,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "role": "user",
    "company": "Company Name",
    "created_at": "2024-01-01T00:00:00Z",
    "voice_template": null,
    "settings": {}
  }
}
```

**Características:**
- Bloqueo de cuenta después de 5 intentos fallidos (15 minutos)
- Token expira en 120 minutos
- Registro de auditoría con IP del cliente
- Validación de contraseña con bcrypt

---

### **POST** `/api/auth/register`
Registra un nuevo usuario en el sistema.

**Datos de entrada:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "rut": "12345678-9",
  "company": "Mi Empresa"
}
```

**Validaciones:**
- Password: mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número
- RUT: formato chileno válido (opcional)
- Email único en el sistema

**Datos de salida:**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid"
}
```

---

### **POST** `/api/auth/refresh`
Refresca el access token usando un refresh token.

**Datos de entrada:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Datos de salida:**
```json
{
  "access_token": "nuevo_token...",
  "token_type": "bearer",
  "expires_in": 7200,
  "refresh_token": "mismo_refresh_token...",
  "user": { /* datos del usuario */ }
}
```

---

### **GET** `/api/auth/profile`
Obtiene el perfil del usuario actual.

**Headers requeridos:**
```
Authorization: Bearer <token>
```

**Datos de salida:**
```json
{
  "id": "uuid",
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "role": "user",
  "company": "Company Name",
  "rut": "12345678-9",
  "created_at": "2024-01-01T00:00:00Z",
  "voice_template": null,
  "settings": {}
}
```

---

### **PATCH** `/api/auth/profile`
Actualiza el perfil del usuario.

**Datos de entrada:**
```json
{
  "first_name": "John",
  "last_name": "Doe Updated",
  "rut": "98765432-1",
  "settings": {
    "notifications": true,
    "language": "es"
  }
}
```

**Datos de salida:**
Perfil actualizado completo.

---

### **POST** `/api/auth/change-password`
Cambia la contraseña del usuario.

**Datos de entrada:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**Datos de salida:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

### **POST** `/api/auth/logout`
Cierra sesión (principalmente para limpieza del lado del cliente).

**Datos de salida:**
```json
{
  "message": "Successfully logged out"
}
```

---

## **Enrollment**
**Prefijo:** `/api/enrollment`

### **POST** `/api/enrollment/start`
Inicia el proceso de inscripción de voz y obtiene frases para leer.

**Datos de entrada (Form Data):**
- `user_id` (opcional): UUID del usuario
- `external_ref` (opcional): Referencia externa
- `difficulty`: "easy" | "medium" | "hard" (default: "medium")
- `force_overwrite`: boolean (default: false)

**Datos de salida:**
```json
{
  "success": true,
  "enrollment_id": "uuid",
  "user_id": "uuid",
  "challenges": [
    {
      "id": "uuid",
      "text": "El sol brilla con intensidad en el cielo azul",
      "difficulty": "medium"
    },
    {
      "id": "uuid",
      "text": "Las estrellas iluminan la noche oscura",
      "difficulty": "medium"
    },
    {
      "id": "uuid",
      "text": "El viento sopla suavemente entre los árboles",
      "difficulty": "medium"
    }
  ],
  "required_samples": 3,
  "message": "Enrollment started successfully",
  "voiceprint_exists": false
}
```

---

### **POST** `/api/enrollment/add-sample`
Agrega una muestra de audio al proceso de inscripción.

**Datos de entrada (Form Data):**
- `enrollment_id`: UUID de la sesión
- `challenge_id`: UUID del challenge/frase leída
- `audio_file`: Archivo de audio (WAV, MP3, FLAC, WebM)

**Validaciones:**
- Calidad de audio (SNR, duración)
- Formato de audio válido

**Datos de salida:**
```json
{
  "success": true,
  "sample_id": "uuid",
  "samples_completed": 1,
  "samples_required": 3,
  "is_complete": false,
  "next_phrase": {
    "id": "uuid",
    "text": "Siguiente frase para leer..."
  },
  "message": "Sample added successfully"
}
```

**Características:**
- Conversión automática a WAV
- Extracción de embedding vocal
- Guardado automático para dataset
- Validación de calidad de audio

---

### **POST** `/api/enrollment/complete`
Completa el proceso de inscripción y crea la huella vocal final.

**Datos de entrada (Form Data):**
- `enrollment_id`: UUID de la sesión
- `speaker_model_id` (opcional): ID del modelo de speaker

**Datos de salida:**
```json
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

### **GET** `/api/enrollment/status/{user_id}`
Obtiene el estado de inscripción de un usuario.

**Datos de salida:**
```json
{
  "is_enrolled": true,
  "enrollment_date": "2024-01-01T00:00:00Z",
  "samples_count": 3,
  "quality_score": 0.95
}
```

---

## **Verification**
**Prefijo:** `/api/verification`

### **POST** `/api/verification/start`
Inicia el proceso de verificación y obtiene una frase.

**Datos de entrada:**
```json
{
  "user_id": "uuid",
  "difficulty": "medium"
}
```

**Datos de salida:**
```json
{
  "success": true,
  "verification_id": "uuid",
  "user_id": "uuid",
  "phrase": {
    "id": "uuid",
    "text": "Frase para verificación..."
  },
  "message": "Verification started successfully"
}
```

---

### **POST** `/api/verification/verify`
Verifica la voz con validación de frase.

**Datos de entrada (Form Data):**
- `verification_id`: UUID de la sesión
- `phrase_id`: UUID de la frase leída
- `audio_file`: Archivo de audio

**Datos de salida:**
```json
{
  "verification_id": "uuid",
  "user_id": "uuid",
  "is_verified": true,
  "confidence_score": 0.92,
  "similarity_score": 0.88,
  "anti_spoofing_score": 0.95,
  "phrase_match": true,
  "is_live": true,
  "threshold_used": 0.75
}
```

**Características:**
- Extracción de embedding
- Anti-spoofing detection
- Transcripción automática (ASR)
- Validación de frase
- Guardado para dataset

---

### **POST** `/api/verification/quick-verify`
Verificación rápida sin gestión de frases.

**Datos de entrada (Form Data):**
- `user_id`: UUID del usuario
- `audio_file`: Archivo de audio

**Datos de salida:**
```json
{
  "verification_id": null,
  "user_id": "uuid",
  "is_verified": true,
  "confidence_score": 0.90,
  "similarity_score": 0.86,
  "anti_spoofing_score": 0.93,
  "phrase_match": null,
  "is_live": true,
  "threshold_used": 0.75
}
```

---

### **POST** `/api/verification/start-multi`
Inicia verificación multi-frase (3 frases).

**Datos de entrada:**
```json
{
  "user_id": "uuid",
  "difficulty": "medium"
}
```

**Datos de salida:**
```json
{
  "success": true,
  "verification_id": "uuid",
  "user_id": "uuid",
  "phrases": [
    {"id": "uuid", "text": "Frase 1..."},
    {"id": "uuid", "text": "Frase 2..."},
    {"id": "uuid", "text": "Frase 3..."}
  ],
  "message": "Multi-phrase verification started"
}
```

---

### **POST** `/api/verification/verify-phrase`
Verifica una frase individual en verificación multi-frase.

**Datos de entrada (Form Data):**
- `verification_id`: UUID
- `phrase_id`: UUID
- `phrase_number`: 1, 2, o 3
- `audio_file`: Archivo de audio
- `user_agent` (opcional): Información del navegador
- `device_info` (opcional): Información del dispositivo

**Datos de salida (no completo):**
```json
{
  "phrase_number": 1,
  "is_verified": true,
  "similarity_score": 0.88,
  "is_complete": false,
  "phrases_completed": 1,
  "phrases_required": 3
}
```

**Datos de salida (completo - 3 frases):**
```json
{
  "is_complete": true,
  "is_verified": true,
  "average_score": 0.89,
  "all_results": [
    {"phrase": 1, "score": 0.88, "verified": true},
    {"phrase": 2, "score": 0.90, "verified": true},
    {"phrase": 3, "score": 0.89, "verified": true}
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Características:**
- Procesamiento paralelo de features
- Registro de auditoría completo con IP, user agent, device info
- Guardado automático para dataset

---

### **GET** `/api/verification/user/{user_id}/history`
Obtiene el historial de verificaciones de un usuario.

**Query Parameters:**
- `limit`: número de resultados (default: 100)

**Datos de salida:**
```json
{
  "success": true,
  "history": [
    {
      "verification_id": "uuid",
      "timestamp": "2024-01-01T00:00:00Z",
      "is_verified": true,
      "confidence_score": 0.92,
      "method": "multi_phrase"
    }
  ]
}
```

---

## **Challenges**
**Prefijo:** `/api/challenges`

### **POST** `/api/challenges/create`
Crea un nuevo desafío de voz para un usuario.

**Datos de entrada (Form Data):**
- `user_id`: UUID
- `difficulty` (opcional): "easy" | "medium" | "hard"

**Datos de salida:**
```json
{
  "success": true,
  "challenge": {
    "id": "uuid",
    "user_id": "uuid",
    "phrase_id": "uuid",
    "phrase_text": "Texto de la frase...",
    "difficulty": "medium",
    "expires_at": "2024-01-01T00:10:00Z"
  },
  "message": "Challenge created successfully"
}
```

---

### **POST** `/api/challenges/create-batch`
Crea múltiples desafíos a la vez (optimizado).

**Datos de entrada (Form Data):**
- `user_id`: UUID
- `count`: número de challenges (default: 3)
- `difficulty` (opcional): nivel de dificultad

**Datos de salida:**
```json
{
  "success": true,
  "challenges": [ /* array de challenges */ ],
  "count": 3,
  "message": "Created 3 challenges successfully"
}
```

---

### **GET** `/api/challenges/{challenge_id}`
Obtiene detalles de un challenge específico.

**Datos de salida:**
```json
{
  "success": true,
  "challenge": {
    "id": "uuid",
    "user_id": "uuid",
    "phrase_id": "uuid",
    "phrase_text": "...",
    "difficulty": "medium",
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T00:10:00Z"
  }
}
```

---

### **GET** `/api/challenges/user/{user_id}/active`
Obtiene el challenge activo más reciente de un usuario.

**Datos de salida:**
```json
{
  "success": true,
  "challenge": { /* datos del challenge */ }
}
```

---

### **POST** `/api/challenges/validate`
Valida un challenge (validación estricta).

**Datos de entrada (Form Data):**
- `challenge_id`: UUID
- `user_id`: UUID

**Datos de salida:**
```json
{
  "success": true,
  "is_valid": true,
  "reason": "Challenge is valid"
}
```

---

### **GET** `/api/challenges/{challenge_id}/time-remaining`
Obtiene el tiempo restante de un challenge.

**Datos de salida:**
```json
{
  "success": true,
  "expired": false,
  "seconds_remaining": 450,
  "expires_at": "2024-01-01T00:10:00Z"
}
```

---

### **POST** `/api/challenges/cleanup`
Limpia challenges expirados (endpoint admin).

**Datos de salida:**
```json
{
  "success": true,
  "deleted_count": 15,
  "message": "Cleaned up 15 expired challenges"
}
```

---

### **POST** `/api/challenges/generate-test-phrase`
Genera una frase de prueba.

**Datos de entrada (Form Data):**
- `phrase_type`: "words" | "numbers" | "mixed"

**Datos de salida:**
```json
{
  "success": true,
  "phrase": "Texto generado...",
  "phrase_type": "mixed"
}
```

---

## **Phrases**
**Prefijo:** `/api/phrases`

### **GET** `/api/phrases/books`
Obtiene lista de libros (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Datos de salida:**
```json
[
  {
    "id": "uuid",
    "title": "El Quijote",
    "author": "Miguel de Cervantes"
  }
]
```

---

### **GET** `/api/phrases/stats`
Obtiene estadísticas de frases (admin only).

**Query Parameters:**
- `language`: código de idioma (default: "es")

**Datos de salida:**
```json
{
  "total": 1500,
  "active": 1200,
  "inactive": 300,
  "easy": 500,
  "medium": 700,
  "hard": 300,
  "language": "es"
}
```

---

### **GET** `/api/phrases/list`
Lista paginada de frases con filtros (admin only).

**Query Parameters:**
- `page`: número de página (default: 1)
- `limit`: elementos por página (default: 50, max: 100)
- `difficulty`: filtrar por dificultad
- `is_active`: filtrar por estado activo
- `search`: búsqueda en texto
- `book_id`: filtrar por libro
- `author`: filtrar por autor

**Datos de salida:**
```json
{
  "phrases": [
    {
      "id": "uuid",
      "text": "Texto de la frase...",
      "source": "libro",
      "book_title": "El Quijote",
      "book_author": "Cervantes",
      "word_count": 15,
      "char_count": 85,
      "language": "es",
      "difficulty": "medium",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "phoneme_score": 85,
      "style": "narrative"
    }
  ],
  "total": 1500,
  "page": 1,
  "limit": 50,
  "total_pages": 30
}
```

---

### **GET** `/api/phrases/random`
Obtiene frases aleatorias (público).

**Query Parameters:**
- `count`: número de frases (default: 1, max: 10)
- `difficulty`: filtrar por dificultad
- `language`: idioma (default: "es")

**Datos de salida:**
```json
[
  {
    "id": "uuid",
    "text": "Frase aleatoria...",
    "source": "libro",
    "word_count": 12,
    "char_count": 70,
    "language": "es",
    "difficulty": "medium",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### **PATCH** `/api/phrases/{phrase_id}/status`
Actualiza el estado activo de una frase (admin only).

**Datos de entrada:**
```json
{
  "is_active": false
}
```

**Datos de salida:**
```json
{
  "success": true,
  "message": "Phrase deactivated successfully",
  "phrase_id": "uuid",
  "is_active": false
}
```

---

### **DELETE** `/api/phrases/{phrase_id}`
Elimina una frase (admin only).

**Datos de salida:**
```json
{
  "success": true,
  "message": "Phrase deleted successfully",
  "phrase_id": "uuid"
}
```

---

### **PUT** `/api/phrases/{phrase_id}`
Actualiza el texto de una frase (admin only).

**Datos de entrada:**
```json
{
  "text": "Nuevo texto de la frase..."
}
```

**Validaciones:**
- Mínimo 20 caracteres
- Máximo 500 caracteres

**Datos de salida:**
```json
{
  "success": true,
  "message": "Phrase updated successfully",
  "phrase_id": "uuid",
  "text": "Nuevo texto...",
  "word_count": 15,
  "char_count": 85
}
```

---

## **Admin**
**Prefijo:** `/api/admin`
**Requiere:** Rol admin o superadmin

### **GET** `/api/admin/users`
Lista paginada de usuarios.

**Query Parameters:**
- `page`: número de página (default: 1)
- `limit`: elementos por página (default: 10)

**Permisos:**
- **Admin:** solo ve usuarios regulares de su empresa
- **Superadmin:** ve todos los usuarios

**Datos de salida:**
```json
{
  "users": [
    {
      "id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email": "user@example.com",
      "role": "user",
      "company": "Company Name",
      "status": "active",
      "enrollment_status": "enrolled",
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-15T10:30:00Z",
      "voice_template": null
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 10,
  "total_pages": 5
}
```

---

### **GET** `/api/admin/users/{user_id}`
Detalles completos de un usuario.

**Permisos:**
- **Admin:** solo usuarios de su empresa
- **Superadmin:** cualquier usuario

**Datos de salida:**
```json
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "role": "user",
  "company": "Company Name",
  "status": "active",
  "enrollment_status": "enrolled",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "voice_template": {
    "id": "uuid",
    "created_at": "2024-01-10T00:00:00Z",
    "model_type": "ECAPA-TDNN",
    "sample_count": 3
  }
}
```

---

### **GET** `/api/admin/stats`
Estadísticas del sistema.

**Permisos:**
- **Admin:** estadísticas de su empresa
- **Superadmin:** estadísticas globales

**Datos de salida:**
```json
{
  "total_users": 150,
  "total_enrollments": 120,
  "total_verifications": 2500,
  "success_rate": 0.95,
  "active_users_24h": 45,
  "failed_verifications_24h": 12,
  "daily_verifications": [
    {"date": "2024-01-01", "count": 350},
    {"date": "2024-01-02", "count": 380}
  ]
}
```

---

### **GET** `/api/admin/activity`
Logs de actividad reciente.

**Query Parameters:**
- `limit`: número de logs (default: 100)
- `action`: filtrar por acción específica

**Permisos:**
- **Admin:** solo logs de su empresa
- **Superadmin:** todos los logs

**Datos de salida:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "user_name": "user@example.com",
    "action": "VERIFICATION",
    "timestamp": "2024-01-01T00:00:00Z",
    "details": "User verified successfully"
  }
]
```

---

### **DELETE** `/api/admin/users/{user_id}`
Elimina un usuario.

**Restricción:** No puedes eliminar tu propia cuenta.

**Datos de salida:**
```json
{
  "message": "User deleted successfully"
}
```

---

### **PATCH** `/api/admin/users/{user_id}`
Actualiza datos de un usuario.

**Datos de entrada:**
```json
{
  "first_name": "Updated Name",
  "role": "admin",
  "status": "active"
}
```

**Datos de salida:**
```json
{
  "message": "User updated successfully"
}
```

---

### **GET** `/api/admin/phrase-rules`
Obtiene reglas de calidad de frases.

**Query Parameters:**
- `include_inactive`: incluir reglas inactivas (default: false)

**Datos de salida:**
```json
[
  {
    "id": "uuid",
    "rule_name": "min_word_count",
    "rule_type": "threshold",
    "rule_value": 10.0,
    "description": "Minimum word count for phrases",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### **PATCH** `/api/admin/phrase-rules/{rule_name}`
Actualiza el valor de una regla.

**Datos de entrada:**
```json
{
  "value": 15.0
}
```

**Datos de salida:**
```json
{
  "success": true,
  "message": "Rule updated successfully",
  "rule_name": "min_word_count",
  "new_value": 15.0
}
```

---

## **Superadmin**
**Prefijo:** `/api/superadmin`
**Requiere:** Rol superadmin

### **GET** `/api/superadmin/system/health`
Estado de salud del sistema.

**Datos de salida:**
```json
{
  "api_status": "healthy",
  "api_uptime_seconds": 86400.0,
  "api_latency_ms": 45.0,
  "database_status": "healthy",
  "database_connections": 8,
  "database_max_connections": 20,
  "models_status": {
    "speaker_recognition": "loaded",
    "anti_spoofing": "loaded",
    "asr": "loaded"
  },
  "last_check": "2024-01-01T00:00:00Z"
}
```

---

### **GET** `/api/superadmin/system/metrics`
Métricas reales del sistema (CPU, memoria, disco).

**Datos de salida:**
```json
{
  "cpu_usage_percent": 45.2,
  "memory_usage_percent": 62.8,
  "memory_used_mb": 2048.5,
  "memory_total_mb": 4096.0,
  "disk_usage_percent": 35.0,
  "disk_used_gb": 15.5,
  "disk_total_gb": 50.0,
  "uptime_seconds": 86400.0,
  "load_average_1m": 1.5,
  "load_average_5m": 1.2,
  "load_average_15m": 1.0,
  "process_count": 156
}
```

---

### **GET** `/api/superadmin/stats/global`
Estadísticas globales del sistema.

**Datos de salida:**
```json
{
  "total_companies": 15,
  "total_users": 1500,
  "total_enrollments": 1200,
  "total_verifications": 25000,
  "total_verifications_30d": 5000,
  "success_rate": 0.95,
  "spoof_detection_rate": 0.02,
  "avg_latency_ms": 450.0,
  "storage_used_mb": 2500.0
}
```

---

### **GET** `/api/superadmin/stats/by-company`
Estadísticas desglosadas por empresa.

**Datos de salida:**
```json
[
  {
    "name": "Company A",
    "user_count": 150,
    "enrolled_count": 120,
    "admin_count": 3,
    "verification_count_30d": 500,
    "status": "active"
  }
]
```

---

### **GET** `/api/superadmin/companies`
Lista de empresas con estadísticas.

**Datos de salida:**
Igual que `/stats/by-company`.

---

### **GET** `/api/superadmin/audit`
Logs de auditoría globales con filtros.

**Query Parameters:**
- `limit`: número de logs (default: 100, max: 1000)
- `action`: filtrar por acción
- `company`: filtrar por empresa
- `start_date`: fecha inicio
- `end_date`: fecha fin

**Datos de salida:**
```json
[
  {
    "id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "actor": "user@example.com",
    "action": "VERIFICATION",
    "entity_type": "multi_verification_complete",
    "entity_id": "uuid",
    "company": "Company A",
    "success": true,
    "details": "Verification completed successfully"
  }
]
```

---

### **GET** `/api/superadmin/models`
Estado de los modelos biométricos.

**Datos de salida:**
```json
[
  {
    "name": "ECAPA-TDNN",
    "version": "1.0.0",
    "kind": "speaker",
    "status": "loaded",
    "load_time_ms": 1500.0
  },
  {
    "name": "RawNet2",
    "version": "1.0.0",
    "kind": "antispoof",
    "status": "loaded",
    "load_time_ms": 800.0
  },
  {
    "name": "Whisper",
    "version": "tiny",
    "kind": "asr",
    "status": "loaded",
    "load_time_ms": 2000.0
  }
]
```

---

## **Evaluation**
**Prefijo:** `/api/evaluation`

### **POST** `/api/evaluation/start-session`
Inicia una sesión de evaluación.

**Datos de entrada:**
```json
{
  "session_name": "test_session_1"
}
```

**Datos de salida:**
```json
{
  "session_id": "test_session_1_20240101_120000",
  "message": "Evaluation session started. All operations will be logged."
}
```

---

### **POST** `/api/evaluation/stop-session`
Detiene una sesión de evaluación.

**Datos de entrada (opcional):**
```json
{
  "session_id": "test_session_1_20240101_120000"
}
```

**Datos de salida:**
```json
{
  "message": "Evaluation session stopped",
  "session_id": "test_session_1_20240101_120000"
}
```

---

### **GET** `/api/evaluation/export-session/{session_id}`
Exporta datos de una sesión a JSON.

**Datos de salida:**
```json
{
  "message": "Session exported successfully",
  "session_id": "test_session_1_20240101_120000",
  "filepath": "/path/to/export.json"
}
```

---

### **GET** `/api/evaluation/sessions`
Lista todas las sesiones activas.

**Datos de salida:**
```json
[
  "test_session_1_20240101_120000",
  "test_session_2_20240102_140000"
]
```

---

### **GET** `/api/evaluation/session-summary/{session_id}`
Obtiene resumen estadístico de una sesión.

**Datos de salida:**
```json
{
  "session_id": "test_session_1_20240101_120000",
  "stats": {
    "total_enrollments": 50,
    "total_verifications": 200,
    "success_rate": 0.95,
    "avg_confidence": 0.89
  }
}
```

---

### **GET** `/api/evaluation/status`
Estado actual del sistema de evaluación.

**Datos de salida:**
```json
{
  "enabled": true,
  "current_session": "test_session_1_20240101_120000",
  "active_sessions": 2
}
```

---

## **Dataset Recording**
**Prefijo:** `/api/dataset-recording`

### **POST** `/api/dataset-recording/start`
Inicia grabación de audios para dataset.

**Datos de entrada:**
```json
{
  "session_name": "dataset_v1"
}
```

**Datos de salida:**
```json
{
  "success": true,
  "session_id": "dataset_v1_20240101_120000",
  "session_dir": "/path/to/recordings/dataset_v1_20240101_120000",
  "message": "Dataset recording started. Audios will be saved to: ..."
}
```

**Características:**
- Persiste en base de datos
- Sobrevive reinicios del servidor
- Guarda todos los audios de enrollment y verification

---

### **POST** `/api/dataset-recording/stop`
Detiene grabación de audios.

**Datos de salida:**
```json
{
  "success": true,
  "message": "Dataset recording stopped",
  "session_dir": "/path/to/recordings/dataset_v1_20240101_120000"
}
```

---

### **GET** `/api/dataset-recording/status`
Estado actual de grabación.

**Datos de salida:**
```json
{
  "enabled": true,
  "session_id": "dataset_v1_20240101_120000",
  "session_dir": "/path/to/recordings/dataset_v1_20240101_120000",
  "total_users": 25,
  "total_enrollment_audios": 75,
  "total_verification_audios": 150,
  "users": {
    "user_uuid_1": {
      "email": "user1@example.com",
      "enrollment_count": 3,
      "verification_count": 6
    }
  }
}
```

---

## **Resumen de Métodos HTTP**

| Método | Uso Principal |
|--------|---------------|
| **GET** | Obtener información, leer datos |
| **POST** | Crear recursos, ejecutar acciones |
| **PATCH** | Actualizar parcialmente un recurso |
| **PUT** | Actualizar completamente un recurso |
| **DELETE** | Eliminar un recurso |

---

## **Códigos de Estado HTTP Comunes**

| Código | Significado |
|--------|-------------|
| **200** | OK - Operación exitosa |
| **201** | Created - Recurso creado exitosamente |
| **400** | Bad Request - Datos inválidos |
| **401** | Unauthorized - Token inválido o expirado |
| **403** | Forbidden - Sin permisos |
| **404** | Not Found - Recurso no encontrado |
| **500** | Internal Server Error - Error del servidor |

---

## **Autenticación en Todos los Endpoints Protegidos**

La mayoría de endpoints requieren un token JWT en el header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Excepciones (endpoints públicos):**
- `/api/auth/login`
- `/api/auth/register`
- `/api/phrases/random`

---

## **Características Transversales**

### **Logging y Auditoría**
Todos los endpoints críticos registran:
- Actor (usuario o sistema)
- Acción realizada
- Timestamp
- IP del cliente
- User agent
- Éxito/fallo
- Metadata adicional

### **Conversión de Audio**
Los endpoints que reciben audio soportan:
- WAV
- MP3
- FLAC
- WebM (Opus)

Conversión automática a WAV para procesamiento.

### **Validación de Calidad**
Los audios se validan por:
- SNR (Signal-to-Noise Ratio)
- Duración mínima/máxima
- Formato válido
- Tasa de muestreo adecuada

### **Dataset Recording**
Cuando está activo, guarda automáticamente:
- Audios de enrollment
- Audios de verification
- Metadata asociada (email, timestamp, etc.)

Estructura:
```
evaluation/dataset/recordings/
  session_name_timestamp/
    user_uuid/
      enrollment/
        sample_1.wav
        sample_2.wav
      verification/
        verify_1.wav
        verify_2.wav
```

---

## **Flujos de Trabajo Típicos**

### **Flujo de Registro e Inscripción**

1. **Registro de usuario**
   ```
   POST /api/auth/register
   ```

2. **Login**
   ```
   POST /api/auth/login
   ```

3. **Iniciar inscripción**
   ```
   POST /api/enrollment/start
   ```

4. **Grabar y enviar 3 muestras**
   ```
   POST /api/enrollment/add-sample (3 veces)
   ```

5. **Completar inscripción**
   ```
   POST /api/enrollment/complete
   ```

### **Flujo de Verificación Simple**

1. **Login**
   ```
   POST /api/auth/login
   ```

2. **Iniciar verificación**
   ```
   POST /api/verification/start
   ```

3. **Verificar voz**
   ```
   POST /api/verification/verify
   ```

### **Flujo de Verificación Multi-Frase**

1. **Login**
   ```
   POST /api/auth/login
   ```

2. **Iniciar verificación multi-frase**
   ```
   POST /api/verification/start-multi
   ```

3. **Verificar cada frase (3 veces)**
   ```
   POST /api/verification/verify-phrase
   ```

### **Flujo de Administración**

1. **Login como admin**
   ```
   POST /api/auth/login (con credenciales de admin)
   ```

2. **Ver estadísticas**
   ```
   GET /api/admin/stats
   ```

3. **Listar usuarios**
   ```
   GET /api/admin/users?page=1&limit=10
   ```

4. **Ver actividad**
   ```
   GET /api/admin/activity?limit=50
   ```

---

## **Notas de Seguridad**

### **Validación de Tokens**
- Todos los tokens JWT se validan en cada request
- Los tokens expirados retornan 401 Unauthorized
- Usa el endpoint `/api/auth/refresh` para renovar tokens

### **Control de Acceso Basado en Roles (RBAC)**
- **user**: Acceso a endpoints básicos (enrollment, verification, profile)
- **admin**: Acceso a gestión de usuarios de su empresa + estadísticas
- **superadmin**: Acceso completo al sistema

### **Rate Limiting y Bloqueo de Cuenta**
- 5 intentos fallidos de login bloquean la cuenta por 15 minutos
- Los intentos fallidos se registran en audit logs con IP

### **Encriptación de Contraseñas**
- Todas las contraseñas se encriptan con bcrypt
- Salt automático generado por bcrypt
- Nunca se devuelven contraseñas en respuestas

### **Validación de Audio**
- Detección de anti-spoofing en todos los audios
- Validación de calidad de audio (SNR mínimo)
- Conversión segura de formatos

---

## **Troubleshooting Común**

### **Error 401: Unauthorized**
- **Causa**: Token expirado o inválido
- **Solución**: Usar `/api/auth/refresh` o hacer login nuevamente

### **Error 403: Forbidden**
- **Causa**: Usuario no tiene permisos suficientes
- **Solución**: Verificar rol del usuario y permisos del endpoint

### **Error 400: Invalid audio**
- **Causa**: Audio de baja calidad o formato no soportado
- **Solución**: Verificar formato (WAV, MP3, FLAC, WebM), duración mínima (1s), y calidad de grabación

### **Error 404: User not found**
- **Causa**: Usuario no existe o fue eliminado
- **Solución**: Verificar UUID del usuario

### **Error 400: Voiceprint already exists**
- **Causa**: Usuario ya tiene voiceprint registrado
- **Solución**: Usar `force_overwrite=true` en `/api/enrollment/start`

---

## **Límites y Quotas**

| Recurso | Límite |
|---------|--------|
| Tamaño máximo de audio | 10 MB |
| Duración máxima de audio | 30 segundos |
| Duración mínima de audio | 1 segundo |
| Intentos de login fallidos | 5 (bloqueo 15 min) |
| Token expiration | 120 minutos |
| Refresh token expiration | 7 días |
| Frases por enrollment | 3 |
| Frases por verificación multi | 3 |
| Max results en listas paginadas | 100 |

---

## **Información de Contacto y Soporte**

Para más información sobre el sistema, consultar:
- Documentación técnica completa: `/docs/arquitectura/`
- Manual de usuario: `/docs/manuales/MANUAL_DE_USUARIO.md`
- Guía de administración: `/docs/manuales/ADMIN_GUIDE.md`
- API OpenAPI Spec: `/docs/api-openapi.yaml`

---

**Última actualización:** Enero 2026
**Versión del API:** 1.0.0
