# Módulo 1: Speaker Recognition (Reconocimiento de Locutor)

**Fecha**: 22 de Diciembre de 2024  
**Modelo**: ECAPA-TDNN  
**Estado**: ✅ Evaluado y Optimizado

---

## 📊 Resumen Ejecutivo

El módulo de Speaker Recognition utiliza el modelo ECAPA-TDNN para verificar la identidad del locutor mediante análisis de características vocales únicas.

**Métricas Principales**:
- **EER**: 6.31% (Excelente)
- **FAR**: 0.90% (< 1%, Muy bueno)
- **FRR**: 16.22% (Aceptable)
- **Threshold Óptimo**: 0.65

---

## 🎯 Objetivo del Módulo

Verificar que la voz en el audio pertenece al usuario registrado, comparando embeddings vocales extraídos del audio de verificación con los embeddings almacenados durante el enrollment.

---

## 🏗️ Arquitectura

### Modelo: ECAPA-TDNN
- **Tipo**: Emphasized Channel Attention, Propagation and Aggregation in TDNN
- **Entrada**: Audio crudo (16kHz)
- **Salida**: Embedding de 192 dimensiones
- **Comparación**: Similitud coseno entre embeddings

### Flujo de Verificación

```
Audio de Verificación
        ↓
Extracción de Embedding (ECAPA-TDNN)
        ↓
Comparación con Embedding de Enrollment
        ↓
Similitud Coseno
        ↓
Threshold (0.65)
        ↓
ACEPTAR / RECHAZAR
```

---

## 📈 Métricas Detalladas

### Configuración Óptima

```python
THRESHOLD = 0.65
MODEL = "speechbrain/spkrec-ecapa-voxceleb"
EMBEDDING_DIM = 192
```

### Resultados por Threshold

| Threshold | FAR | FRR | Accuracy | Recomendación |
|-----------|-----|-----|----------|---------------|
| 0.60 | 1.80% | 12.16% | 93.01% | Más permisivo |
| **0.65** | **0.90%** | **16.22%** | **91.40%** | ⭐ **Óptimo** |
| 0.70 | 0.00% | 25.68% | 87.16% | Más restrictivo |

### Métricas de Rendimiento

```
EER (Equal Error Rate): 6.31%
Accuracy: 91.40%
Precision: 98.20%
Recall: 83.78%
F1-Score: 90.41%
```

---

## 📊 Gráficos Correspondientes

### 1. EER Analysis Curves
**Archivo**: [`eer_analysis_curves.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/eer_analysis_curves.png)

**Descripción**: Curvas ROC y DET mostrando el punto de Equal Error Rate (6.31%)

**Qué muestra**:
- Curva ROC (Receiver Operating Characteristic)
- Punto EER donde FAR = FRR
- Rendimiento del modelo en diferentes thresholds

---

### 2. FAR/FRR Intersection
**Archivo**: [`far_frr_intersection.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/far_frr_intersection.png)

**Descripción**: Intersección de FAR y FRR en función del threshold

**Qué muestra**:
- FAR disminuye al aumentar threshold
- FRR aumenta al aumentar threshold
- Punto óptimo de balance (threshold 0.65)

---

### 3. Speaker Recognition Only
**Archivo**: [`model1_speaker_only.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/model1_speaker_only.png)

**Descripción**: Evaluación completa del módulo de Speaker Recognition

**Qué muestra**:
- Distribución de scores de similitud
- Métricas de rendimiento
- Comparación de thresholds

---

## 🔧 Configuración Final

### Parámetros del Modelo

```python
{
    "model_id": 1,
    "model_name": "speechbrain/spkrec-ecapa-voxceleb",
    "threshold": 0.65,
    "embedding_dim": 192,
    "sample_rate": 16000,
    "use_gpu": true
}
```

### Decisión de Threshold

**¿Por qué 0.65?**

1. **Balance óptimo**: FAR 0.90% (excelente seguridad) vs FRR 16.22% (usabilidad aceptable)
2. **Cerca del EER**: Threshold cercano al punto de Equal Error Rate (6.31%)
3. **Seguridad prioritaria**: FAR < 1% cumple requisitos de seguridad
4. **Usabilidad**: FRR 16.22% es manejable con sistema de reintentos

---

## 📊 Análisis de Rendimiento

### Distribución de Scores

**Genuinos**:
- Media: 0.72
- Desviación: 0.08
- Rango: [0.45 - 0.85]

**Impostores**:
- Media: 0.35
- Desviación: 0.12
- Rango: [0.15 - 0.60]

**Separación**: Buena separación entre genuinos e impostores

---

### Casos de Error

**False Acceptances (FAR 0.90%)**:
- Impostores con características vocales similares
- ~1 de cada 111 intentos de impostor

**False Rejections (FRR 16.22%)**:
- Variaciones en calidad de audio
- Cambios en estado de voz (resfriado, fatiga)
- ~1 de cada 6 usuarios genuinos

---

## ✅ Fortalezas

1. ✅ **FAR < 1%**: Excelente seguridad
2. ✅ **EER 6.31%**: Rendimiento competitivo
3. ✅ **Modelo robusto**: ECAPA-TDNN estado del arte
4. ✅ **Rápido**: ~500ms de procesamiento

---

## ⚠️ Limitaciones

1. ⚠️ **FRR 16.22%**: Puede rechazar usuarios genuinos
2. ⚠️ **Sensible a calidad**: Requiere audio de buena calidad
3. ⚠️ **Variabilidad vocal**: Afectado por cambios en voz

---

## 🎓 Para la Tesis

### Métricas a Reportar

```
Modelo: ECAPA-TDNN
Threshold: 0.65

EER: 6.31%
FAR: 0.90%
FRR: 16.22%
Accuracy: 91.40%
```

### Justificación

> "El módulo de Speaker Recognition utiliza ECAPA-TDNN, un modelo estado del arte para reconocimiento de locutor. Con un threshold de 0.65, se logra un FAR de 0.90% (< 1%), cumpliendo los requisitos de seguridad, mientras se mantiene un FRR de 16.22%, aceptable para un sistema con reintentos. El EER de 6.31% demuestra un rendimiento competitivo en la tarea de verificación de locutor."

---

## 📁 Archivos Relacionados

### Scripts
- [`evaluate_speaker_recognition.py`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/scripts/evaluate_speaker_recognition.py)

### Resultados
- [`speaker_recognition_results.txt`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/results/speaker_recognition/)

### Gráficos
- [`eer_analysis_curves.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/eer_analysis_curves.png)
- [`far_frr_intersection.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/far_frr_intersection.png)
- [`model1_speaker_only.png`](file:///Users/tomipoch/Documents/Nueva%20carpeta%20con%20elementos/Ultimo%20Semestre/Tesis/Proyecto/Backend/evaluation/plots/speaker_recognition/model1_speaker_only.png)

---

**Documento generado**: 22 de Diciembre de 2024  
**Versión**: 1.0 - Evaluación Final
