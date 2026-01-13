# Sistema de Evaluación Biométrica - Nueva Estructura

**Fecha de reorganización:** 13 de enero de 2026  
**Estado:** ✅ Estructura limpia y organizada

---

## 📁 Estructura Actual

```
evaluation/
├── anterior/                       # 📦 Evaluaciones anteriores (referencia)
│   ├── scripts/                    # Scripts antiguos de evaluación
│   ├── results/                    # Resultados previos
│   ├── plots/                      # Gráficos generados anteriormente
│   ├── docs/                       # Documentación antigua
│   └── README_OLD.md              # README anterior
│
├── evaluate_speaker_recognition.py # ✅ Script 1: Reconocimiento de Locutor
├── evaluate_text_verification.py  # ✅ Script 2: Verificación de Texto
├── evaluate_antispoofing.py        # ✅ Script 3: Anti-Spoofing
├── evaluate_complete_system.py     # ✅ Script 4: Sistema Completo
│
├── results/                        # 📈 Resultados de evaluación (se generan)
│
├── EVALUATION_README.md           # 📖 Documentación completa
└── README.md                      # Este archivo
```

**📊 Datasets Externos:**

Los datasets para evaluación están en:  
`infra/evaluation/dataset/` (fuera de apps/backend)

```
infra/evaluation/dataset/
├── recordings/                     # Grabaciones genuinas
├── attacks/                        # Ataques sintéticos (TTS, etc.)
└── cloning/                        # Ataques de clonación de voz
```

---

## 🎯 Scripts de Evaluación (4 en total)

### 1. Reconocimiento de Locutor
**Archivo:** `evaluate_speaker_recognition.py`

**Métricas:**
- ✅ FRR (False Rejection Rate) - Menor es mejor (~0%)
- ✅ FAR (False Acceptance Rate) - Menor es mejor (~0%)
- ✅ EER (Equal Error Rate) - Menor es mejor (~0%)

**Ejecutar:**
```bash
python evaluation/evaluate_speaker_recognition.py
```

---

### 2. Verificación de Texto (ASR)
**Archivo:** `evaluate_text_verification.py`

**Métricas:**
- ✅ WER (Word Error Rate) - Menor es mejor (~0%)
- ✅ Transcription Accuracy - Mayor es mejor (~100%)
- ✅ Phrase Matching Accuracy - Mayor es mejor (~100%)

**Ejecutar:**
```bash
python evaluation/evaluate_text_verification.py
```

---

### 3. Anti-Spoofing
**Archivo:** `evaluate_antispoofing.py`

**Métricas:**
- ✅ APCER (Attack Classification Error) - Menor es mejor (~0%)
- ✅ BPCER (Genuine Classification Error) - Menor es mejor (~0%)
- ✅ ACER (Average Classification Error) - Menor es mejor (~0%)

**Ejecutar:**
```bash
python evaluation/evaluate_antispoofing.py
```

---

### 4. Sistema Completo
**Archivo:** `evaluate_complete_system.py`

**Métricas:**

**Eficiencia:**
- ✅ RTF (Real-Time Factor) - Menor es mejor (~0)
- ✅ TTP (Total Processing Time) - ~2 segundos es bueno

**Robustez:**
- ✅ SNR vs Error - Sensibilidad al ruido
- ✅ Duración vs EER - Sensibilidad a duración del audio

**Calibración:**
- ✅ t-DCF (tandem Detection Cost Function) - Menor es mejor (~0%)

**Ejecutar:**
```bash
python evaluation/evaluate_complete_system.py
```

---

## 📊 Ubicación de Datasets

Los datasets están externalizados en:  
**`/infra/evaluation/dataset/`**

Estructura actual:
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

**Nota:** Los scripts de evaluación deberán configurarse para apuntar a esta ubicación externa.

---

## 📈 Resultados

Los resultados se generan en `results/` con dos formatos:

- **`.txt`** - Reportes legibles para humanos
- **`.json`** - Métricas estructuradas para procesamiento

```
results/
├── speaker_recognition_evaluation.txt
├── speaker_recognition_evaluation.json
├── text_verification_evaluation.txt
├── text_verification_evaluation.json
├── antispoofing_evaluation.txt
├── antispoofing_evaluation.json
├── complete_system_evaluation.txt
└── complete_system_evaluation.json
```

---

## 🚀 Ejecución Rápida

Para ejecutar todos los scripts:

```bash
cd apps/backend

# Ejecutar todos en secuencia
python evaluation/evaluate_speaker_recognition.py
python evaluation/evaluate_text_verification.py
python evaluation/evaluate_antispoofing.py
python evaluation/evaluate_complete_system.py
```

---

## 📦 Carpeta `anterior/`

Contiene todo el trabajo previo de evaluación:
- ✅ 35+ scripts antiguos de evaluación
- ✅ Resultados históricos
- ✅ Gráficos generados anteriormente
- ✅ Documentación previa

**Nota:** Esta carpeta se mantiene solo como referencia y no debe modificarse.

---

## 📚 Documentación Completa

Para información detallada sobre cada script, estructura de datasets, interpretación de métricas, y ejemplos, consulta:

**📖 [EVALUATION_README.md](EVALUATION_README.md)**

---

## 🔄 Cambios Principales

### Nueva Estructura (Enero 2026)
- ✅ **4 scripts** enfocados (vs 35+ anteriores)
- ✅ Métricas claramente definidas
- ✅ Estructura de datasets documentada
- ✅ Reportes duales (TXT + JSON)
- ✅ Todo el contenido anterior organizado en `anterior/`

### Beneficios
- ✅ Más fácil de entender y mantener
- ✅ Scripts independientes y reutilizables
- ✅ Métricas alineadas con estándares (ISO/IEC)
- ✅ Documentación clara y concisa
- ✅ Resultados estructurados para tesis

---

## ⚠️ Importante

1. **No modificar la carpeta `anterior/`** - Es solo referencia
2. **Preparar datasets** antes de ejecutar los scripts
3. **GPU recomendada** para mejor rendimiento
4. **Revisar logs** durante la ejecución para detectar errores

---

## 🎓 Para la Tesis

Esta estructura limpia está diseñada para:
- ✅ Generar resultados reproducibles
- ✅ Documentar métricas estándar
- ✅ Facilitar la escritura de capítulos
- ✅ Proporcionar datos estructurados para tablas y gráficos

---

**Última actualización:** 13 de enero de 2026
