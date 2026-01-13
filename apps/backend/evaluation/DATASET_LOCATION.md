# Ubicación de Datasets

Los datasets para evaluación están **externalizados** en una ubicación fuera de `apps/backend/evaluation/`.

## 📍 Ubicación

**Ruta:** `infra/evaluation/dataset/`

Ruta completa desde el proyecto:
```
/Users/tomipoch/Documents/Nueva carpeta con elementos/Ultimo Semestre/Tesis/Proyecto/infra/evaluation/dataset/
```

## 📊 Estructura Actual

```
infra/evaluation/dataset/
├── recordings/
│   └── auto_recordings_20251218/
│       ├── anachamorromunoz/
│       ├── ft_fernandotomas/
│       ├── piapobletech/
│       └── rapomo3/
│
├── attacks/                        # Ataques sintéticos (TTS, etc.)
│   ├── anachamorromunoz/
│   ├── ft_fernandotomas/
│   ├── piapobletech/
│   └── rapomo3/
│
└── cloning/                        # Ataques de clonación de voz
    ├── anachamorromunoz/
    ├── ft_fernandotomas/
    ├── piapobletech/
    └── rapomo3/
```

## 👥 Usuarios en el Dataset

El dataset contiene grabaciones de **4 usuarios:**

1. **anachamorromunoz**
2. **ft_fernandotomas**
3. **piapobletech**
4. **rapomo3**

## 🔧 Configuración en Scripts

Para acceder a los datasets desde los scripts de evaluación, usa:

```python
from pathlib import Path

# Ruta base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Ruta al dataset externo
DATASET_BASE = PROJECT_ROOT / "infra" / "evaluation" / "dataset"

# Ejemplos de uso
recordings_dir = DATASET_BASE / "recordings" / "auto_recordings_20251218"
attacks_dir = DATASET_BASE / "attacks"
cloning_dir = DATASET_BASE / "cloning"
```

## 📝 Tipos de Datos

### 1. Recordings (Grabaciones Genuinas)
Ubicación: `recordings/auto_recordings_20251218/[usuario]/`
- Grabaciones auténticas de cada usuario
- Útil para enrollment y pruebas genuinas

### 2. Attacks (Ataques Sintéticos)
Ubicación: `attacks/[usuario]/`
- Ataques generados por TTS u otros métodos sintéticos
- Para evaluar detección de anti-spoofing

### 3. Cloning (Ataques de Clonación)
Ubicación: `cloning/[usuario]/`
- Ataques de clonación de voz
- Para evaluar robustez contra voice cloning

## ⚠️ Importante

- **No mover** los datasets a `apps/backend/evaluation/`
- Los datasets están externalizados por **tamaño** y **organización**
- Los scripts de evaluación deben **apuntar a la ubicación externa**
- Mantener esta estructura para **reproducibilidad**

## 🔄 Actualización de Scripts

Los 4 scripts de evaluación necesitarán actualizarse para usar esta ruta:

1. `evaluate_speaker_recognition.py`
2. `evaluate_text_verification.py`
3. `evaluate_antispoofing.py`
4. `evaluate_complete_system.py`

Cada script debe incluir al inicio:

```python
# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATASET_BASE = PROJECT_ROOT / "infra" / "evaluation" / "dataset"
```

---

**Última actualización:** 13 de enero de 2026
