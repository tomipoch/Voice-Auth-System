# Verification Module - Dynamic Phrases Integration

## Resumen de cambios

Se ha implementado completamente el módulo de verificación (V2) con soporte para frases dinámicas extraídas de los libros PDF.

## Archivos creados

### 1. `Backend/src/application/verification_service_v2.py` (NUEVO)
Servicio de verificación con frases dinámicas:
- **Clase VerificationSession**: Gestiona sesiones activas de verificación
- **VerificationServiceV2**:
  - `start_verification()`: Selecciona frase aleatoria según dificultad
  - `verify_voice()`: Verifica voz con validación de frase
  - `quick_verify()`: Verificación rápida sin gestión de frases
  - `get_verification_history()`: Historial de verificaciones
- **Características**:
  - Umbral de similitud configurable (default: 0.75)
  - Umbral anti-spoofing configurable (default: 0.5)
  - Cálculo de similitud coseno normalizado
  - Validación completa de embeddings

### 2. `Backend/src/api/verification_controller_v2.py` (NUEVO)
Endpoints REST para verificación:
- `POST /api/v1/verification/start`: Inicia verificación y obtiene frase
- `POST /api/v1/verification/verify`: Verifica voz con validación de frase
- `POST /api/v1/verification/quick-verify`: Verificación rápida sin frase
- `GET /api/v1/verification/history/{user_id}`: Historial de verificaciones

### 3. Actualizaciones en archivos existentes

**`Backend/src/infrastructure/config/dependencies.py`**:
- Agregada función `get_verification_service_v2()`: Crea VerificationServiceV2 con todas las dependencias
- Configura umbrales de similitud y anti-spoofing

**`Backend/src/main.py`**:
- Importado `verification_router_v2`
- Registrado router con `app.include_router(verification_router_v2)`

## Flujo de verificación con frases dinámicas

```
1. Cliente → POST /api/v1/verification/start
   ├─ Parámetros: user_id, difficulty (easy/medium/hard)
   ├─ Validaciones:
   │  ├─ Usuario existe
   │  └─ Usuario tiene voiceprint (está enrolado)
   └─ Respuesta: { verification_id, user_id, phrase: { id, text, difficulty } }

2. Cliente → POST /api/v1/verification/verify
   ├─ Parámetros: verification_id, phrase_id, audio_file
   ├─ Validaciones:
   │  ├─ Frase coincide con la sesión
   │  ├─ Audio válido
   │  ├─ Embedding válido
   │  └─ Usuario tiene voiceprint
   ├─ Procesamiento:
   │  ├─ Extrae embedding del audio
   │  ├─ Calcula similitud coseno con voiceprint
   │  ├─ Verifica anti-spoofing
   │  └─ Decide: is_verified = (similarity >= 0.75) AND is_live
   ├─ Registra uso en phrase_usage
   └─ Respuesta: {
         verification_id, user_id, is_verified,
         confidence_score, similarity_score,
         anti_spoofing_score, phrase_match,
         is_live, threshold_used
       }

3. (Alternativa) Cliente → POST /api/v1/verification/quick-verify
   ├─ Parámetros: user_id, audio_file
   ├─ Sin gestión de frases (más simple)
   └─ Respuesta: Similar a /verify pero sin verification_id ni phrase_match
```

## Características implementadas

✅ **Selección dinámica de frases**:
- Frases aleatorias según dificultad
- Excluye frases usadas recientemente
- Acceso a 43,459 frases disponibles

✅ **Validación de frases**:
- Verifica que phrase_id coincida con la sesión
- Previene uso de frases incorrectas

✅ **Registro de uso**:
- Tabla `phrase_usage` rastrea cada uso
- Campo `used_for = 'verification'`

✅ **Gestión de sesiones**:
- VerificationSession en memoria (transición a Redis en producción)
- Limpieza automática después de verificar

✅ **Auditoría completa**:
- Logs de inicio y resultado
- Metadata detallada (scores, decisión, frase)

✅ **Cálculo de similitud robusto**:
- Similitud coseno normalizada
- Valores entre 0.0 y 1.0
- Normalización de embeddings

✅ **Anti-spoofing**:
- Score opcional de anti-spoofing
- Umbral configurable (default: 0.5)
- Verificación de voz en vivo

✅ **Modo quick-verify**:
- Verificación rápida sin frases
- Útil para casos de uso simples
- Mismo motor de decisión

## Diferencias con módulo de enrollment

| Característica | Enrollment | Verification |
|----------------|------------|--------------|
| **Frases** | Múltiples (MIN_ENROLLMENT_SAMPLES) | Una por verificación |
| **Sesión** | Múltiples muestras | Una muestra |
| **Resultado** | Voiceprint creado | Decisión is_verified |
| **Umbral** | N/A (promedia embeddings) | 0.75 (configurable) |
| **Anti-spoofing** | Opcional | Recomendado |
| **Limpieza** | Al completar | Inmediatamente |

## Configuración de umbrales

Los umbrales se configuran en `get_verification_service_v2()`:

```python
return VerificationServiceV2(
    voice_repo=voice_repo,
    user_repo=user_repo,
    audit_repo=audit_repo,
    phrase_repo=phrase_repo,
    phrase_usage_repo=phrase_usage_repo,
    similarity_threshold=0.75,      # Umbral de similitud (0.0 - 1.0)
    anti_spoofing_threshold=0.5     # Umbral anti-spoofing (0.0 - 1.0)
)
```

**Recomendaciones**:
- `similarity_threshold = 0.75`: Balance entre seguridad y usabilidad
- `similarity_threshold = 0.85`: Más estricto (mayor seguridad)
- `similarity_threshold = 0.65`: Más permisivo (mejor UX)
- `anti_spoofing_threshold = 0.5`: Detecta voces sintéticas/grabadas

## Testing

Para probar la verificación:

```bash
# 1. Iniciar verificación
curl -X POST http://localhost:8000/api/v1/verification/start \
  -F "user_id=<UUID>" \
  -F "difficulty=medium"

# 2. Verificar voz
curl -X POST http://localhost:8000/api/v1/verification/verify \
  -F "verification_id=<UUID>" \
  -F "phrase_id=<UUID>" \
  -F "audio_file=@voice.wav"

# 3. Verificación rápida (sin frases)
curl -X POST http://localhost:8000/api/v1/verification/quick-verify \
  -F "user_id=<UUID>" \
  -F "audio_file=@voice.wav"

# 4. Ver historial
curl http://localhost:8000/api/v1/verification/history/<user_id>?limit=20
```

## Flujo completo: Enrollment + Verification

```
Usuario nuevo:
1. POST /api/v1/enrollment/start → obtiene 3-5 frases
2. POST /api/v1/enrollment/add-sample (repetir para cada frase)
3. POST /api/v1/enrollment/complete → crea voiceprint

Usuario existente:
1. POST /api/v1/verification/start → obtiene 1 frase
2. POST /api/v1/verification/verify → decide is_verified
3. Sistema verifica: similarity >= 0.75 AND is_live
```

## Dependencias

El sistema requiere:
- PostgreSQL con tablas: phrase, phrase_usage, user, voiceprint, verification_attempt, audit_log
- VoiceBiometricEngineFacade para procesamiento de audio
- Repositorios: VoiceTemplate, User, Phrase, PhraseUsage, AuditLog
- Usuario debe estar enrolado (tener voiceprint)

## Próximos pasos

⏳ Actualizar documentación API con ejemplos de verificación
⏳ Crear tests unitarios para VerificationServiceV2
⏳ Crear tests de integración para verification endpoints
⏳ Implementar métrica de FAR (False Accept Rate) y FRR (False Reject Rate)
⏳ Agregar soporte para múltiples intentos de verificación
⏳ Implementar rate limiting para prevenir ataques de fuerza bruta
⏳ Agregar manejo de sesiones con Redis (producción)
⏳ Implementar timeout para sesiones de verificación

## Seguridad

**Consideraciones implementadas**:
- ✅ Validación de phrase_id en sesión
- ✅ Validación de embeddings (dimensión, NaN, infinitos, zeros)
- ✅ Anti-spoofing opcional
- ✅ Auditoría completa de intentos
- ✅ Limpieza de sesiones después de uso

**Por implementar**:
- ⏳ Rate limiting (máximo 5 intentos por minuto)
- ⏳ Bloqueo temporal después de N intentos fallidos
- ⏳ Timeout de sesiones (5 minutos)
- ⏳ Detección de ataques de replay
- ⏳ Logging de IPs y user agents

## Ejemplo de respuesta exitosa

```json
{
  "verification_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "12345678-abcd-ef12-3456-7890abcdef12",
  "is_verified": true,
  "confidence_score": 0.87,
  "similarity_score": 0.87,
  "anti_spoofing_score": 0.23,
  "phrase_match": true,
  "is_live": true,
  "threshold_used": 0.75
}
```

## Ejemplo de respuesta fallida

```json
{
  "verification_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "12345678-abcd-ef12-3456-7890abcdef12",
  "is_verified": false,
  "confidence_score": 0.62,
  "similarity_score": 0.62,
  "anti_spoofing_score": 0.18,
  "phrase_match": true,
  "is_live": true,
  "threshold_used": 0.75
}
```

**Nota**: `is_verified = false` porque `similarity_score (0.62) < threshold (0.75)`
