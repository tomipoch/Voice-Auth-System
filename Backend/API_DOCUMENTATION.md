# 📚 Documentación de la API - Voice Biometrics

## Información General

**Base URL**: `http://localhost:8000`  
**Versión**: 1.0.0  
**Autenticación**: JWT Bearer Token (para endpoints protegidos)

## 📑 Tabla de Contenidos

1. [Autenticación](#autenticación)
2. [Gestión de Frases](#gestión-de-frases)
3. [Administración](#administración)
4. [Challenges](#challenges)
5. [Health Check](#health-check)
6. [Códigos de Error](#códigos-de-error)

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

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@voicebio.com",
    "password": "SuperAdmin2024!"
  }'
```

**Ejemplo JavaScript**:
```javascript
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'superadmin@voicebio.com',
    password: 'SuperAdmin2024!'
  })
});

const data = await response.json();
const token = data.access_token;
```

**Usuarios de Prueba**:
| Email | Password | Rol |
|-------|----------|-----|
| superadmin@voicebio.com | SuperAdmin2024! | SuperAdmin |
| admin@empresa.com | AdminEmpresa2024! | Admin |
| user@empresa.com | User2024! | User |

---

### Register

Registra un nuevo usuario en el sistema.

**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
  "email": "nuevo@empresa.com",
  "password": "Password123!",
  "full_name": "Nuevo Usuario",
  "role": "user"
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid-generado",
  "email": "nuevo@empresa.com",
  "full_name": "Nuevo Usuario",
  "role": "user",
  "created_at": "2025-11-20T19:00:00Z"
}
```

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@empresa.com",
    "password": "Password123!",
    "full_name": "Nuevo Usuario"
  }'
```

---

## 📝 Gestión de Frases

Todos los endpoints de frases requieren autenticación.

**Header requerido**:
```
Authorization: Bearer {token}
```

### Obtener Frases Aleatorias

Obtiene frases aleatorias para enrollment o verificación.

**Endpoint**: `GET /api/phrases/random`

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| count | integer | No | 1 | Cantidad de frases (1-10) |
| difficulty | string | No | - | Dificultad: easy, medium, hard |
| language | string | No | es | Idioma de las frases |
| user_id | uuid | No | - | ID del usuario (evita frases recientes) |

**Response**: `200 OK`
```json
[
  {
    "id": "6a1fb31f-a7d8-49d9-b7d4-23d55c0e12dd",
    "text": "El cielo estaba despejado y las estrellas brillaban con intensidad",
    "source": "las-aventuras-de-tom-sawyer",
    "word_count": 11,
    "char_count": 68,
    "language": "es",
    "difficulty": "medium",
    "is_active": true,
    "created_at": "2025-11-20T19:43:55.800069+00:00"
  }
]
```

**Ejemplos**:

```bash
# Obtener 3 frases fáciles
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/random?count=3&difficulty=easy"

# Obtener 5 frases medias para un usuario específico
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/random?count=5&difficulty=medium&user_id=uuid-del-usuario"

# Obtener 1 frase difícil
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/random?difficulty=hard"
```

**Ejemplo JavaScript**:
```javascript
async function getRandomPhrases(token, count = 3, difficulty = 'medium') {
  const response = await fetch(
    `http://localhost:8000/api/phrases/random?count=${count}&difficulty=${difficulty}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return await response.json();
}

// Uso
const phrases = await getRandomPhrases(token, 5, 'easy');
console.log(phrases);
```

---

### Estadísticas de Frases

Obtiene estadísticas agrupadas por dificultad.

**Endpoint**: `GET /api/phrases/stats`

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| language | string | No | es | Idioma |

**Response**: `200 OK`
```json
{
  "total": 43459,
  "by_difficulty": {
    "easy": 6637,
    "medium": 25063,
    "hard": 11759
  },
  "language": "es"
}
```

**Ejemplo cURL**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/phrases/stats
```

**Ejemplo Python**:
```python
import requests

def get_phrase_stats(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        'http://localhost:8000/api/phrases/stats',
        headers=headers
    )
    return response.json()

stats = get_phrase_stats(token)
print(f"Total frases: {stats['total']}")
print(f"Frases fáciles: {stats['by_difficulty']['easy']}")
```

---

### Listar Frases

Lista frases activas con filtros opcionales.

**Endpoint**: `GET /api/phrases/list`

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| difficulty | string | No | - | Filtrar por dificultad |
| language | string | No | es | Idioma |
| limit | integer | No | 20 | Máximo de resultados (1-100) |
| offset | integer | No | 0 | Offset para paginación |

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "text": "Texto de la frase",
      "source": "nombre-del-libro",
      "difficulty": "medium",
      "word_count": 15,
      "char_count": 85
    }
  ],
  "total": 43459,
  "limit": 20,
  "offset": 0
}
```

**Ejemplos**:
```bash
# Listar primeras 10 frases fáciles
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/list?difficulty=easy&limit=10"

# Paginación: obtener segunda página de frases medias
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/list?difficulty=medium&limit=20&offset=20"

# Listar todas las frases (máximo 100)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/phrases/list?limit=100"
```

---

### Obtener Frase por ID

Obtiene una frase específica por su ID.

**Endpoint**: `GET /api/phrases/{phrase_id}`

**Path Parameters**:
- `phrase_id`: UUID de la frase

**Response**: `200 OK`
```json
{
  "id": "6a1fb31f-a7d8-49d9-b7d4-23d55c0e12dd",
  "text": "El cielo estaba despejado...",
  "source": "las-aventuras-de-tom-sawyer",
  "word_count": 11,
  "char_count": 68,
  "language": "es",
  "difficulty": "medium",
  "is_active": true,
  "created_at": "2025-11-20T19:43:55.800069+00:00"
}
```

**Error**: `404 Not Found`
```json
{
  "detail": "Frase no encontrada"
}
```

**Ejemplo cURL**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/phrases/6a1fb31f-a7d8-49d9-b7d4-23d55c0e12dd
```

---

### Registrar Uso de Frase

Registra que un usuario utilizó una frase (para enrollment o verificación).

**Endpoint**: `POST /api/phrases/{phrase_id}/record-usage`

**Path Parameters**:
- `phrase_id`: UUID de la frase

**Request Body**:
```json
{
  "user_id": "uuid-del-usuario",
  "used_for": "enrollment"
}
```

**Valores válidos para `used_for`**:
- `enrollment` - Usado en proceso de enrolamiento
- `verification` - Usado en proceso de verificación

**Response**: `201 Created`
```json
{
  "id": "uuid-del-registro",
  "phrase_id": "uuid-de-la-frase",
  "user_id": "uuid-del-usuario",
  "used_for": "enrollment",
  "used_at": "2025-11-20T20:00:00Z"
}
```

**Ejemplo cURL**:
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-del-usuario",
    "used_for": "enrollment"
  }' \
  http://localhost:8000/api/phrases/6a1fb31f-a7d8-49d9-b7d4-23d55c0e12dd/record-usage
```

**Ejemplo JavaScript**:
```javascript
async function recordPhraseUsage(token, phraseId, userId, usedFor) {
  const response = await fetch(
    `http://localhost:8000/api/phrases/${phraseId}/record-usage`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        used_for: usedFor
      })
    }
  );
  
  return await response.json();
}

// Uso
await recordPhraseUsage(token, phraseId, userId, 'enrollment');
```

---

### Actualizar Estado de Frase

Activa o desactiva una frase (solo administradores).

**Endpoint**: `PATCH /api/phrases/{phrase_id}/status`

**Path Parameters**:
- `phrase_id`: UUID de la frase

**Request Body**:
```json
{
  "is_active": false
}
```

**Response**: `200 OK`
```json
{
  "id": "uuid-de-la-frase",
  "is_active": false,
  "updated_at": "2025-11-20T20:00:00Z"
}
```

**Ejemplo cURL**:
```bash
# Desactivar una frase
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}' \
  http://localhost:8000/api/phrases/uuid-de-la-frase/status

# Reactivar una frase
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}' \
  http://localhost:8000/api/phrases/uuid-de-la-frase/status
```

---

### Eliminar Frase

Elimina una frase del sistema (solo administradores).

**Endpoint**: `DELETE /api/phrases/{phrase_id}`

**Path Parameters**:
- `phrase_id`: UUID de la frase

**Response**: `204 No Content`

**Error**: `404 Not Found`
```json
{
  "detail": "Frase no encontrada"
}
```

**Ejemplo cURL**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/phrases/uuid-de-la-frase
```

---

## 👥 Administración

### Estadísticas del Sistema

Obtiene estadísticas generales del sistema (solo administradores).

**Endpoint**: `GET /api/admin/stats`

**Response**: `200 OK`
```json
{
  "total_users": 150,
  "active_users": 142,
  "total_enrollments": 145,
  "total_verifications": 1234,
  "success_rate": 0.92,
  "phrases": {
    "total": 43459,
    "by_difficulty": {
      "easy": 6637,
      "medium": 25063,
      "hard": 11759
    }
  }
}
```

**Ejemplo cURL**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/stats
```

---

### Listar Usuarios

Lista todos los usuarios del sistema (solo administradores).

**Endpoint**: `GET /api/admin/users`

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| limit | integer | No | 50 | Máximo de resultados |
| offset | integer | No | 0 | Offset para paginación |
| role | string | No | - | Filtrar por rol |

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@empresa.com",
      "full_name": "Usuario Ejemplo",
      "role": "user",
      "is_active": true,
      "has_voiceprint": true,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Ejemplo cURL**:
```bash
# Listar todos los usuarios
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users

# Filtrar solo administradores
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/admin/users?role=admin"
```

---

## 🎯 Challenges

### Obtener Challenge Activo

Obtiene un challenge activo para un usuario.

**Endpoint**: `GET /api/challenges/{user_id}/active`

**Path Parameters**:
- `user_id`: UUID del usuario

**Response**: `200 OK`
```json
{
  "id": "uuid-del-challenge",
  "user_id": "uuid-del-usuario",
  "phrase": {
    "id": "uuid-de-la-frase",
    "text": "Texto que el usuario debe leer"
  },
  "expires_at": "2025-11-20T20:05:00Z",
  "is_used": false
}
```

**Error**: `404 Not Found`
```json
{
  "detail": "No hay challenge activo"
}
```

**Ejemplo cURL**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/challenges/uuid-del-usuario/active
```

---

## ❤️ Health Check

Verifica el estado del servidor.

**Endpoint**: `GET /health`

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "voice-biometrics-api",
  "version": "1.0.0"
}
```

**Ejemplo cURL**:
```bash
curl http://localhost:8000/health
```

**No requiere autenticación**.

---

## ⚠️ Códigos de Error

### Errores Comunes

| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 400 | Bad Request | Datos de entrada inválidos |
| 401 | Unauthorized | Token inválido o expirado |
| 403 | Forbidden | Sin permisos para esta acción |
| 404 | Not Found | Recurso no encontrado |
| 422 | Unprocessable Entity | Validación fallida |
| 500 | Internal Server Error | Error del servidor |

### Formato de Error

```json
{
  "detail": "Descripción del error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-11-20T20:00:00Z"
}
```

### Errores de Validación (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 📊 Rate Limiting

Todos los endpoints tienen límites de tasa:

- **Endpoints públicos**: 100 requests/hora
- **Endpoints autenticados**: 1000 requests/hora
- **Admin endpoints**: 500 requests/hora

**Headers de respuesta**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1700000000
```

---

## 🔄 Flujos de Trabajo Típicos

### Flujo de Enrollment

```javascript
// 1. Login del usuario
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token, user } = await loginResponse.json();

// 2. Obtener frases para enrollment (3 frases medias)
const phrasesResponse = await fetch(
  '/api/phrases/random?count=3&difficulty=medium',
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);
const phrases = await phrasesResponse.json();

// 3. Para cada frase, grabar audio y registrar uso
for (const phrase of phrases) {
  // Usuario graba audio leyendo phrase.text
  const audioBlob = await recordAudio(phrase.text);
  
  // Registrar uso de la frase
  await fetch(`/api/phrases/${phrase.id}/record-usage`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: user.id,
      used_for: 'enrollment'
    })
  });
  
  // Enviar audio para enrollment (endpoint no implementado aún)
  // await enrollVoice(audioBlob, phrase.id);
}
```

### Flujo de Verificación

```javascript
// 1. Login
const { access_token, user } = await login(email, password);

// 2. Obtener 1 frase para verificación
const [phrase] = await fetch(
  `/api/phrases/random?count=1&difficulty=medium&user_id=${user.id}`,
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
).then(r => r.json());

// 3. Usuario graba audio
const audioBlob = await recordAudio(phrase.text);

// 4. Registrar uso
await fetch(`/api/phrases/${phrase.id}/record-usage`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: user.id,
    used_for: 'verification'
  })
});

// 5. Verificar voz (endpoint no implementado aún)
// const result = await verifyVoice(audioBlob, phrase.id);
```

---

## 📮 Postman Collection

Importa la colección de Postman incluida en el proyecto:

1. **Archivo**: `Backend/Voice_Biometrics_API.postman_collection.json`
2. **Environment**: `Backend/Voice_Biometrics_Local.postman_environment.json`

La colección incluye:
- Todos los endpoints documentados
- Variables de entorno pre-configuradas
- Scripts de auto-captura de tokens
- Ejemplos de requests completos

---

## 🔗 Enlaces Útiles

- **Documentación Interactiva**: http://localhost:8000/docs
- **Commands Cheatsheet**: Ver archivo `COMMANDS_CHEATSHEET.md`
- **Backend README**: Ver archivo `Backend/README.md`

---

## 📞 Soporte

Para problemas o preguntas:
1. Verificar logs: `docker-compose logs -f voice_biometrics_api`
2. Consultar troubleshooting en `COMMANDS_CHEATSHEET.md`
3. Verificar estado de servicios: `docker-compose ps`
