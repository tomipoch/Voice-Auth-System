# Proyecto Backend - Sistema Biométrico de Voz

## 📁 Estructura Organizada del Proyecto

```
Backend/
├── 📂 src/                                 # Código fuente principal
│   ├── 📂 api/                            # Controladores REST
│   │   ├── enrollment_controller.py
│   │   ├── verification_controller.py
│   │   ├── challenge_controller.py
│   │   └── middleware/
│   ├── 📂 application/                    # Servicios de aplicación
│   │   ├── enrollment_service.py
│   │   ├── verification_service.py
│   │   ├── challenge_service.py
│   │   ├── dto/                          # Data Transfer Objects
│   │   └── policies/
│   ├── 📂 domain/                        # Lógica de dominio
│   │   ├── model/                        # Modelos de dominio
│   │   ├── services/                     # Servicios de dominio
│   │   ├── repositories/                 # Interfaces de repositorio
│   │   └── policies/
│   ├── 📂 infrastructure/                # Implementaciones técnicas
│   │   ├── biometrics/                   # Motor biométrico
│   │   │   ├── SpeakerEmbeddingAdapter.py      # ECAPA-TDNN, x-vector
│   │   │   ├── SpoofDetectorAdapter.py         # AASIST, RawNet2, ResNet
│   │   │   ├── ASRAdapter.py                   # Lightweight ASR
│   │   │   ├── VoiceBiometricEngineFacade.py   # Facade principal
│   │   │   └── model_manager.py                # Gestión de modelos
│   │   └── persistence/                  # Acceso a datos
│   └── 📂 shared/                        # Código compartido
│       ├── types/
│       ├── constants/
│       └── utils/
├── 📂 training/                          # **🆕 REORGANIZADO**
│   ├── 📂 configs/                       # Configuraciones de entrenamiento
│   │   └── training_config.yaml
│   ├── 📂 datasets/                      # Datasets (no en git)
│   │   ├── speaker_recognition/          # Datos sintéticos actuales
│   │   ├── anti_spoofing/
│   │   └── librispeech/                  # Si se descarga
│   ├── 📂 models/                        # Modelos entrenados (no en git)
│   │   ├── ecapa_tdnn/
│   │   ├── x_vector/
│   │   └── aasist/
│   ├── 📂 scripts/                       # **🔧 REORGANIZADO POR FUNCIÓN**
│   │   ├── train_models.py              # 🚀 Script principal
│   │   ├── quick_start.py               # 🆕 Inicio rápido
│   │   ├── 📂 data_generation/          # 🧪 Datos sintéticos
│   │   │   ├── create_synthetic_dataset.py
│   │   │   └── create_enhanced_dataset.py
│   │   ├── 📂 downloading/              # 📥 Descarga datasets
│   │   │   ├── download_datasets.py
│   │   │   ├── download_librispeech.py
│   │   │   ├── dataset_guide.py
│   │   │   └── dataset_registration_guide.py
│   │   ├── 📂 utils/                    # 🔧 Utilidades
│   │   │   ├── preprocess_audio.py
│   │   │   └── test_training_pipeline.py
│   │   └── README.md                    # Documentación de scripts
│   ├── 📂 evaluation/                   # Evaluación y métricas
│   │   └── evaluate_models.py
│   └── README.md                        # Documentación principal
├── 📂 tests/                            # **🔧 REORGANIZADO**
│   ├── 📂 unit/                         # Tests unitarios
│   ├── 📂 integration/                  # Tests de integración
│   ├── 📂 models/                       # Tests de modelos específicos
│   ├── 📂 training/                     # 🆕 Tests de entrenamiento
│   └── 📂 manual/                       # 🆕 Tests manuales
│       └── test_simple.py
├── 📂 scripts/                          # **🔧 REORGANIZADO**
│   ├── 📂 dev/                          # 🆕 Scripts de desarrollo
│   │   └── dev_server.py
│   ├── init-db.sql
│   ├── purge-job.sql
│   └── seed_data.sql
├── 📂 models/                           # Modelos pre-entrenados (SpeechBrain)
├── 📂 docs/                             # Documentación
├── 📂 logs/                             # Logs del sistema
├── 📂 monitoring/                       # Configuración de monitoreo
└── 📄 Archivos de configuración
    ├── requirements.txt
    ├── training_requirements.txt
    ├── docker-compose.yml
    ├── Dockerfile
    └── README.md
```

## 🎯 Principales Mejoras de Organización

### ✅ **ANTES vs DESPUÉS**

| **ANTES** | **DESPUÉS** |
|-----------|-------------|
| `test_simple.py` en raíz | `tests/manual/test_simple.py` |
| `dev_server.py` en raíz | `scripts/dev/dev_server.py` |
| Scripts mezclados en `training/scripts/` | Organizados por función en subcarpetas |
| Tests de training mezclados | `tests/training/` específico |
| Datasets en ubicaciones múltiples | Centralizados en `training/datasets/` |

### 🔧 **SCRIPTS REORGANIZADOS**

#### **Por Función:**
- **🚀 Principales**: `train_models.py`, `quick_start.py`
- **🧪 Generación**: `data_generation/create_*.py`
- **📥 Descarga**: `downloading/download_*.py`, `dataset_guide.py`
- **🔧 Utilidades**: `utils/preprocess_*.py`, `test_*.py`

#### **Por Uso:**
- **Desarrollo**: Scripts en `data_generation/` y `utils/`
- **Producción**: Scripts en `downloading/` y archivo principal
- **Testing**: Scripts en `utils/` y directorio `tests/`

## 🚀 Inicio Rápido

```bash
# Navegar a scripts de entrenamiento
cd training/scripts

# Usar script de inicio rápido
python quick_start.py

# O directamente crear datos y entrenar
python data_generation/create_enhanced_dataset.py
python train_models.py --model ecapa_tdnn
```

## 📚 Documentación

- `training/README.md` - Documentación completa de entrenamiento
- `training/scripts/README.md` - Guía específica de scripts
- `docs/` - Documentación técnica del proyecto

## 🧪 Testing

- Tests unitarios: `tests/unit/`
- Tests de integración: `tests/integration/`
- Tests de modelos: `tests/models/`
- Tests de entrenamiento: `tests/training/`
- Tests manuales: `tests/manual/`

La estructura está ahora completamente organizada y lista para desarrollo eficiente.