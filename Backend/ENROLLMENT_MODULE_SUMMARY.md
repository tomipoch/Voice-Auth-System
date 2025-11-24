# Enrollment Module - Dynamic Phrases Integration

## Resumen de cambios

Se ha implementado completamente el módulo de enrollment con soporte para frases dinámicas extraídas de los libros PDF.

## Archivos modificados/creados

### 1. `Backend/src/application/enrollment_service.py` (REESCRITO)
- **Clase EnrollmentSession**: Gestiona sesiones activas de enrollment en memoria
- **EnrollmentService**: 
  - `start_enrollment()`: Selecciona frases dinámicas según dificultad
  - `add_enrollment_sample()`: Valida frase y registra uso
  - `complete_enrollment()`: Crea voiceprint final
  - `get_enrollment_status()`: Consulta estado del usuario
- **Inyección de dependencias**: PhraseRepository y PhraseUsageRepository

### 2. `Backend/src/application/dto/enrollment_dto.py` (CREADO)
DTOs para enrollment con soporte de frases:
- `StartEnrollmentRequest/Response`: Include lista de frases
- `AddEnrollmentSampleRequest/Response`: Include phrase_id
- `CompleteEnrollmentRequest/Response`: Voiceprint final
- `EnrollmentStatusResponse`: Estado completo

### 3. `Backend/src/api/enrollment_controller.py` (REESCRITO)
Endpoints REST:
- `POST /api/v1/enrollment/start`: Inicia enrollment y devuelve frases
- `POST /api/v1/enrollment/add-sample`: Agrega muestra con validación de frase
- `POST /api/v1/enrollment/complete`: Completa enrollment
- `GET /api/v1/enrollment/status/{user_id}`: Consulta estado

### 4. `Backend/src/infrastructure/persistence/PostgresAuditLogRepository.py` (CREADO)
Implementación PostgreSQL del repositorio de audit log:
- `log_event()`: Registra eventos de auditoría
- `get_logs()`: Consulta logs con filtros
- `get_user_activity()`: Actividad reciente del usuario

### 5. `Backend/src/infrastructure/config/dependencies.py` (ACTUALIZADO)
Agregadas funciones de inyección:
- `get_enrollment_service()`: Crea EnrollmentService con todas las dependencias
- `get_voice_biometric_engine()`: Retorna VoiceBiometricEngineFacade

### 6. `Backend/src/main.py` (ACTUALIZADO)
- Importado enrollment_router
- Registrado router con `app.include_router(enrollment_router)`

## Flujo de enrollment con frases dinámicas

```
1. Cliente → POST /api/v1/enrollment/start
   ├─ Parámetros: external_ref?, user_id?, difficulty (easy/medium/hard)
   └─ Respuesta: { enrollment_id, user_id, phrases: [{ id, text, difficulty }], required_samples }

2. Para cada frase (MIN_ENROLLMENT_SAMPLES veces):
   Cliente → POST /api/v1/enrollment/add-sample
   ├─ Parámetros: enrollment_id, phrase_id, audio_file
   ├─ Validaciones:
   │  ├─ Frase pertenece a la sesión
   │  ├─ Audio válido (SNR, duración)
   │  └─ Embedding válido
   ├─ Registra uso en phrase_usage
   └─ Respuesta: { sample_id, samples_completed, samples_required, is_complete, next_phrase? }

3. Cliente → POST /api/v1/enrollment/complete
   ├─ Parámetros: enrollment_id, speaker_model_id?
   ├─ Crea voiceprint (promedio de embeddings)
   └─ Respuesta: { voiceprint_id, user_id, quality_score, samples_used }

4. Consulta estado (opcional):
   Cliente → GET /api/v1/enrollment/status/{user_id}
   └─ Respuesta: { status, voiceprint_id?, samples_count, required_samples, phrases_used }
```

## Características implementadas

✅ **Selección dinámica de frases**: 
- Basada en dificultad (easy/medium/hard)
- Excluye frases usadas recientemente
- 43,459 frases disponibles

✅ **Validación de frases**:
- Verifica que phrase_id corresponda a la sesión
- Previene uso de frases no asignadas

✅ **Registro de uso**:
- Tabla `phrase_usage` rastrea cada uso
- Campo `used_for` diferencia enrollment/verification

✅ **Gestión de sesiones**:
- EnrollmentSession en memoria (transición a Redis en producción)
- Limpieza automática al completar

✅ **Auditoría completa**:
- Logs de inicio, muestras, completado
- Metadata detallada (SNR, duración, quality_score)

✅ **Calidad del enrollment**:
- Cálculo de similitud entre embeddings
- Score de 0.0 a 1.0

## Próximos pasos

⏳ Implementar módulo de verificación con frases dinámicas
⏳ Actualizar documentación API con ejemplos de enrollment
⏳ Crear tests unitarios para EnrollmentService
⏳ Crear tests de integración para enrollment endpoints
⏳ Agregar manejo de sesiones con Redis (producción)
⏳ Implementar límite de tiempo para sesiones

## Dependencias necesarias

El sistema requiere:
- PostgreSQL con tablas: phrase, phrase_usage, user, voiceprint, enrollment_sample, audit_log
- VoiceBiometricEngineFacade para procesamiento de audio
- Repositorios: VoiceTemplate, User, Phrase, PhraseUsage, AuditLog

## Testing

Para probar el enrollment:

```bash
# 1. Iniciar enrollment
curl -X POST http://localhost:8000/api/v1/enrollment/start \
  -F "difficulty=medium"

# 2. Agregar muestra (repetir para cada frase)
curl -X POST http://localhost:8000/api/v1/enrollment/add-sample \
  -F "enrollment_id=<UUID>" \
  -F "phrase_id=<UUID>" \
  -F "audio_file=@sample.wav"

# 3. Completar enrollment
curl -X POST http://localhost:8000/api/v1/enrollment/complete \
  -F "enrollment_id=<UUID>"

# 4. Verificar estado
curl http://localhost:8000/api/v1/enrollment/status/<user_id>
```
