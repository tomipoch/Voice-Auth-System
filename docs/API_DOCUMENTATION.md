# API Documentation - Challenge System

## Tabla de Contenidos
- [Admin Endpoints](#admin-endpoints)
- [Challenge Endpoints](#challenge-endpoints)
- [Enrollment Endpoints](#enrollment-endpoints)
- [Verification Endpoints](#verification-endpoints)

---

## Admin Endpoints

### GET /api/admin/phrase-rules
Obtener todas las reglas de calidad de frases configurables.

**Autenticación**: Requiere rol `admin` o `superadmin`

**Response**:
```json
[
  {
    "id": "uuid",
    "rule_name": "min_success_rate",
    "rule_type": "threshold",
    "rule_value": 0.70,
    "is_active": true,
    "created_at": "2025-12-02T10:00:00Z",
    "updated_at": "2025-12-02T10:00:00Z"
  }
]
```

---

### PATCH /api/admin/phrase-rules/{rule_name}
Actualizar el valor de una regla específica.

**Autenticación**: Requiere rol `admin` o `superadmin`

**Path Parameters**:
- `rule_name` (string): Nombre de la regla a actualizar

**Request Body**:
```json
{
  "new_value": 0.75
}
```

**Response**:
```json
{
  "success": true,
  "rule": {
    "id": "uuid",
    "rule_name": "min_success_rate",
    "rule_value": 0.75,
    "is_active": true
  },
  "message": "Rule updated successfully"
}
```

---

### POST /api/admin/phrase-rules/{rule_name}/toggle
Activar o desactivar una regla.

**Autenticación**: Requiere rol `admin` o `superadmin`

**Path Parameters**:
- `rule_name` (string): Nombre de la regla a toggle

**Response**:
```json
{
  "success": true,
  "rule": {
    "id": "uuid",
    "rule_name": "min_success_rate",
    "is_active": false
  },
  "message": "Rule toggled successfully"
}
```

---

## Challenge Endpoints

### POST /api/challenges/create
Crear un challenge individual para un usuario.

**Autenticación**: Requerida

**Request Body**:
```json
{
  "user_id": "uuid",
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "challenge_id": "uuid",
  "phrase": "El cielo está despejado hoy",
  "phrase_id": "uuid",
  "difficulty": "medium",
  "expires_at": "2025-12-02T10:05:00Z",
  "expires_in_seconds": 300
}
```

---

### POST /api/challenges/create-batch
Crear múltiples challenges en una sola operación (optimizado).

**Autenticación**: Requerida

**Request Body**:
```json
{
  "user_id": "uuid",
  "count": 5,
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "challenges": [
    {
      "challenge_id": "uuid",
      "phrase": "El cielo está despejado hoy",
      "phrase_id": "uuid",
      "difficulty": "medium",
      "expires_at": "2025-12-02T10:05:00Z",
      "expires_in_seconds": 300
    }
  ]
}
```

---

### POST /api/challenges/validate
Validar un challenge antes de usarlo.

**Autenticación**: Requerida

**Request Body**:
```json
{
  "challenge_id": "uuid",
  "user_id": "uuid"
}
```

**Response**:
```json
{
  "is_valid": true,
  "reason": "Valid"
}
```

**Posibles razones de invalidez**:
- "Challenge not found"
- "Challenge does not belong to user"
- "Challenge already used"
- "Challenge expired"

---

## Enrollment Endpoints

### POST /api/enrollment/start
Iniciar proceso de enrollment con challenges.

**Autenticación**: Requerida

**Request Body** (multipart/form-data):
- `external_ref` (optional): Referencia externa del usuario
- `user_id` (optional): ID del usuario
- `difficulty` (optional): Dificultad de las frases (easy/medium/hard)

**Response**:
```json
{
  "success": true,
  "enrollment_id": "uuid",
  "user_id": "uuid",
  "challenges": [
    {
      "challenge_id": "uuid",
      "phrase": "El cielo está despejado hoy",
      "phrase_id": "uuid",
      "difficulty": "medium",
      "expires_at": "2025-12-02T10:05:00Z",
      "expires_in_seconds": 300
    }
  ],
  "required_samples": 5,
  "message": "Enrollment started successfully"
}
```

---

### POST /api/enrollment/add-sample
Agregar una muestra de voz con su challenge correspondiente.

**Autenticación**: Requerida

**Request Body** (multipart/form-data):
- `enrollment_id` (string): ID del enrollment
- `challenge_id` (string): ID del challenge
- `audio_file` (file): Archivo de audio WAV

**Response**:
```json
{
  "success": true,
  "sample_id": "uuid",
  "samples_completed": 1,
  "samples_required": 5,
  "is_complete": false,
  "next_challenge": {
    "challenge_id": "uuid",
    "phrase": "La lluvia cae suavemente",
    "phrase_id": "uuid",
    "difficulty": "medium",
    "expires_at": "2025-12-02T10:05:00Z",
    "expires_in_seconds": 300
  },
  "quality_score": 0.85,
  "message": "Sample added successfully"
}
```

---

### POST /api/enrollment/complete
Completar el proceso de enrollment y crear voiceprint.

**Autenticación**: Requerida

**Request Body** (multipart/form-data):
- `enrollment_id` (string): ID del enrollment
- `speaker_model_id` (optional): ID del modelo de speaker

**Response**:
```json
{
  "success": true,
  "voiceprint_id": "uuid",
  "user_id": "uuid",
  "enrollment_quality": 0.87,
  "samples_used": 5,
  "message": "Enrollment completed successfully"
}
```

---

## Verification Endpoints

### POST /api/verification/start
Iniciar proceso de verificación con un challenge.

**Autenticación**: Requerida

**Request Body**:
```json
{
  "user_id": "uuid",
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "success": true,
  "verification_id": "uuid",
  "user_id": "uuid",
  "challenge_id": "uuid",
  "phrase": "El cielo está despejado hoy",
  "phrase_id": "uuid",
  "expires_at": "2025-12-02T10:05:00Z",
  "message": "Verification started successfully"
}
```

---

### POST /api/verification/verify
Verificar la voz del usuario con el challenge.

**Autenticación**: Requerida

**Request Body** (multipart/form-data):
- `verification_id` (string): ID de la verificación
- `challenge_id` (string): ID del challenge
- `audio_file` (file): Archivo de audio WAV

**Response**:
```json
{
  "verification_id": "uuid",
  "user_id": "uuid",
  "is_verified": true,
  "confidence_score": 0.89,
  "similarity_score": 0.91,
  "anti_spoofing_score": 0.15,
  "phrase_match": true,
  "is_live": true,
  "threshold_used": 0.60
}
```

---

### POST /api/verification/start-multi
Iniciar verificación multi-frase (3 challenges).

**Autenticación**: Requerida

**Request Body**:
```json
{
  "user_id": "uuid",
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "verification_id": "uuid",
  "user_id": "uuid",
  "challenges": [
    {
      "challenge_id": "uuid",
      "phrase": "El cielo está despejado hoy",
      "phrase_id": "uuid",
      "difficulty": "medium",
      "expires_at": "2025-12-02T10:05:00Z",
      "expires_in_seconds": 300
    }
  ],
  "total_phrases": 3
}
```

---

### POST /api/verification/verify-phrase
Verificar una frase individual en verificación multi-frase.

**Autenticación**: Requerida

**Request Body** (multipart/form-data):
- `verification_id` (string): ID de la verificación
- `challenge_id` (string): ID del challenge
- `phrase_number` (int): Número de la frase (1, 2, o 3)
- `audio_file` (file): Archivo de audio WAV

**Response**:
```json
{
  "phrase_number": 1,
  "individual_score": 0.89,
  "is_complete": false,
  "phrases_remaining": 2
}
```

**Response (última frase)**:
```json
{
  "phrase_number": 3,
  "individual_score": 0.87,
  "is_complete": true,
  "average_score": 0.88,
  "is_verified": true,
  "threshold_used": 0.60,
  "all_results": [
    {
      "phrase_number": 1,
      "challenge_id": "uuid",
      "similarity_score": 0.89,
      "asr_confidence": 0.95,
      "asr_penalty": 1.0,
      "final_score": 0.89
    }
  ]
}
```

---

## Reglas de Calidad Configurables

### Thresholds
- `min_success_rate` (0.5-1.0): Tasa mínima de éxito para mantener frase activa
- `min_asr_score` (0.5-1.0): Score mínimo de reconocimiento de voz
- `min_phrase_ok_rate` (0.5-1.0): Tasa mínima de transcripción correcta
- `min_attempts_for_analysis` (5-50): Intentos mínimos antes de analizar

### Rate Limits
- `exclude_recent_phrases` (10-100): Número de frases recientes a excluir
- `max_challenges_per_user` (1-10): Máximo de challenges activos por usuario
- `max_challenges_per_hour` (5-100): Máximo de challenges por hora

### Cleanup
- `challenge_expiry_minutes` (1-60): Tiempo de expiración de challenges
- `cleanup_expired_after_hours` (1-24): Borrar expirados después de N horas
- `cleanup_used_after_hours` (1-168): Borrar usados después de N horas

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Bad Request - Parámetros inválidos |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - Sin permisos suficientes |
| 404 | Not Found - Recurso no encontrado |
| 422 | Unprocessable Entity - Validación fallida |
| 429 | Too Many Requests - Rate limit excedido |
| 500 | Internal Server Error - Error del servidor |

---

## Notas de Seguridad

1. **Challenges de uso único**: Cada challenge solo puede usarse una vez
2. **Expiración temporal**: Los challenges expiran después de 5 minutos (configurable)
3. **Rate limiting**: Límites configurables para prevenir abuso
4. **Validación estricta**: Verificación de pertenencia y estado del challenge
5. **Audit logging**: Todos los eventos son registrados para auditoría
