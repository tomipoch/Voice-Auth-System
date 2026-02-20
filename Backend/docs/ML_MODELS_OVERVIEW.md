# Modelos de Machine Learning - Voice Biometrics System

## Resumen

Este documento detalla los modelos de Machine Learning utilizados en el sistema de autenticación biométrica por voz, incluyendo sus datasets de entrenamiento, propósitos y características técnicas.

---

## Tabla de Modelos

| **Modelo** | **Propósito** | **Dataset de Entrenamiento** | **Fuente** | **Dimensión Embeddings** |
|-----------|---------------|------------------------------|-----------|-------------------------|
| **ECAPA-TDNN** | Speaker Recognition (Reconocimiento de locutor) | VoxCeleb 1 & 2 | SpeechBrain (`speechbrain/spkrec-ecapa-voxceleb`) | 192/512-D |
| **x-vector** | Speaker Recognition alternativo (comparación académica) | VoxCeleb 1 & 2 | SpeechBrain (`speechbrain/spkrec-xvect-voxceleb`) | 512-D |
| **Wav2Vec2 ASR** | Automatic Speech Recognition (verificación de texto) | CommonVoice 14 (Español) | HuggingFace/SpeechBrain (`speechbrain/asr-wav2vec2-commonvoice-14-es`) | N/A (texto) |
| **AASIST** | Anti-Spoofing (detección de voz sintética) | ASVspoof 2019/2021 LA | SpeechBrain + Local weights | N/A (score) |
| **RawNet2** | Anti-Spoofing (detección de deepfakes) | ASVspoof 2019/2021 LA | SpeechBrain + Local weights | N/A (score) |
| **Nes2Net** | Anti-Spoofing (general purpose) | ASVspoof 2021 DF | Local weights | N/A (score) |

---

## Detalles por Categoría

### 1. Speaker Recognition (Reconocimiento de Locutor)

#### ECAPA-TDNN (Modelo Principal)
- **Arquitectura**: Emphasized Channel Attention, Propagation and Aggregation Time Delay Neural Network
- **Dataset**: VoxCeleb 1 & 2
  - ~7,000 locutores únicos
  - ~1.2M utterances
  - Datos de YouTube con variaciones de calidad
- **Uso en el sistema**: 
  - Extracción de embeddings de voz durante enrollment
  - Comparación de embeddings durante verification
  - Generación de voiceprint del usuario
- **Performance**: 
  - EER (Equal Error Rate): ~0.87% en VoxCeleb1-O
  - Embedding dimension: Configurable (192 o 512-D)
- **Repositorio**: `models/speaker-recognition/ecapa_tdnn/`

#### x-vector (Modelo Alternativo)
- **Arquitectura**: DNN-based x-vector extractor
- **Dataset**: VoxCeleb 1 & 2
- **Uso en el sistema**: 
  - Comparación académica con ECAPA-TDNN
  - Análisis de diferentes arquitecturas
  - Disponible mediante `switch_model_type()`
- **Performance**: 
  - EER: ~3.1% en VoxCeleb1-O
  - Embedding dimension: 512-D
- **Repositorio**: `models/speaker-recognition/x_vector/`

---

### 2. ASR (Automatic Speech Recognition)

#### Wav2Vec2 para Español
- **Arquitectura**: Wav2Vec2-based CTC model
- **Dataset**: CommonVoice 14 (Español)
  - Corpus de voz crowdsourced
  - Múltiples acentos del español
  - ~1,000 horas de audio validado
- **Uso en el sistema**:
  - Transcripción de audio durante enrollment y verification
  - Validación de que el usuario dice la frase correcta
  - Cálculo de similitud entre frase esperada y reconocida
- **Performance**:
  - WER (Word Error Rate): ~10-15% en español general
  - Sample rate: 16kHz
- **Repositorio**: `models/text-verification/lightweight_asr/`
- **Fuente**: `speechbrain/asr-wav2vec2-commonvoice-14-es`

**Nota**: El threshold de similitud de frases se configura en `DEFAULT_PHRASE_MATCH_THRESHOLD` (default: 0.7)

---

### 3. Anti-Spoofing (Detección de Ataques)

El sistema utiliza un **ensemble de 3 modelos** para detección robusta de spoofing:

#### AASIST (Primary Anti-Spoofing Model)
- **Arquitectura**: Graph Attention Network con análisis espectral
- **Dataset**: ASVspoof 2019 & 2021 Logical Access (LA)
  - TTS systems (Text-to-Speech)
  - Voice conversion
  - ~100k utterances sintéticas
- **Peso en ensemble**: 40%
- **Fortalezas**: 
  - Excelente contra voz sintética (TTS)
  - Detección de artefactos espectrales
- **Performance**: 
  - EER: ~0.83% en ASVspoof 2021 LA
  - t-DCF: 0.0275
- **Repositorio**: `models/anti-spoofing/aasist/`

#### RawNet2 (Deepfake Detection)
- **Arquitectura**: End-to-end CNN sobre forma de onda raw
- **Dataset**: ASVspoof 2019 & 2021 LA
  - Neural vocoder deepfakes
  - Replay attacks
  - Voice cloning
- **Peso en ensemble**: 35%
- **Fortalezas**:
  - Especializado en deepfakes de voz
  - Detección de replay attacks
  - Análisis temporal de forma de onda
- **Performance**:
  - EER: ~1.5% en ASVspoof 2021 LA
- **Repositorio**: `models/anti-spoofing/rawnet2/`

#### Nes2Net (General Purpose)
- **Arquitectura**: Nested Residual Network
- **Dataset**: ASVspoof 2021 Deepfake (DF)
  - Múltiples tipos de ataques
  - Scenarios de audio comprimido
- **Peso en ensemble**: 25%
- **Fortalezas**:
  - Detección general de ataques
  - Robusto a compresión de audio
- **Performance**:
  - EER: ~2.0% en ASVspoof 2021 DF
- **Repositorio**: `models/anti-spoofing/nes2net/`

#### Estrategia de Ensemble

```python
spoof_score = (
    aasist_score * 0.40 +
    rawnet2_score * 0.35 +
    nes2net_score * 0.25
)

is_spoofed = spoof_score >= DEFAULT_SPOOF_THRESHOLD  # 0.5
```

El ensemble proporciona:
- **Mayor precisión**: Combina fortalezas de cada modelo
- **Robustez**: Reduce falsos positivos/negativos
- **Confianza**: Calcula confianza basada en acuerdo entre modelos

---

## Datasets Resumidos

| **Dataset** | **Propósito** | **Tamaño** | **Modelos que lo usan** |
|------------|--------------|-----------|------------------------|
| **VoxCeleb 1 & 2** | Speaker Recognition | ~7k locutores, 1.2M utterances | ECAPA-TDNN, x-vector |
| **CommonVoice 14 (ES)** | ASR en Español | ~1000 horas | Wav2Vec2 ASR |
| **ASVspoof 2019 LA** | Anti-Spoofing Logical Access | ~100k sintéticas | AASIST, RawNet2 |
| **ASVspoof 2021 LA** | Anti-Spoofing actualizado | Expandido | AASIST, RawNet2 |
| **ASVspoof 2021 DF** | Anti-Spoofing Deepfakes | Múltiples ataques | Nes2Net |

---

## Gestión de Modelos

### Descarga Automática
Los modelos se descargan automáticamente al primer uso mediante `model_manager.py`:

```python
from .infrastructure.biometrics.model_manager import model_manager

# Descarga ECAPA-TDNN si no existe
model_manager.download_model("ecapa_tdnn")

# Obtener ruta del modelo
model_path = model_manager.get_model_path("ecapa_tdnn")
```

### Modelos Locales vs SpeechBrain

El sistema soporta dos modos:

1. **Local weights** (preferido): 
   - Modelos TorchScript pre-descargados en `models/`
   - Carga más rápida
   - Sin dependencia de internet

2. **SpeechBrain downloads** (fallback):
   - Descarga automática desde HuggingFace
   - Primera ejecución más lenta
   - Requiere internet

---

## Configuración

### Device (CPU/GPU)

```python
# Configurar en adaptadores
speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
spoof_adapter = SpoofDetectorAdapter(use_gpu=True)
asr_adapter = ASRAdapter(use_gpu=True)
```

### Thresholds

```python
# En biometric_constants.py
SIMILARITY_THRESHOLD = 0.60  # Speaker verification
ANTI_SPOOFING_THRESHOLD = 0.5  # Spoof detection
DEFAULT_PHRASE_MATCH_THRESHOLD = 0.7  # ASR phrase matching
```

---

## Performance del Sistema

### Métricas Estimadas (End-to-End)

| Métrica | Valor |
|---------|-------|
| **FAR** (False Accept Rate) | ~1-2% |
| **FRR** (False Reject Rate) | ~3-5% |
| **Spoof Detection Rate** | ~97-98% |
| **ASR Accuracy** (Español) | ~85-90% |
| **Average Processing Time** | 2-4 segundos/audio |

**Nota**: Métricas estimadas basadas en performance de modelos individuales. Requiere evaluación con dataset propio para métricas exactas.

---

## Referencias

### Papers

1. **ECAPA-TDNN**: [ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification](https://arxiv.org/abs/2005.07143)
2. **AASIST**: [AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks](https://arxiv.org/abs/2110.01200)
3. **RawNet2**: [End-to-End anti-spoofing with RawNet2](https://arxiv.org/abs/2011.01108)
4. **Wav2Vec2**: [wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations](https://arxiv.org/abs/2006.11477)

### Recursos

- **SpeechBrain**: https://speechbrain.github.io/
- **VoxCeleb**: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/
- **ASVspoof**: https://www.asvspoof.org/
- **CommonVoice**: https://commonvoice.mozilla.org/

---

**Última actualización**: Diciembre 2024  
**Versión del documento**: 1.0.0
