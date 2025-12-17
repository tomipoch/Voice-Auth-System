# Guía de Evaluación - Framework de Evaluación de Biometría de Voz

## Descripción General

Este framework proporciona herramientas para evaluar el sistema de autenticación biométrica por voz utilizando métricas estándar de la industria (FAR, FRR, EER) siguiendo las normas ISO/IEC 19795.

## Estructura del Proyecto

```
Backend/evaluation/
├── metrics_calculator.py          # Cálculo de métricas biométricas
├── results_manager.py              # Gestión de resultados y export
├── evaluation_logger.py            # Logging automático para frontend
├── scripts/
│   ├── evaluate_speaker_verification.py   # Evaluación de verificación de locutor
│   ├── evaluate_antispoofing.py           # Evaluación de anti-spoofing
│   ├── evaluate_asr.py                    # Evaluación de ASR
│   ├── annotate_results.py                # Anotación manual de resultados
│   └── plot_results.py                    # Visualizaciones
├── dataset/                        # Datasets de evaluación  
└── results/                        # Resultados de experimentos
```

---

## 1. Evaluación Automatizada (Con Datasets)

### 1.1 Preparar Dataset

Organizar audios en la siguiente estructura:

```
Backend/evaluation/dataset/
├── voxceleb/
│   ├── user_001/
│   │   ├── enrollment_01.wav
│   │   ├── enrollment_02.wav
│   │   ├── test_genuine_01.wav
│   │   └── test_genuine_02.wav
│   └── user_002/
│       └── ...
└── asvspoof/
    ├── bonafide/
    │   └── genuine_001.wav
    └── spoof/
        └── spoofed_001.wav
```

### 1.2 Crear Archivo de Configuración

**Ejemplo: `dataset/voxceleb_config.json`**

```json
{
  "enrollment": {
    "user_001": ["voxceleb/user_001/enrollment_01.wav", "voxceleb/user_001/enrollment_02.wav"],
    "user_002": ["voxceleb/user_002/enrollment_01.wav", "voxceleb/user_002/enrollment_02.wav"]
  },
  "genuine": {
    "user_001": ["voxceleb/user_001/test_genuine_01.wav"],
    "user_002": ["voxceleb/user_002/test_genuine_01.wav"]
  },
  "impostor": {
    "user_001": {
      "user_002": ["voxceleb/user_002/test_genuine_01.wav"]
    }
  }
}
```

### 1.3 Ejecutar Evaluación

**Speaker Verification:**
```bash
python evaluation/scripts/evaluate_speaker_verification.py \
    --dataset evaluation/dataset \
    --config evaluation/dataset/voxceleb_config.json \
    --name voxceleb_10users
```

**Anti-Spoofing:**
```bash
# Evaluar modelo específico
python evaluation/scripts/evaluate_antispoofing.py \
    --dataset evaluation/dataset \
    --config evaluation/dataset/asvspoof_config.json \
    --model aasist_antispoofing \
    --name asvspoof_aasist

# Evaluar ensemble
python evaluation/scripts/evaluate_antispoofing.py \
    --dataset evaluation/dataset \
    --config evaluation/dataset/asvspoof_config.json \
    --model ensemble_antispoofing \
    --name asvspoof_ensemble
```

**ASR:**
```bash
python evaluation/scripts/evaluate_asr.py \
    --dataset evaluation/dataset \
    --config evaluation/dataset/asr_config.json \
    --name asr_phrases
```

---

## 2. Evaluación Manual (Con Frontend)

### 2.1 Iniciar Sesión de Evaluación

**Opción A: Via API**
```bash
curl -X POST http://localhost:8000/api/evaluation/start-session \
    -H "Content-Type: application/json" \
    -d '{"session_name": "manual_eval_20251217"}'
```

**Opción B: Vía código Python**
```python
from evaluation.evaluation_logger import evaluation_logger

session_id = evaluation_logger.start_session("manual_eval")
print(f"Session started: {session_id}")
```

### 2.2 Realizar Pruebas en el Frontend

1. Login con usuario existente (ej: `user@empresa.com`)
2. Realizar enrollment (si no tiene voiceprint)
3. Realizar verificaciones:
   - **Genuinas**: El usuario real verificándose
   - **Impostoras**: Otro usuario intentando verificarse como el primero

**Todo se loggea automáticamente** mientras la sesión está activa.

### 2.3 Detener Sesión y Exportar Datos

```bash
# Detener sesión
curl -X POST "http://localhost:8000/api/evaluation/stop-session"

# Exportar datos
curl -X GET "http://localhost:8000/api/evaluation/export-session/manual_eval_20251217_020000"
```

### 2.4 Anotar Resultados

Marcar manualmente cada intento como genuino o impostor:

```bash
python evaluation/scripts/annotate_results.py \
    --session manual_eval_20251217_020000
```

El script te preguntará por cada intento:
```
Was this GENUINE or IMPOSTOR? [g/i/s/q]:
```

Al finalizar, calcula automáticamente FAR y FRR.

---

## 3. Visualizar Resultados

### 3.1 Instalar Dependencias

```bash
pip install matplotlib numpy
```

### 3.2 Generar Gráficas

```python
from evaluation.scripts.plot_results import ResultsVisualizer
import numpy as np

visualizer = ResultsVisualizer()

# Cargar datos
genuine_scores = np.array([...])  # De tus resultados
impostor_scores = np.array([...])

# Generar gráficas
visualizer.plot_score_distributions(genuine_scores, impostor_scores)
visualizer.plot_roc_curve(far_values, tpr_values)
```

---

## 4. Métricas Importantes

### Verificación de Locutor

- **FAR (False Acceptance Rate)**: % de impostores aceptados
- **FRR (False Rejection Rate)**: % de genuinos rechazados
- **EER (Equal Error Rate)**: Punto donde FAR = FRR (menor es mejor)
- **Threshold**: Umbral de decisión usado

### Anti-Spoofing

- **FAR_spoof**: % de ataques aceptados como genuinos
- **FRR_spoof**: % de genuinos rechazados como ataques
- **EER_spoof**: EER específico para anti-spoofing

### ASR

- **WER (Word Error Rate)**: % de palabras incorrectas en transcripción
- **Phrase Match Accuracy**: % de veces que detecta correctamente frase correcta/incorrecta

---

## 5. Estructura de Resultados

Los resultados se guardan en JSON:

```json
{
  "metadata": {
    "experiment_id": "speaker_verification_voxceleb_20251217_020000",
    "experiment_type": "speaker_verification",
    "timestamp": "20251217_020000",
    "dataset": "voxceleb_10users"
  },
  "test_results": [
    {
      "test_id": "genuine_0001",
      "test_type": "genuine",
      "user_id": "user_001",
      "similarity_score": 0.85,
      "label": "genuine"
    }
  ],
  "metrics": {
    "eer": 0.04,
    "far": 0.04,
    "frr": 0.04,
    "eer_threshold": 0.65
  }
}
```

---

## 6. Comandos Útiles

```bash
# Listar sesiones activas
curl http://localhost:8000/api/evaluation/sessions

# Ver estado del sistema de evaluación
curl http://localhost:8000/api/evaluation/status

# Ver resumen de sesión
curl http://localhost:8000/api/evaluation/session-summary/<session_id>
```

---

## 7. Tips para Tesis

1. **Datasets Públicos**: Usa VoxCeleb y ASVspoof para comparación con literatura
2. **Múltiples Umbrales**: Genera curvas ROC variando umbrales
3. **Comparación de Modelos**: Evalúa cada modelo del ensemble por separado
4. **Manual + Automatizado**: Combina ambos enfoques para resultados completos
5. **Documentar Todo**: El framework guarda metadata automáticamente

---

## 8. Troubleshooting

**Problema: "No module named 'matplotlib'"**
```bash
pip install matplotlib
```

**Problema: "Session not found"**
- Verificar que la sesión esté activa con `/api/evaluation/sessions`
- El session_id incluye timestamp, copiar exactamente

**Problema: "Not enough data for metrics"**
- Necesitas al menos 10 genuinos y 10 impostores para métricas confiables

---

## 9. Próximos Pasos para Completar

1. **Hooks Automáticos** (Opcional): Integrar logging en services
2. **Datasets**: Preparar mini-datasets de prueba
3. **Experimentar**: Ejecutar evaluaciones y documentar resultados
4. **Visualizar**: Generar gráficas para informe de tesis

---

## Contacto y Soporte

Para preguntas sobre el framework, consultar el archivo `implementation_plan.md` para detalles técnicos adicionales.
