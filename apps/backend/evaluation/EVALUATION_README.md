# Sistema de Evaluación del Sistema Biométrico de Voz

Este directorio contiene **4 scripts** enfocados para evaluar el sistema completo de autenticación biométrica por voz.

## 📋 Índice de Scripts

1. **`evaluate_speaker_recognition.py`** - Módulo de Reconocimiento de Locutor
2. **`evaluate_text_verification.py`** - Módulo de Verificación de Texto (ASR)
3. **`evaluate_antispoofing.py`** - Módulo de Anti-Spoofing
4. **`evaluate_complete_system.py`** - Sistema Completo (Métricas de Integración)

---

## 🎯 1. Evaluación del Reconocimiento de Locutor

**Script:** `evaluate_speaker_recognition.py`

### Métricas Calculadas

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **FRR** (False Rejection Rate) | % de usuarios genuinos rechazados | ✅ Menor es mejor (~0% óptimo) |
| **FAR** (False Acceptance Rate) | % de impostores aceptados | ✅ Menor es mejor (~0% óptimo) |
| **EER** (Equal Error Rate) | Punto donde FAR = FRR | ✅ Menor es mejor (~0% óptimo) |

### Estructura del Dataset

```
evaluation/dataset/speaker_recognition/
  ├── enrollment/
  │   ├── user1/
  │   │   ├── sample1.wav
  │   │   ├── sample2.wav
  │   │   └── sample3.wav
  │   └── user2/
  │       └── ...
  ├── genuine/
  │   ├── user1/
  │   │   ├── test1.wav
  │   │   └── test2.wav
  │   └── user2/
  │       └── ...
  └── impostor/
      ├── user1_vs_user2.wav
      ├── user1_vs_user3.wav
      └── ...
```

### Uso

```bash
cd apps/backend
python evaluation/evaluate_speaker_recognition.py
```

### Salida

- Reporte: `evaluation/results/speaker_recognition_evaluation.txt`
- Métricas JSON: `evaluation/results/speaker_recognition_evaluation.json`

---

## 📝 2. Evaluación de Verificación de Texto

**Script:** `evaluate_text_verification.py`

### Métricas Calculadas

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **WER** (Word Error Rate) | % de errores en palabras | ✅ Menor es mejor (~0% óptimo) |
| **Transcription Accuracy** | % de transcripciones correctas | ✅ Mayor es mejor (~100% óptimo) |
| **Phrase Matching Accuracy** | % de frases correctamente identificadas | ✅ Mayor es mejor (~100% óptimo) |

### Estructura del Dataset

```
evaluation/dataset/text_verification/
  ├── transcription_tests.json
  ├── phrase_matching_tests.json
  ├── audio1.wav
  ├── audio2.wav
  └── ...
```

**Formato `transcription_tests.json`:**
```json
[
  {
    "audio": "audio1.wav",
    "text": "el texto esperado de la transcripción"
  },
  {
    "audio": "audio2.wav",
    "text": "otra frase de ejemplo"
  }
]
```

**Formato `phrase_matching_tests.json`:**
```json
[
  {
    "audio": "audio1.wav",
    "expected_phrase": "la frase correcta",
    "test_phrases": [
      "la frase correcta",
      "otra frase diferente",
      "frase incorrecta"
    ]
  }
]
```

### Uso

```bash
cd apps/backend
python evaluation/evaluate_text_verification.py
```

### Salida

- Reporte: `evaluation/results/text_verification_evaluation.txt`
- Métricas JSON: `evaluation/results/text_verification_evaluation.json`

---

## 🛡️ 3. Evaluación de Anti-Spoofing

**Script:** `evaluate_antispoofing.py`

### Métricas Calculadas (ISO/IEC 30107-3)

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **APCER** (Attack Presentation Classification Error Rate) | % de ataques aceptados | ✅ Menor es mejor (~0% óptimo) |
| **BPCER** (Bona Fide Presentation Classification Error Rate) | % de genuinos rechazados | ✅ Menor es mejor (~0% óptimo) |
| **ACER** (Average Classification Error Rate) | Promedio de APCER y BPCER | ✅ Menor es mejor (~0% óptimo) |

### Estructura del Dataset

```
evaluation/dataset/antispoofing/
  ├── genuine/
  │   ├── genuine1.wav
  │   ├── genuine2.wav
  │   └── ...
  ├── tts/
  │   ├── tts_attack1.wav
  │   ├── tts_attack2.wav
  │   └── ...
  └── cloning/
      ├── clone_attack1.wav
      ├── clone_attack2.wav
      └── ...
```

### Uso

```bash
cd apps/backend
python evaluation/evaluate_antispoofing.py
```

### Salida

- Reporte: `evaluation/results/antispoofing_evaluation.txt`
- Métricas JSON: `evaluation/results/antispoofing_evaluation.json`
- Métricas separadas por tipo de ataque (TTS, Cloning)

---

## 🔧 4. Evaluación del Sistema Completo

**Script:** `evaluate_complete_system.py`

### Métricas Calculadas

#### Eficiencia

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **RTF** (Real-Time Factor) | Tiempo de procesamiento / Duración del audio | ✅ Menor es mejor (~0 óptimo, <1 es tiempo real) |
| **TTP** (Total Processing Time) | Tiempo total de procesamiento en segundos | ✅ ~2 segundos es BUENO |

#### Robustez

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **SNR vs Error** | Error de verificación según nivel de SNR | Menor error con SNR bajo es mejor |
| **Sensibilidad a Duración** | EER según duración del audio | EER bajo incluso con audio corto es mejor |

#### Calibración

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **t-DCF** (tandem Detection Cost Function) | Costo de detección combinado | ✅ Menor es mejor (~0% óptimo) |

### Estructura del Dataset

```
evaluation/dataset/complete_system/
  ├── efficiency_test/
  │   ├── audio1.wav
  │   ├── audio2.wav
  │   └── ...
  ├── snr_robustness/
  │   ├── genuine/
  │   │   ├── high_snr_audio.wav
  │   │   ├── medium_snr_audio.wav
  │   │   └── low_snr_audio.wav
  │   └── ...
  ├── duration_sensitivity/
  │   ├── genuine/
  │   │   ├── short_audio.wav
  │   │   ├── medium_audio.wav
  │   │   └── long_audio.wav
  │   └── spoof/
  │       └── ...
  └── antispoofing/
      ├── genuine/
      │   └── ...
      └── spoof/
          └── ...
```

### Uso

```bash
cd apps/backend
python evaluation/evaluate_complete_system.py
```

### Salida

- Reporte: `evaluation/results/complete_system_evaluation.txt`
- Métricas JSON: `evaluation/results/complete_system_evaluation.json`

---

## 📊 Resumen de Todas las Métricas

### Por Módulo

| Módulo | Métricas | Objetivo |
|--------|----------|----------|
| **Speaker Recognition** | FRR, FAR, EER | Todos cercanos a 0% |
| **Text Verification** | WER (~0%), Phrase Matching (~100%), Transcription (~100%) | WER bajo, Accuracy alto |
| **Anti-Spoofing** | APCER, BPCER, ACER | Todos cercanos a 0% |
| **Sistema Completo** | RTF (~0), TTP (~2s), SNR vs Error, Duración vs EER, t-DCF (~0) | Eficiente y robusto |

### Interpretación de Resultados

#### ✅ EXCELENTE
- FRR < 5%, FAR < 1%, EER < 5%
- WER < 5%, Transcription > 95%, Phrase Matching > 95%
- APCER < 5%, BPCER < 5%, ACER < 5%
- RTF < 0.5, TTP 1.5-3.0s, t-DCF < 0.05

#### ✓ BUENO
- FRR < 10%, FAR < 5%, EER < 10%
- WER < 15%, Transcription > 85%, Phrase Matching > 85%
- APCER < 15%, BPCER < 15%, ACER < 15%
- RTF < 1.0, TTP < 5s, t-DCF < 0.10

#### ⚠️ REQUIERE MEJORA
- FRR > 10%, FAR > 5%, EER > 10%
- WER > 15%, Transcription < 85%, Phrase Matching < 85%
- APCER > 15%, BPCER > 15%, ACER > 15%
- RTF > 1.0, TTP > 5s, t-DCF > 0.10

---

## 🚀 Ejecución Completa

Para ejecutar todos los scripts en secuencia:

```bash
cd apps/backend

# 1. Speaker Recognition
python evaluation/evaluate_speaker_recognition.py

# 2. Text Verification
python evaluation/evaluate_text_verification.py

# 3. Anti-Spoofing
python evaluation/evaluate_antispoofing.py

# 4. Sistema Completo
python evaluation/evaluate_complete_system.py
```

---

## 📁 Resultados

Todos los resultados se guardan en:

```
evaluation/results/
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

## 🔧 Requisitos

- Python 3.8+
- Dependencias instaladas: `pip install -r requirements.txt`
- GPU recomendada para mejor rendimiento
- Datasets preparados en las rutas especificadas

---

## 📝 Notas

- Los scripts son independientes y pueden ejecutarse en cualquier orden
- Los archivos `.txt` contienen reportes legibles para humanos
- Los archivos `.json` contienen métricas estructuradas para procesamiento automático
- Todos los scripts incluyen logging detallado del progreso
- Los datasets de ejemplo deben ser proporcionados según las estructuras especificadas

---

## 📚 Referencias

- **ISO/IEC 19795**: Estándares para evaluación de rendimiento biométrico
- **ISO/IEC 30107-3**: Estándares para métricas de anti-spoofing
- **ASVspoof Challenge**: Metodologías de evaluación de anti-spoofing
