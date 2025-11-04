# Scripts de Entrenamiento - Organización

Este directorio contiene todos los scripts necesarios para el entrenamiento de modelos biométricos, organizados por funcionalidad.

## 📁 Estructura Organizada

```
training/scripts/
├── train_models.py              # 🚀 Script principal de entrenamiento
├── data_generation/             # 🧪 Generación de datos sintéticos
│   ├── create_synthetic_dataset.py     # Dataset básico para pruebas
│   └── create_enhanced_dataset.py      # Dataset mejorado y realista
├── downloading/                 # 📥 Descarga de datasets académicos
│   ├── download_datasets.py            # Descargador principal (requiere registro)
│   ├── download_librispeech.py         # LibriSpeech (público)
│   ├── dataset_guide.py               # Guía de datasets disponibles
│   └── dataset_registration_guide.py   # Guía de registro académico
└── utils/                      # 🔧 Utilidades y herramientas
    ├── preprocess_audio.py             # Preprocesamiento de audio
    └── test_training_pipeline.py       # Test del pipeline de entrenamiento
```

## 🎯 Scripts Principales

### 🚀 Entrenamiento
- `train_models.py` - Script principal para entrenar cualquier modelo

### 🧪 Datos Sintéticos (Para desarrollo)
- `data_generation/create_synthetic_dataset.py` - Dataset básico (5 speakers)
- `data_generation/create_enhanced_dataset.py` - Dataset mejorado (20 speakers, más realismo)

### 📥 Datasets Académicos (Para producción)
- `downloading/download_librispeech.py` - Descarga LibriSpeech (público, 6.9 GB)
- `downloading/download_datasets.py` - VoxCeleb/ASVspoof (requiere registro)
- `downloading/dataset_guide.py` - Guía de todos los datasets disponibles

### 🔧 Utilidades
- `utils/preprocess_audio.py` - Preprocesamiento estándar de audio
- `utils/test_training_pipeline.py` - Verificación del pipeline

## 🚀 Uso Típico

### 1. Desarrollo/Pruebas Rápidas
```bash
# Crear datos sintéticos
python data_generation/create_enhanced_dataset.py

# Verificar pipeline
python utils/test_training_pipeline.py

# Entrenar modelo
python train_models.py --model ecapa_tdnn --config ../configs/training_config.yaml
```

### 2. Entrenamiento con Datos Reales
```bash
# Descargar dataset público
python downloading/download_librispeech.py

# O registrarse para datasets académicos
python downloading/dataset_guide.py

# Preprocesar datos
python utils/preprocess_audio.py --dataset voxceleb1 --input-path ../datasets/voxceleb1

# Entrenar
python train_models.py --model ecapa_tdnn --config ../configs/training_config.yaml
```

## ⚙️ Configuración

Todos los scripts usan las configuraciones en `../configs/training_config.yaml`.
Los modelos entrenados se guardan en `../models/`.
Los datasets se almacenan en `../datasets/`.

## 📊 Datasets Soportados

- **VoxCeleb1/2**: Speaker recognition (requiere registro académico)
- **ASVspoof 2019/2021**: Anti-spoofing (requiere registro académico)  
- **LibriSpeech**: ASR (público, sin registro)
- **Sintético**: Generado localmente para desarrollo