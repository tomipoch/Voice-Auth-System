# 🚀 Mejoras y Trabajos Futuros
## Sistema de Autenticación Biométrica por Voz

**Fecha:** 17 de Diciembre de 2025  
**Versión del Sistema:** 2.0.0-RELEASE  
**Propósito:** Documento de recomendaciones para mejoras y evolución del proyecto

---

## 📋 Índice

1. [Mejoras de Corto Plazo (1-3 meses)](#1-mejoras-de-corto-plazo)
2. [Mejoras de Mediano Plazo (3-6 meses)](#2-mejoras-de-mediano-plazo)
3. [Trabajos Futuros de Largo Plazo (6+ meses)](#3-trabajos-futuros-de-largo-plazo)
4. [Mejoras en Seguridad](#4-mejoras-en-seguridad)
5. [Optimizaciones de Performance](#5-optimizaciones-de-performance)
6. [Mejoras en ML/IA](#6-mejoras-en-mlia)
7. [Escalabilidad y Arquitectura](#7-escalabilidad-y-arquitectura)
8. [UX/UI y Accesibilidad](#8-uxui-y-accesibilidad)
9. [Investigación y Publicación](#9-investigación-y-publicación)

---

## 1. Mejoras de Corto Plazo (1-3 meses)

### 1.1 Testing y Calidad del Código

#### 1.1.1 Tests Unitarios
**Prioridad:** 🔴 ALTA

- [x] **Backend: Aumentar cobertura de tests**
  - Objetivo: Alcanzar 80%+ de cobertura
  - Implementar tests para todos los servicios
  - Tests para repositorios con mocks de BD
  - Tests para validaciones de DTOs

```python
# Ejemplo de test pendiente
def test_verification_with_invalid_phrase_id():
    """Should reject verification with non-existent phrase"""
    pass

def test_enrollment_minimum_quality_threshold():
    """Should reject low-quality audio samples"""
    pass
```

- [ ] **Frontend: Tests con Jest + React Testing Library**
  - Tests de componentes (`DynamicEnrollment`, `DynamicVerification`)
  - Tests de servicios (mocks de API calls)
  - Tests de integración E2E con Playwright/Cypress

#### 1.1.2 Integración Continua (CI/CD)
**Prioridad:** 🟡 MEDIA

- [ ] **GitHub Actions / GitLab CI**
  - Pipeline automático de tests
  - Linting automático (pylint, ESLint)
  - Build y push de imágenes Docker
  - Deploy automático a staging

```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run pytest
        run: |
          cd Backend
          pytest --cov=src --cov-report=xml
```

### 1.2 Logging y Monitoreo Avanzado

#### 1.2.1 Logging Estructurado
**Prioridad:** 🟡 MEDIA

- [ ] **Implementar logs estructurados (JSON)**
  - Usar biblioteca como `structlog` o `python-json-logger`
  - Incluir `trace_id` para seguimiento de requests
  - Niveles de log apropiados (DEBUG, INFO, WARNING, ERROR, CRITICAL)

```python
# Ejemplo de implementación
import structlog

logger = structlog.get_logger()
logger.info(
    "verification_attempted",
    user_id=user_id,
    similarity_score=score,
    is_verified=result,
    trace_id=trace_id
)
```

#### 1.2.2 Dashboard de Métricas
**Prioridad:** 🟡 MEDIA

- [ ] **Grafana + Prometheus**
  - Métricas de latencia de endpoints
  - Tasa de éxito/fallo de verificaciones
  - Uso de CPU/memoria
  - Alertas automáticas ante anomalías

- [ ] **Métricas biométricas en tiempo real**
  - EER (Equal Error Rate) actualizado diariamente
  - FAR/FRR por dificultad de frase
  - Distribución de similarity scores

### 1.3 Validación Experimental Completa

#### 1.3.1 Ejecución del EVALUATION_GUIDE.md
**Prioridad:** 🔴 ALTA

- [ ] **Recolectar datos reales** (ver `docs/EVALUATION_GUIDE.md`)
  - Mínimo 10 usuarios reales
  - 10-15 verificaciones por usuario
  - Diferentes condiciones de ruido
  - Diferentes dispositivos (laptop, móvil, tablet)

- [ ] **Calcular métricas biométricas reales**
  - EER (Equal Error Rate)
  - FAR (False Acceptance Rate)
  - FRR (False Rejection Rate)
  - Curva DET (Detection Error Tradeoff)

- [ ] **Actualizar documentación con resultados**
  - Completar sección 7 de `METRICS_AND_EVALUATION.md`
  - Incluir gráficos generados
  - Análisis e interpretación de resultados

#### 1.3.2 Testing Cross-User (Impostor Testing)
**Prioridad:** 🔴 ALTA

> **NOTA CRÍTICA:** Actualmente los "impostor scores" están **simulados** con distribuciones normales. Es crucial realizar pruebas reales de impostores.

- [ ] **Implementar endpoint de testing cross-user**

```python
POST /api/admin/test/cross-verify
{
  "enrolled_user_id": "uuid-1",
  "impostor_user_id": "uuid-2",
  "phrase_id": "uuid-3",
  "audio_file": "blob"
}
# Respuesta: { "similarity_score": 0.42, "should_reject": true }
```

- [ ] **Protocolo de testing**
  - Usuario A intenta autenticarse como Usuario B
  - Repetir con múltiples combinaciones
  - Mínimo 50-100 intentos de impostor

### 1.4 Mejoras en la Base de Datos

#### 1.4.1 Optimización de Queries
**Prioridad:** 🟢 BAJA

- [ ] **Índices adicionales**
  - `CREATE INDEX idx_phrase_usage_recent ON phrase_usage(user_id, used_at DESC);`
  - `CREATE INDEX idx_verification_user_created ON verification_attempt(user_id, created_at DESC);`

- [ ] **Vistas materializadas para estadísticas**
  
```sql
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
  u.id,
  u.email,
  COUNT(DISTINCT va.id) as total_verifications,
  AVG(va.similarity_score) as avg_similarity,
  SUM(CASE WHEN va.is_verified THEN 1 ELSE 0 END) as successful_verifications
FROM "user" u
LEFT JOIN verification_attempt va ON va.user_id = u.id
GROUP BY u.id, u.email;
```

#### 1.4.2 Particionamiento de Tablas
**Prioridad:** 🟢 BAJA

- [ ] **Particionar `audit_log` por fecha**
  - Mejorar performance de queries históricos
  - Facilitar archivado de logs antiguos

```sql
CREATE TABLE audit_log_2025_12 PARTITION OF audit_log
FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

---

## 2. Mejoras de Mediano Plazo (3-6 meses)

### 2.1 Funcionalidades Nuevas

#### 2.1.1 Re-enrollment Adaptativo
**Prioridad:** 🟡 MEDIA

**Problema identificado:** Las voces cambian con el tiempo (edad, enfermedad, fatiga).

- [ ] **Sistema de actualización incremental de voiceprint**
  - Detectar degradación del voiceprint (similarity scores bajando consistentemente)
  - Sugerir re-enrollment cuando avg_similarity < 0.70
  - Re-enrollment "suave" (mezclar nuevas muestras con las antiguas)

```python
# Pseudocódigo
def adaptive_reenrollment(user_id):
    recent_scores = get_last_10_verification_scores(user_id)
    if avg(recent_scores) < 0.70:
        trigger_reenrollment_suggestion(user_id)
        # Nueva muestra se pondera 30%, voiceprint antiguo 70%
        new_voiceprint = 0.3 * new_embedding + 0.7 * old_voiceprint
```

#### 2.1.2 Autenticación Multi-Factor (MFA)
**Prioridad:** 🟡 MEDIA

- [ ] **Voz + PIN de voz**
  - Usuario dice un PIN de 4-6 dígitos además de la frase
  - Validación con ASR (Speech-to-Text)
  - Fortalecer seguridad sin sacrificar UX

```
Frase challenge: "El rápido zorro marrón salta sobre el perro perezoso"
PIN de voz: "3-7-9-2"
Usuario dice: "El rápido zorro marrón salta sobre el perro perezoso, tres siete nueve dos"
```

- [ ] **Voz + OTP (One-Time Password)**
  - Integración con Google Authenticator / Authy
  - Voz como factor 1, OTP como factor 2

#### 2.1.3 Historiales y Analytics para Usuarios
**Prioridad:** 🟢 BAJA

- [ ] **Dashboard personal de usuario**
  - Historial de verificaciones (última semana/mes)
  - Tendencia de similarity scores
  - Alertas de intentos fallidos

- [ ] **Página de verificaciones en frontend**
  - Tabla con fecha, resultado, confidence
  - Gráfico de evolución temporal
  - Filtros por rango de fecha

### 2.2 Anti-Spoofing Mejorado

#### 2.2.1 Detección de Deepfakes Avanzada
**Prioridad:** 🔴 ALTA

**Estado actual:** Se tiene un modelo anti-spoofing básico.

- [ ] **Implementar modelos SOTA**
  - **AASIST** (Audio Anti-Spoofing using Integrated Spectro-Temporal Features)
  - **RawNet3** (mejor que RawNet2 para anti-spoofing)
  - Usar dataset ASVspoof 2021 para fine-tuning

- [ ] **Análisis multi-modal**
  - Análisis de frecuencias (MFCC, Mel-spectrogram)
  - Análisis temporal (pitch, jitter, shimmer)
  - Detección de artefactos de compresión (MP3, AAC)

```python
# Pipeline propuesto
def advanced_spoofing_detection(audio):
    # Modelo 1: RawNet3 (raw waveform)
    score_rawnet = rawnet3_model(audio)
    
    # Modelo 2: AASIST (spectrogram)
    score_aasist = aasist_model(extract_spectrogram(audio))
    
    # Modelo 3: Artifact Detector
    score_artifact = detect_compression_artifacts(audio)
    
    # Ensemble voting
    final_score = weighted_average([score_rawnet, score_aasist, score_artifact])
    return final_score
```

#### 2.2.2 Detección de Replay Attacks
**Prioridad:** 🟡 MEDIA

- [ ] **Challenge acústico**
  - Emitir un tono aleatorio (800-2000 Hz) antes de la grabación
  - Usuario debe grabar en el mismo ambiente
  - Verificar que el tono se refleje en el audio (eco, reverberación)

- [ ] **Análisis de ruido ambiente**
  - Extraer "audio fingerprint" del ruido de fondo
  - Cada grabación debe tener un ruido único
  - Detectar si 2 grabaciones tienen el mismo ruido (sospecha de replay)

### 2.3 Mejoras en el Modelo de Speaker Recognition

#### 2.3.1 Upgrade a Modelos Más Recientes
**Prioridad:** 🟡 MEDIA

**Estado actual:** ECAPA-TDNN (2020).

- [ ] **Evaluar modelos SOTA 2023-2025**
  - **WavLM** (Microsoft, 2022)
  - **Whisper Embeddings** (OpenAI, puede usarse para speaker ID)
  - **UniSpeech-SAT** (Microsoft)
  - **Pyannote.audio 3.0** (speaker diarization + verification)

- [ ] **Benchmark comparativo**
  - Evaluar EER de cada modelo en tu dataset
  - Comparar latencia (inference time)
  - Trade-off precisión vs velocidad

#### 2.3.2 Fine-Tuning con Datos Propios
**Prioridad:** 🟢 BAJA

- [ ] **Reentrenar modelo con datos locales**
  - Usar las muestras de enrollment recolectadas
  - Fine-tune sobre VoxCeleb2 + datos propios
  - Mejorar rendimiento específico para tu caso de uso

```python
# Proceso de fine-tuning
from speechbrain.pretrained import EncoderClassifier

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="models/fine_tuned_ecapa"
)

# Entrenar con tus datos
classifier.fit(train_data, validation_data, n_epochs=10)
```

---

## 3. Trabajos Futuros de Largo Plazo (6+ meses)

### 3.1 Aplicación Móvil Nativa

#### 3.1.1 React Native App
**Prioridad:** 🟡 MEDIA

- [ ] **App multiplataforma (iOS + Android)**
  - Misma lógica que el frontend web
  - Uso de `react-native-audio-recorder-player`
  - Compartir código con web (React + TypeScript)

- [ ] **Features específicas de móvil**
  - Autenticación con voz para desbloqueo de app
  - Notificaciones push de intentos de acceso
  - Soporte offline (local voiceprint caching)

#### 3.1.2 Optimización para Dispositivos Móviles
**Prioridad:** 🟢 BAJA

- [ ] **Compresión de audio optimizada**
  - Usar OPUS codec (mejor que MP3 para voz)
  - Reducir bitrate a 16kbps sin pérdida de calidad biométrica

- [ ] **Modelos cuantizados para edge inference**
  - Quantize embeddings a INT8 (4x más rápido)
  - Ejecutar anti-spoofing en el dispositivo (privacidad)

### 3.2 Multi-Tenancy y SaaS

#### 3.2.1 Arquitectura Multi-Tenant
**Prioridad:** 🟢 BAJA

- [ ] **Soporte para múltiples organizaciones**
  - Tabla `organization` con `tenant_id`
  - Row-level security en PostgreSQL
  - API keys por tenant

```sql
CREATE TABLE organization (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  api_key_hash VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Modificar tabla user
ALTER TABLE "user" ADD COLUMN tenant_id UUID REFERENCES organization(id);
```

- [ ] **Dashboard de administración por tenant**
  - Cada organización ve solo sus usuarios
  - Configuración de umbrales por tenant
  - Reportes y analíticas separadas

#### 3.2.2 Modelo de Negocio SaaS
**Prioridad:** 🟢 BAJA

- [ ] **Sistema de facturación**
  - Integración con Stripe/PayPal
  - Planes: Free (100 verificaciones/mes), Pro, Enterprise
  - Límites de rate basados en plan

- [ ] **Marketplace de frases**
  - Permitir a organizaciones subir sus propias frases
  - Vender corpus de frases especializados (legal, médico, financiero)

### 3.3 Integración con Sistemas Externos

#### 3.3.1 Single Sign-On (SSO)
**Prioridad:** 🟡 MEDIA

- [ ] **OAuth 2.0 / SAML**
  - Integración con Google Workspace
  - Integración con Microsoft Azure AD
  - Soporte para LDAP

- [ ] **Voz como MFA para SSO**
  - Usuario inicia sesión con Google → desafío de voz
  - Casos de uso: banking, healthcare, government

#### 3.3.2 APIs de Terceros
**Prioridad:** 🟢 BAJA

- [ ] **Webhooks**
  - Notificar a sistemas externos de eventos (enrollment, verification success/fail)
  - Formato JSON estándar

```json
POST https://cliente.com/webhook/voice-biometrics
{
  "event": "verification.success",
  "user_id": "uuid",
  "timestamp": "2025-12-17T01:15:57Z",
  "confidence": 0.89
}
```

- [ ] **SDK para lenguajes populares**
  - `voice-bio-js` (JavaScript/TypeScript)
  - `voice-bio-py` (Python)
  - `voice-bio-java` (Java/Kotlin)

### 3.4 Soporte Multi-Idioma

#### 3.4.1 Internacionalización del Sistema
**Prioridad:** 🟢 BAJA

**Estado actual:** Solo español.

- [ ] **Corpus de frases en múltiples idiomas**
  - Inglés: 40,000+ frases de literatura anglosajona
  - Francés, Alemán, Portugués
  - Detección automática de idioma (usar ASR)

- [ ] **Modelos de speaker recognition multi-idioma**
  - Entrenar/fine-tune con datos en varios idiomas
  - Verificar que embeddings sean language-independent

#### 3.4.2 ASR Multi-Idioma
**Prioridad:** 🟢 BAJA

- [ ] **Reemplazar ASR español con modelo multilingüe**
  - Whisper de OpenAI (99 idiomas)
  - Wav2Vec2-XLSR (53 idiomas)

---

## 4. Mejoras en Seguridad

### 4.1 Encriptación Avanzada

#### 4.1.1 Encriptación de Embeddings
**Prioridad:** 🟡 MEDIA

**Estado actual:** Embeddings almacenados en texto plano en `voiceprint.embedding`.

- [ ] **Implementar encriptación AES-256**

```python
from cryptography.fernet import Fernet

# Al guardar
key = os.getenv('EMBEDDING_ENCRYPTION_KEY')
cipher = Fernet(key)
encrypted_embedding = cipher.encrypt(pickle.dumps(embedding))

# Al leer
decrypted_embedding = pickle.loads(cipher.decrypt(encrypted_embedding))
```

- [ ] **Key rotation policy**
  - Rotar clave cada 6 meses
  - Re-encriptar embeddings con nueva clave

#### 4.1.2 Zero-Knowledge Proof (Investigación)
**Prioridad:** 🟢 BAJA (Investigación académica)

- [ ] **Verificación sin revelar voiceprint**
  - Explorar protocolos tipo "Secure Multi-Party Computation"
  - Usuario prueba que su voz coincide sin enviar el audio al servidor
  - Aplicación: compliance con GDPR extremo

### 4.2 Rate Limiting y Anti-Abuse

#### 4.2.1 Rate Limiting Granular
**Prioridad:** 🔴 ALTA

**Estado actual:** Implementación básica o ausente.

- [ ] **Límites por endpoint**
  - `/api/enrollment/start`: 3 requests/hora por usuario
  - `/api/verification/start`: 10 requests/hora por usuario
  - Usar Redis para contadores

```python
# Implementación con Redis
def rate_limit(user_id: str, action: str, max_attempts: int, window_seconds: int):
    key = f"rate_limit:{user_id}:{action}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    if current > max_attempts:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

- [ ] **Migrar rate limiting de in-memory a Redis**
  - Estado actual: `auth_middleware.py` usa `Dict` en memoria
  - Problema: No funciona en entornos distribuidos (múltiples workers)
  - Solución: Usar Redis como store centralizado

#### 4.2.2 Session Cleanup (Memory Leak Prevention)
**Prioridad:** 🟡 MEDIA

**Estado actual:** Las sesiones en `EnrollmentService._active_sessions` y `VerificationService._active_multi_sessions` no se limpian si el usuario abandona el proceso.

- [ ] **Implementar background task de limpieza**

```python
# Ejemplo con APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def cleanup_expired_sessions():
    now = datetime.now(timezone.utc)
    max_age = timedelta(minutes=10)
    
    # Cleanup enrollment sessions
    for session_id, session in list(EnrollmentService._active_sessions.items()):
        if now - session.created_at > max_age:
            del EnrollmentService._active_sessions[session_id]
    
    # Cleanup verification sessions
    for session_id, session in list(VerificationService._active_multi_sessions.items()):
        if now - session.created_at > max_age:
            del VerificationService._active_multi_sessions[session_id]

scheduler = AsyncIOScheduler()
scheduler.add_job(cleanup_expired_sessions, 'interval', minutes=5)
scheduler.start()
```

- [ ] **Agregar endpoint de monitoreo de sesiones**
  - `GET /api/admin/sessions/active` → Número de sesiones activas
  - Útil para debugging y monitoreo

#### 4.2.3 Thread Safety en Session Management
**Prioridad:** 🟡 MEDIA

**Estado actual:** Los diccionarios `_active_sessions` y `_active_multi_sessions` son atributos de clase, compartidos entre todas las instancias.

```python
class EnrollmentService:
    _active_sessions: Dict[UUID, EnrollmentSession] = {}  # Compartido entre workers
```

- [ ] **Migrar a Redis para entornos distribuidos**
  - Estado actual funciona para desarrollo/demo (single worker)
  - Producción multi-worker requiere store externo (Redis)
  - Usar `asyncio.Lock` como alternativa temporal

```python
# Alternativa temporal para single-pod
_session_lock = asyncio.Lock()

async def start_enrollment(self, ...):
    async with self._session_lock:
        session = EnrollmentSession(...)
        self._active_sessions[enrollment_id] = session
```


#### 4.2.2 Account Lockout
**Prioridad:** 🔴 ALTA

- [ ] **Bloqueo temporal tras intentos fallidos**
  - 3 fallos consecutivos → bloqueo 15 minutos
  - 5 fallos en 1 hora → bloqueo 24 horas
  - Notificación por email al usuario

- [ ] **CAPTCHA challenge**
  - Tras 2 fallos, mostrar CAPTCHA
  - Prevenir ataques automatizados

### 4.3 Auditoría y Compliance

#### 4.3.1 Logs Inmutables
**Prioridad:** 🟡 MEDIA

- [ ] **Blockchain de auditoría (opcional)**
  - Hash de cada entrada de `audit_log` en blockchain privado
  - Garantizar no-repudio

- [ ] **Firma digital de eventos críticos**
  - Enrollment, cambios de voiceprint, accesos de admin
  - Timestamp RFC 3161

#### 4.3.2 Cumplimiento Normativo
**Prioridad:** 🟡 MEDIA

- [ ] **GDPR Compliance**
  - Endpoint "Right to be forgotten" (`DELETE /api/user/{id}/gdpr-delete`)
  - Exportar datos del usuario (`GET /api/user/{id}/data-export`)

- [ ] **ISO 27001 / SOC 2**
  - Documentar controles de seguridad
  - Auditoría de acceso a datos biométricos

---

## 5. Optimizaciones de Performance

### 5.1 Backend

#### 5.1.1 Caché de Embeddings
**Prioridad:** 🟡 MEDIA

- [ ] **Redis cache para voiceprints**
  - Evitar queries a PostgreSQL en cada verificación
  - TTL de 1 hora

```python
def get_voiceprint_cached(user_id: str):
    cache_key = f"voiceprint:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return pickle.loads(cached)
    
    # Fetch from DB
    voiceprint = db.query(Voiceprint).filter_by(user_id=user_id).first()
    redis_client.setex(cache_key, 3600, pickle.dumps(voiceprint))
    return voiceprint
```

#### 5.1.2 Async/Await Optimización
**Prioridad:** 🟢 BAJA

- [ ] **Paralelizar operaciones ML**
  - Speaker recognition + Anti-spoofing + ASR en paralelo

```python
async def verify_audio(audio_bytes):
    speaker_task = asyncio.create_task(speaker_recognition(audio_bytes))
    spoofing_task = asyncio.create_task(anti_spoofing(audio_bytes))
    asr_task = asyncio.create_task(transcribe(audio_bytes))
    
    speaker, spoofing, transcript = await asyncio.gather(
        speaker_task, spoofing_task, asr_task
    )
    return compute_final_score(speaker, spoofing, transcript)
```

#### 5.1.3 GPU Acceleration
**Prioridad:** 🟢 BAJA

- [ ] **Inferencia en GPU**
  - Usar PyTorch con CUDA
  - Batch processing de múltiples verificaciones
  - Reducir latencia de 2.5s → 0.5s

### 5.2 Frontend

#### 5.2.1 Lazy Loading
**Prioridad:** 🟢 BAJA

- [ ] **Code splitting**
  - Cargar `DynamicEnrollment` solo cuando se accede a `/enrollment`
  - Usar `React.lazy()` y `Suspense`

```typescript
const DynamicEnrollment = React.lazy(() => import('./components/DynamicEnrollment'));

<Suspense fallback={<Loading />}>
  <DynamicEnrollment />
</Suspense>
```

#### 5.2.2 Audio Processing en Web Worker
**Prioridad:** 🟡 MEDIA

- [ ] **Offload audio processing a worker thread**
  - No bloquear UI thread durante encoding
  - Usar `AudioWorklet` para procesamiento en tiempo real

---

## 6. Mejoras en ML/IA

### 6.1 Adaptación al Usuario (Personalization)

#### 6.1.1 User-Specific Thresholds
**Prioridad:** 🟡 MEDIA

**Observación:** Algunos usuarios tienen voces muy consistentes (threshold 0.85), otros más variables (threshold 0.70).

- [ ] **Calcular threshold personalizado**

```python
def adaptive_threshold(user_id):
    historical_scores = get_genuine_scores(user_id, limit=50)
    mean = np.mean(historical_scores)
    std = np.std(historical_scores)
    
    # Threshold = mean - 2*std (2 desviaciones estándar)
    return max(0.60, mean - 2*std)
```

### 6.2 Detección de Emociones

#### 6.2.1 Análisis de Estado Emocional
**Prioridad:** 🟢 BAJA (Feature experimental)

- [ ] **Detectar estrés/nerviosismo**
  - Cambios en pitch, tempo, intensidad
  - Alertar si el usuario parece bajo coacción

```python
emotion = analyze_emotion(audio)
if emotion == "stressed" or emotion == "fearful":
    trigger_security_alert("Possible duress authentication attempt")
```

### 6.3 Continuous Authentication

#### 6.3.1 Autenticación Continua
**Prioridad:** 🟢 BAJA (Research)

- [ ] **Verificación periódica durante sesión**
  - Cada 5 minutos, pedir una frase corta
  - Asegurar que la misma persona sigue usando el sistema

---

## 7. Escalabilidad y Arquitectura

### 7.1 Microservicios

#### 7.1.1 Desacoplamiento del Motor ML
**Prioridad:** 🟡 MEDIA

**Estado actual:** Monolito modular.

- [ ] **Extraer `VoiceEngine` a microservicio separado**

```
Backend (FastAPI)         ML Service (FastAPI/gRPC)
     │                              │
     ├─ API Controllers             ├─ /embed (speaker recognition)
     ├─ Business Logic              ├─ /anti-spoof
     └─ DB Access                   └─ /transcribe
          │
          └──── HTTP/gRPC ──────────┘
```

**Beneficios:**
- Escalar ML service independientemente (agregar GPUs)
- Hacer A/B testing de modelos
- Deployment sin downtime (canary releases)

#### 7.1.2 Message Queue para Procesamiento Asíncrono
**Prioridad:** 🟢 BAJA

- [ ] **RabbitMQ / AWS SQS**
  - Enrollment: encolar 3 audios → procesar en background
  - Usuario no espera 7-10 segundos, recibe notificación cuando termine

### 7.2 Database Scaling

#### 7.2.1 Read Replicas
**Prioridad:** 🟢 BAJA

- [ ] **PostgreSQL replication**
  - 1 master (writes) + 2 replicas (reads)
  - Queries de stats/admin usan réplicas
  - Reduce carga en master

#### 7.2.2 Sharding por Tenant
**Prioridad:** 🟢 BAJA

- [ ] **Database per tenant (para SaaS)**
  - Tenant grande (1M+ usuarios) → DB dedicado
  - Tenants pequeños → DB compartido

---

## 8. UX/UI y Accesibilidad

### 8.1 Accesibilidad (a11y)

#### 8.1.1 WCAG 2.1 Compliance
**Prioridad:** 🟡 MEDIA

- [ ] **Soporte para lectores de pantalla**
  - ARIA labels en todos los componentes
  - `alt` text en iconos
  - Navegación por teclado completa

- [ ] **Contraste de colores**
  - Verificar ratios con herramientas (WebAIM Contrast Checker)
  - Modo de alto contraste

#### 8.1.2 Soporte para Usuarios con Discapacidades Vocales
**Prioridad:** 🟢 BAJA

- [ ] **Modo de texto-a-voz**
  - Usuario con disfonía puede usar TTS de alta calidad
  - Sistema verifica "patrón de habla" del TTS configurado

### 8.2 Mejoras de Interfaz

#### 8.2.1 Onboarding Interactivo
**Prioridad:** 🟢 BAJA

- [ ] **Tutorial guiado para nuevo usuario**
  - Tour de la aplicación con `react-joyride`
  - Tips de cómo grabar audio de calidad

#### 8.2.2 Feedback Háptico (Móvil)
**Prioridad:** 🟢 BAJA

- [ ] **Vibración en eventos clave**
  - Iniciar grabación: vibración corta
  - Verificación exitosa: 2 vibraciones
  - Verificación fallida: vibración larga

---

## 9. Investigación y Publicación

### 9.1 Publicaciones Académicas

#### 9.1.1 Paper en Conferencias
**Prioridad:** 🟡 MEDIA

- [ ] **Redactar paper científico**
  - Título: "Dynamic Phrase-Based Voice Biometrics: A Novel Approach to Anti-Spoofing"
  - Conferencias objetivo: INTERSPEECH, ICASSP, IEEE BTAS
  - Secciones: Abstract, Introduction, Related Work, Methodology, Experiments, Results, Conclusion

- [ ] **Dataset público**
  - Anonimizar y liberar dataset de evaluación
  - 10 usuarios, 150 verification attempts
  - Contribuir a la comunidad científica

#### 9.1.2 Métricas de Investigación
**Prioridad:** 🔴 ALTA

> **CRÍTICO:** Estas métricas son esenciales para validar tu tesis.

- [ ] **Comparación con estado del arte**
  - Comparar tu EER con papers recientes (2022-2025)
  - Benchmarking en datasets públicos (VoxCeleb, ASVspoof)

| Sistema | EER | FAR @ FRR=1% | Dataset |
|---------|-----|--------------|---------|
| Tu sistema | **TBD** | **TBD** | Custom (10 users) |
| ECAPA-TDNN (baseline) | 0.87% | 2.3% | VoxCeleb1 |
| WavLM-TDNN (SOTA 2023) | 0.54% | 1.2% | VoxCeleb1 |

### 9.2 Patentes y Propiedad Intelectual

#### 9.2.1 Solicitud de Patente
**Prioridad:** 🟢 BAJA

- [ ] **Patentar sistema de frases dinámicas**
  - "Method and System for Voice Authentication Using Dynamically Selected Literary Phrases"
  - Consultar con oficina de transferencia tecnológica de tu universidad

---

## 10. Resumen Ejecutivo de Prioridades

### 🔴 ALTA PRIORIDAD (Imprescindible para tesis)

1. **Validación experimental completa** (EVALUATION_GUIDE.md)
2. **Testing cross-user real** (eliminar simulación de impostores)
3. **Aumentar cobertura de tests unitarios** (backend)
4. **Rate limiting y account lockout** (seguridad básica)
5. **Métricas de investigación y comparación SOTA**

### 🟡 MEDIA PRIORIDAD (Mejora significativa)

6. Anti-spoofing avanzado (AASIST, RawNet3)
7. Re-enrollment adaptativo
8. Modelos de speaker recognition más recientes (WavLM, UniSpeech)
9. CI/CD pipeline
10. Logging estructurado + Grafana

### 🟢 BAJA PRIORIDAD (Nice to have)

11. Aplicación móvil
12. Multi-tenancy SaaS
13. Soporte multi-idioma
14. Features de investigación avanzada (ZKP, continuous auth)

---

## 11. Roadmap Sugerido

### Mes 1 (Enero 2026)
- ✅ Ejecutar EVALUATION_GUIDE.md (10 usuarios, 150 verificaciones)
- ✅ Calcular EER, FAR, FRR reales
- ✅ Implementar testing cross-user
- ✅ Actualizar METRICS_AND_EVALUATION.md con resultados

### Mes 2 (Febrero 2026)
- ✅ Aumentar cobertura de tests a 80%
- ✅ Implementar rate limiting robusto
- ✅ Mejorar anti-spoofing (evaluar AASIST)
- ✅ CI/CD básico (GitHub Actions)

### Mes 3 (Marzo 2026)
- ✅ Redactar paper científico
- ✅ Re-enrollment adaptativo
- ✅ Dashboard de métricas (Grafana)
- ✅ Documentación final de tesis

---

## 12. Conclusión

Este documento presenta **más de 80 mejoras y trabajos futuros** categorizados en:
- **Seguridad** (encriptación, anti-spoofing, compliance)
- **Performance** (caché, GPU, async)
- **ML/IA** (modelos SOTA, personalización)
- **Escalabilidad** (microservicios, sharding)
- **UX/Accesibilidad**
- **Investigación** (publicaciones, patentes)

El proyecto tiene una base sólida ✅, pero las **mejoras identificadas** lo pueden elevar de:
- "Sistema funcional de tesis" → **"Producto comercial listo para producción"**
- "Investigación local" → **"Contribución científica publicable"**

---

**Próximos pasos inmediatos:**
1. Priorizar ítems marcados 🔴 ALTA
2. Ejecutar `docs/EVALUATION_GUIDE.md` COMPLETO
3. Actualizar `docs/METRICS_AND_EVALUATION.md` con resultados reales
4. Preparar documentación de tesis con métricas sólidas

**¡Mucho éxito con tu tesis!** 🎓🚀
