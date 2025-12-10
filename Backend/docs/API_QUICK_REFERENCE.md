# Voice Biometrics API - Quick Reference

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
```
http://localhost:8000/docs
```

---

## Quick Start

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 3. Start Enrollment
```bash
curl -X POST http://localhost:8000/api/enrollment/start \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "difficulty": "medium"
  }'
```

### 4. Start Verification
```bash
curl -X POST http://localhost:8000/api/verification/start-multi \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "difficulty": "medium"
  }'
```

---

## Endpoint Summary

### Authentication (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - Login and get token
- `POST /logout` - Logout user
- `GET /profile` - Get user profile
- `PATCH /profile` - Update profile
- `POST /change-password` - Change password
- `POST /refresh` - Refresh token

### Enrollment (`/api/enrollment`)
- `POST /start` - Start enrollment (get 5 challenges)
- `POST /add-sample` - Add voice sample
- `POST /complete` - Complete enrollment
- `GET /status/{user_id}` - Check enrollment status

### Verification (`/api/verification`)
- `POST /start-multi` - Start multi-phrase verification (3 phrases)
- `POST /verify-phrase` - Verify single phrase
- `GET /history/{user_id}` - Get verification history

### Challenges (`/api/challenges`)
- `POST /create` - Create single challenge
- `POST /create-batch` - Create multiple challenges
- `GET /{challenge_id}` - Get challenge details
- `GET /{challenge_id}/time-remaining` - Get time remaining
- `GET /user/{user_id}/active` - Get active challenge
- `POST /validate` - Validate challenge
- `POST /cleanup` - Clean expired challenges

### Admin (`/api/admin`)
- `GET /users` - List users (paginated)
- `GET /stats` - System statistics
- `GET /activity` - Activity logs
- `DELETE /users/{user_id}` - Delete user
- `PATCH /users/{user_id}` - Update user
- `GET /phrase-rules` - Get quality rules
- `PATCH /phrase-rules/{rule_name}` - Update rule
- `POST /phrase-rules/{rule_name}/toggle` - Toggle rule

---

## Common Headers

```bash
# Authentication
Authorization: Bearer <access_token>

# Content Type (JSON)
Content-Type: application/json

# Content Type (File Upload)
Content-Type: multipart/form-data
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

---

## Rate Limits

- **Global**: 100 req/min per IP
- **Active challenges**: 3 per user
- **Challenges/hour**: 50 per user

---

## Challenge Timeouts

| Difficulty | Timeout |
|------------|---------|
| Easy | 60s |
| Medium | 90s |
| Hard | 120s |

---

## Audio Requirements

- **Format**: WAV or WebM
- **Max size**: 10MB
- **Min duration**: 2 seconds
- **Max duration**: 30 seconds

---

## Full Documentation

See [API.md](./API.md) for complete documentation with examples.
