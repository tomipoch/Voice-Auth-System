# Pipeline de Preprocesamiento de Audio

## 🎯 Resumen Ejecutivo

Cada módulo del sistema aplica su propio preprocesamiento especializado al audio antes de la inferencia. Aunque comparten operaciones comunes (resample, mono conversion, normalización), cada módulo tiene requisitos específicos según su arquitectura de red neuronal.

---

## 📊 Visión General del Flujo

```
Audio Bytes (Input)
    ↓
[Conversión a Tensor] → BytesIO → torchaudio.load()
    ↓
┌─────────────────────────────────────────────────────────────┐
│           PREPROCESAMIENTO COMÚN (3 MÓDULOS)               │
├─────────────────────────────────────────────────────────────┤
│  1. Resample a 16 kHz                                       │
│  2. Conversión a Mono                                       │
│  3. Normalización de Amplitud                               │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────┬─────────────────┬──────────────────┐
│ Antispoofing│ Speaker Recognition│ Text Verification│
│ (AASIST +   │ (ECAPA-TDNN)      │ (Wav2Vec2)        │
│ RawNet2)    │                   │                   │
└─────────────┴─────────────────┴──────────────────┘
```

---

## 🔬 Módulo 1: Antispoofing (AASIST + RawNet2)

### Archivo: `SpoofDetectorAdapter.py`

### Parámetros de Configuración:
```python
target_sample_rate = 16000  # Hz
device = "cuda" o "cpu"
```

### Pipeline de Preprocesamiento:

#### 1. **Carga de Audio**
```python
audio_io = io.BytesIO(audio_data)
waveform, sample_rate = torchaudio.load(audio_io)
```
- **Input:** Bytes del archivo de audio
- **Output:** Tensor de waveform + sample rate original

#### 2. **Resampling (si necesario)**
```python
if sample_rate != 16000:
    resampler = torchaudio.transforms.Resample(sample_rate, 16000)
    waveform = resampler(waveform)
```
- **Objetivo:** Estandarizar a 16 kHz (requerido por modelos)
- **Método:** Interpolación de torchaudio
- **Output:** Waveform a 16 kHz

#### 3. **Conversión a Mono**
```python
if waveform.shape[0] > 1:
    waveform = torch.mean(waveform, dim=0, keepdim=True)
```
- **Objetivo:** Reducir canales estéreo a mono
- **Método:** Promedio de canales
- **Output:** Waveform mono `[1, samples]`

#### 4. **Transferencia a Device**
```python
waveform = waveform.to(self.device)
```
- **Objetivo:** Mover tensor a GPU o CPU según configuración
- **Output:** Tensor en device objetivo

### Características Especiales:
- ✅ **Sin truncamiento:** Acepta audios de longitud variable
- ✅ **Sin padding:** Los modelos manejan longitud variable
- ✅ **Sin normalización explícita:** Los modelos esperan valores raw

### Output Final:
```python
torch.Tensor: shape [1, samples], dtype float32, range [-1, 1]
```

---

## 🎤 Módulo 2: Speaker Recognition (ECAPA-TDNN)

### Archivo: `SpeakerEmbeddingAdapter.py`

### Parámetros de Configuración:
```python
target_sample_rate = 16000  # Hz
target_length = 3.0  # seconds (referencia, no forzado)
MIN_AUDIO_DURATION_SEC = 1.0  # Mínimo aceptable
MAX_AUDIO_DURATION_SEC = 10.0  # Máximo aceptable
```

### Pipeline de Preprocesamiento:

#### 1. **Conversión de Formato (si necesario)**
```python
if format_lower != "wav":
    audio_data = convert_to_wav(audio_data, format_lower)
```
- **Objetivo:** Convertir MP3, OGG, etc. a WAV
- **Herramienta:** `audio_converter.py` (usa pydub)
- **Output:** Audio en formato WAV

#### 2. **Carga de Audio WAV**
```python
waveform, sample_rate = self._load_wav_audio(audio_data)
```
- **Método:** `wave` library o torchaudio
- **Output:** NumPy array + sample rate

#### 3. **Resampling (si necesario)**
```python
if sample_rate != 16000:
    waveform = torchaudio.functional.resample(
        torch.tensor(waveform), 
        orig_freq=sample_rate, 
        new_freq=16000
    ).numpy()
```
- **Objetivo:** Estandarizar a 16 kHz
- **Output:** Waveform a 16 kHz

#### 4. **Conversión a Mono**
```python
if len(waveform.shape) > 1:
    waveform = np.mean(waveform, axis=0)
```
- **Método:** Promedio de canales (NumPy)
- **Output:** Array 1D

#### 5. **Normalización de Amplitud**
```python
waveform = waveform / (np.max(np.abs(waveform)) + 1e-8)
```
- **Objetivo:** Escalar a rango [-1, 1]
- **Método:** División por valor máximo absoluto
- **Epsilon:** 1e-8 para evitar división por cero
- **Output:** Waveform normalizado

#### 6. **Ajuste de Longitud (Trim/Pad)**
```python
max_samples = int(10.0 * sample_rate)  # 10s max
min_samples = int(1.0 * sample_rate)   # 1s min

if len(waveform) > max_samples:
    # Trim: tomar porción central
    start = (len(waveform) - max_samples) // 2
    waveform = waveform[start:start + max_samples]
    
elif len(waveform) < min_samples:
    # Pad: rellenar con ceros
    pad_length = min_samples - len(waveform)
    waveform = np.pad(waveform, (0, pad_length), mode='constant')
```
- **Trim:** Si > 10s, tomar porción central de 10s
- **Pad:** Si < 1s, rellenar con ceros hasta 1s
- **Mantener:** Si entre 1s y 10s, dejar sin modificar

### Características Especiales:
- ✅ **Longitud variable:** Acepta entre 1s y 10s
- ✅ **Normalización obligatoria:** Crítico para ECAPA-TDNN
- ✅ **Centro del audio:** Al truncar, toma la parte central (mejor calidad)

### Output Final:
```python
np.ndarray: shape [samples], dtype float32, range [-1, 1]
Samples: entre 16,000 (1s) y 160,000 (10s)
```

---

## 🗣️ Módulo 3: Text Verification (Wav2Vec2 ASR)

### Archivo: `ASRAdapter.py`

### Parámetros de Configuración:
```python
target_sample_rate = 16000  # Hz
max_asr_samples = int(15.0 * 16000)  # 15 segundos máximo
```

### Pipeline de Preprocesamiento:

#### 1. **Carga de Audio**
```python
audio_io = io.BytesIO(audio_data)
waveform, sample_rate = torchaudio.load(audio_io)
```
- **Input:** Bytes del archivo de audio
- **Output:** Tensor de waveform + sample rate

#### 2. **Resampling (si necesario)**
```python
if sample_rate != 16000:
    resampler = torchaudio.transforms.Resample(sample_rate, 16000)
    waveform = resampler(waveform)
    sample_rate = 16000
```
- **Objetivo:** Estandarizar a 16 kHz
- **Output:** Waveform a 16 kHz

#### 3. **Conversión a Mono**
```python
if waveform.shape[0] > 1:
    waveform = torch.mean(waveform, dim=0, keepdim=True)
```
- **Método:** Promedio de canales
- **Output:** Waveform mono `[1, samples]`

#### 4. **Truncamiento (IMPORTANTE)**
```python
max_asr_samples = int(15.0 * sample_rate)  # 240,000 samples
if waveform.shape[1] > max_asr_samples:
    waveform = waveform[:, :max_asr_samples]  # Tomar inicio
```
- **Objetivo:** Limitar a 15 segundos (optimización de rendimiento)
- **Método:** Truncar al inicio (no centro)
- **Razón:** Bug fix crítico - antes limitaba a 5s causando WER 60%
- **Output:** Máximo 15s de audio

#### 5. **Normalización de Amplitud**
```python
max_val = waveform.abs().max()
if max_val > 0:
    waveform = waveform / max_val
```
- **Objetivo:** Escalar a rango [-1, 1]
- **Método:** División por valor máximo absoluto
- **Output:** Waveform normalizado

#### 6. **Transferencia a Device**
```python
waveform = waveform.to(self.device)
```
- **Objetivo:** Mover a GPU/CPU
- **Output:** Tensor en device objetivo

### Características Especiales:
- ✅ **Límite de 15s:** Optimización crítica para ASR
- ✅ **Truncar desde inicio:** Mejor para frases cortas al principio
- ✅ **Sin padding:** ASR maneja longitud variable
- ⚠️ **Bug histórico:** Antes limitaba a 5s (causaba WER 60% → 8%)

### Output Final:
```python
torch.Tensor: shape [1, samples], dtype float32, range [-1, 1]
Samples: máximo 240,000 (15s a 16kHz)
```

---

## 📋 Tabla Comparativa de Preprocesamiento

| Operación | Antispoofing | Speaker Recognition | Text Verification |
|-----------|--------------|---------------------|-------------------|
| **Sample Rate** | 16 kHz | 16 kHz | 16 kHz |
| **Resample** | ✅ Si necesario | ✅ Si necesario | ✅ Si necesario |
| **Mono Conversion** | ✅ Promedio | ✅ Promedio | ✅ Promedio |
| **Normalización** | ❌ No | ✅ Sí (max abs) | ✅ Sí (max abs) |
| **Truncamiento** | ❌ No | ✅ 10s (centro) | ✅ 15s (inicio) |
| **Padding** | ❌ No | ✅ Si < 1s | ❌ No |
| **Output Type** | torch.Tensor | np.ndarray | torch.Tensor |
| **Output Shape** | `[1, samples]` | `[samples]` | `[1, samples]` |
| **Device** | GPU/CPU | CPU (NumPy) | GPU/CPU |

---

## 🔧 Operaciones Comunes Detalladas

### 1. Resample (Todos los módulos)
```python
# Método: Resampler de torchaudio
resampler = torchaudio.transforms.Resample(
    orig_freq=sample_rate_original,
    new_freq=16000
)
waveform_resampled = resampler(waveform)
```
- **Algoritmo:** Interpolación sinc (alta calidad)
- **Preserva:** Información espectral dentro de Nyquist
- **Costo:** ~10-20ms por segundo de audio

### 2. Conversión a Mono (Todos los módulos)
```python
# Método: Promedio aritmético de canales
waveform_mono = torch.mean(waveform, dim=0, keepdim=True)
# o en NumPy:
waveform_mono = np.mean(waveform, axis=0)
```
- **Por qué promedio:** Preserva energía total
- **Alternativas:** Tomar solo canal izquierdo (más rápido, menos robusto)

### 3. Normalización de Amplitud (Speaker + ASR)
```python
# Método 1: Max absolute scaling (usado en el sistema)
waveform_norm = waveform / (waveform.abs().max() + epsilon)

# Método 2: RMS normalization (alternativa común)
rms = torch.sqrt(torch.mean(waveform ** 2))
waveform_norm = waveform / (rms + epsilon)
```
- **Max abs:** Mantiene dinámica original, escala lineal
- **RMS:** Iguala energía promedio, mejor para audios con silencio

---

## ⚡ Optimizaciones de Performance

### 1. Lazy Loading de Modelos
```python
# Los modelos se cargan solo la primera vez
if not self._model_loaded:
    self._load_model()
```
- **Ahorro:** ~2-5 segundos en inicio

### 2. Device Caching
```python
# Tensors permanecen en GPU entre inferencias
waveform = waveform.to(self.device)
```
- **Ahorro:** ~5-10ms por transferencia CPU→GPU

### 3. Batch Processing Potencial
```python
# Los modelos soportan batching
with torch.no_grad():
    scores = model.classify_batch(waveform)
```
- **Escalabilidad:** Procesamiento paralelo de múltiples audios

### 4. Thread Safety
```python
with self._lock:
    prediction = self._model.predict(waveform)
```
- **Protección:** Evita race conditions en requests concurrentes

---

## 🐛 Bugs Históricos y Fixes

### Bug #1: ASR Truncamiento a 5s (CRÍTICO)
**Problema:**
```python
# ANTES (causaba WER 60%)
max_asr_samples = int(5.0 * sample_rate)
start = (waveform.shape[1] - max_asr_samples) // 2  # Centro
waveform = waveform[:, start:start+max_asr_samples]
```

**Fix Aplicado:**
```python
# DESPUÉS (WER 8%)
max_asr_samples = int(15.0 * sample_rate)
waveform = waveform[:, :max_asr_samples]  # Inicio
```

**Impacto:**
- WER: 59.98% → 8.26%
- Genuinos aceptados: 2.8% → 80.6%
- **Root cause:** Frases del dataset son cortas, estaban al inicio del audio

---

## 📊 Métricas de Preprocesamiento

### Tiempo de Procesamiento (Promedio por audio de 3s):
| Operación | Antispoofing | Speaker | ASR |
|-----------|--------------|---------|-----|
| Load | ~5ms | ~5ms | ~5ms |
| Resample | ~10ms | ~10ms | ~10ms |
| Mono | ~2ms | ~2ms | ~2ms |
| Normalize | N/A | ~3ms | ~3ms |
| Trim/Pad | N/A | ~2ms | ~2ms |
| **Total** | **~17ms** | **~22ms** | **~22ms** |

### Memoria (por audio de 3s a 16kHz):
- **Waveform crudo:** 48,000 samples × 4 bytes = 192 KB
- **Tensor GPU:** 192 KB + overhead PyTorch (~50 KB) = ~240 KB
- **Batch de 10 audios:** ~2.4 MB (manejable en GPU)

---

## 🔍 Validación de Preprocesamiento

### Tests Unitarios Sugeridos:

#### 1. **Test de Sample Rate**
```python
def test_resample_accuracy():
    audio_44100 = generate_test_audio(sample_rate=44100)
    audio_16000 = preprocess(audio_44100)
    assert audio_16000.sample_rate == 16000
```

#### 2. **Test de Mono Conversion**
```python
def test_stereo_to_mono():
    audio_stereo = generate_stereo_audio()
    audio_mono = preprocess(audio_stereo)
    assert audio_mono.shape[0] == 1
```

#### 3. **Test de Normalización**
```python
def test_normalization_range():
    audio = preprocess(raw_audio)
    assert audio.abs().max() <= 1.0
```

#### 4. **Test de Truncamiento**
```python
def test_asr_max_length():
    audio_20s = generate_long_audio(duration=20.0)
    processed = asr_adapter._preprocess_audio(audio_20s)
    assert processed.shape[1] <= 240000  # 15s max
```

---

## 📚 Referencias

### Código Fuente:
- **Antispoofing:** `src/infrastructure/biometrics/SpoofDetectorAdapter.py` (líneas 311-330)
- **Speaker Recognition:** `src/infrastructure/biometrics/SpeakerEmbeddingAdapter.py` (líneas 167-230)
- **Text Verification:** `src/infrastructure/biometrics/ASRAdapter.py` (líneas 180-215)

### Librerías Utilizadas:
- **torchaudio:** v2.0+ para carga y resample
- **torch:** v2.0+ para operaciones de tensor
- **numpy:** v1.24+ para arrays en Speaker Recognition
- **wave:** stdlib para lectura WAV básica

### Configuración de Audio:
```python
# Constants en biometric_constants.py
EMBEDDING_DIMENSION = 192
MIN_AUDIO_DURATION_SEC = 1.0
MAX_AUDIO_DURATION_SEC = 10.0
```

---

## 🎓 Conclusión

El sistema implementa **preprocesamiento especializado por módulo**, con operaciones comunes pero parámetros adaptados a cada arquitectura de red neuronal:

- **Antispoofing:** Mínimo procesamiento, modelos manejan variabilidad
- **Speaker Recognition:** Normalización estricta, longitud controlada (1-10s)
- **Text Verification:** Truncamiento a 15s, normalización para mejor transcripción

Todas las transformaciones son **determinísticas y reproducibles**, garantizando consistencia entre enrollment y verification.
