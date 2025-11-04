# Pipeline de Entrenamiento - Modelos Biométricos

Este directorio contiene el pipeline completo de entrenamiento para los modelos biométricos especificados en el anteproyecto.

## 🎯 Modelos Implementados

### 📢 Reconocimiento de Hablantes
- **ECAPA-TDNN**: Modelo principal con 192 dimensiones de embedding
- **x-vector**: Modelo alternativo para comparación académica

### 🛡️ Anti-Spoofing  
- **AASIST**: Advanced Anti-Spoofing with Integrated Spectro-Temporal graph attention
- **RawNet2**: Red neuronal para audio crudo, detección de deepfakes
- **ResNet**: Variante CNN para detección de spoofing general

### 🗣️ ASR (Automatic Speech Recognition)
- **Lightweight ASR**: Modelo ligero para verificación de frases

## 📁 Estructura del Directorio

```
training/
├── configs/
│   └── training_config.yaml      # Configuraciones de entrenamiento
├── datasets/                     # Datasets descargados (no en git)
├── scripts/
│   ├── download_datasets.py      # Descarga automática de datasets
│   ├── preprocess_audio.py       # Preprocesamiento de audio
│   └── train_models.py          # Script principal de entrenamiento
├── models/                       # Modelos entrenados (no en git)
├── evaluation/
│   └── evaluate_models.py        # Evaluación y métricas
└── README.md                     # Esta documentación
```

## 🚀 Guía de Uso

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
pip install speechbrain torch torchaudio
pip install librosa soundfile pandas tqdm
pip install scikit-learn matplotlib seaborn
```

### 2. Descarga de Datasets

```bash
cd training/scripts
python download_datasets.py
```

**Datasets soportados:**
- **VoxCeleb1**: ~25 GB, 153K muestras
- **VoxCeleb2**: ~87 GB, 1M+ muestras  
- **ASVspoof 2019**: ~12 GB, 54K muestras
- **ASVspoof 2021**: ~8 GB, 200K muestras

### 3. Preprocesamiento

```bash
# VoxCeleb
python preprocess_audio.py --dataset voxceleb1 \
  --input-path ./datasets/voxceleb1 \
  --output-path ./datasets/voxceleb1_processed

# ASVspoof
python preprocess_audio.py --dataset asvspoof2019 \
  --input-path ./datasets/asvspoof2019 \
  --output-path ./datasets/asvspoof2019_processed \
  --protocol LA
```

### 4. Entrenamiento

#### ECAPA-TDNN (Principal)
```bash
python train_models.py --model ecapa_tdnn \
  --config ../configs/training_config.yaml \
  --output ../models
```

#### x-vector (Alternativo)
```bash
python train_models.py --model x_vector \
  --config ../configs/training_config.yaml \
  --output ../models
```

#### Anti-Spoofing
```bash
# AASIST
python train_models.py --model aasist \
  --config ../configs/training_config.yaml \
  --output ../models

# RawNet2
python train_models.py --model rawnet2 \
  --config ../configs/training_config.yaml \
  --output ../models

# ResNet
python train_models.py --model resnet_antispoofing \
  --config ../configs/training_config.yaml \
  --output ../models
```

#### ASR Ligero
```bash
python train_models.py --model lightweight_asr \
  --config ../configs/training_config.yaml \
  --output ../models
```

### 5. Evaluación

```bash
cd ../evaluation

# Speaker Verification
python evaluate_models.py --task speaker_verification \
  --scores embeddings.npy \
  --labels trials.txt \
  --output results/speaker

# Anti-Spoofing
python evaluate_models.py --task anti_spoofing \
  --scores scores.npy \
  --labels labels.npy \
  --output results/antispoofing
```

## 📊 Métricas de Evaluación

### Reconocimiento de Hablantes
- **EER** (Equal Error Rate): Tasa de error cuando FPR = FNR
- **min-DCF**: Función de costo de detección mínima
- **Cllr**: Costo de log-likelihood ratio calibrado

### Anti-Spoofing
- **EER**: Equal Error Rate para bonafide vs spoof
- **t-DCF**: Tandem Detection Cost Function
- **AUC**: Area Under ROC Curve

## ⚙️ Configuración

El archivo `configs/training_config.yaml` contiene todas las configuraciones:

```yaml
ecapa_tdnn:
  model:
    embedding_dim: 192
    channels: [512, 512, 512, 512, 1536]
  training:
    batch_size: 32
    num_epochs: 100
    learning_rate: 0.001
```

### Parámetros Principales

| Modelo | Batch Size | Epochs | Learning Rate | Dataset |
|--------|------------|--------|---------------|---------|
| ECAPA-TDNN | 32 | 100 | 0.001 | VoxCeleb1 |
| x-vector | 64 | 80 | 0.0005 | VoxCeleb1 |
| AASIST | 24 | 50 | 0.0001 | ASVspoof2019 |
| RawNet2 | 16 | 60 | 0.0003 | ASVspoof2019 |
| ResNet | 32 | 40 | 0.001 | ASVspoof2021 |

## 🔧 Opciones Avanzadas

### Entrenamiento Distribuido
```bash
# Múltiples GPUs
python train_models.py --model ecapa_tdnn --distributed
```

### Validación Cruzada
```bash
# Solo generar scripts (dry run)
python train_models.py --model ecapa_tdnn --dry-run
```

### Continuar Entrenamiento
```bash
# Desde checkpoint
python train_models.py --model ecapa_tdnn --resume path/to/checkpoint.ckpt
```

## 📈 Resultados Esperados

### Benchmarks Académicos

| Modelo | Dataset | EER (%) | min-DCF |
|--------|---------|---------|---------|
| ECAPA-TDNN | VoxCeleb1 | 1.01 | 0.0581 |
| x-vector | VoxCeleb1 | 3.30 | 0.153 |
| AASIST | ASVspoof2019 LA | 0.83 | 0.0275 |
| RawNet2 | ASVspoof2019 PA | 2.48 | 0.0734 |

## 🚨 Consideraciones Importantes

### Recursos Computacionales
- **GPU recomendada**: NVIDIA RTX 3080+ (12GB VRAM)
- **RAM**: Mínimo 32 GB para datasets grandes
- **Almacenamiento**: ~150 GB para todos los datasets

### Tiempo de Entrenamiento
- **ECAPA-TDNN**: ~24-48 horas en GPU
- **Anti-spoofing**: ~12-24 horas por modelo
- **ASR**: ~8-16 horas

### Datasets Académicos
Los datasets requieren registro académico:
- **VoxCeleb**: http://www.robots.ox.ac.uk/~vgg/data/voxceleb/
- **ASVspoof**: https://www.asvspoof.org/

## 🔄 Integración con Sistema Principal

Una vez entrenados, los modelos se integran automáticamente:

```python
# Los adapters cargarán los modelos entrenados
from infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

adapter = SpeakerEmbeddingAdapter(model_path="./training/models/ecapa_tdnn/save/model.ckpt")
```

## 📚 Referencias Académicas

1. **ECAPA-TDNN**: Desplanques et al., "ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification", INTERSPEECH 2020
2. **AASIST**: Jung et al., "AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks", ICASSP 2022
3. **RawNet2**: Tak et al., "RawNet2: Better Generalization to Unseen Attacks for Utterance-level Anti-spoofing Models", INTERSPEECH 2021

## 🆘 Troubleshooting

### Errores Comunes

1. **CUDA Out of Memory**: Reducir batch_size en config
2. **Dataset no encontrado**: Verificar rutas en download_datasets.py
3. **Importación de SpeechBrain**: `pip install speechbrain==0.5.14`

### Logs y Depuración
```bash
# Logs detallados
python train_models.py --model ecapa_tdnn --verbose

# Solo generar configuración
python train_models.py --model ecapa_tdnn --dry-run
```