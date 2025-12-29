# Guía: Captura de Ataques Spoof para Evaluación del Sistema

## 🎯 Objetivo

Crear un dataset de ataques reales para evaluar el sistema completo de autenticación por voz, incluyendo:
1. **Ataques de Replay** (reproducción desde celular/parlante)
2. **Ataques TTS** (text-to-speech sintético)
3. **Intentos de impostor** (otra persona)

---

## 📋 Tipos de Ataques a Implementar

### 1. Ataque de Replay (PRIORIDAD ALTA) ⭐

**Descripción**: Reproducir grabaciones genuinas desde un dispositivo.

**Cómo hacerlo**:
1. Toma los audios genuinos existentes (enrollment o verification)
2. Reprodúcelos desde un celular/laptop
3. Graba con el micrófono del sistema

**Variantes**:
- **Replay directo**: Reproducir desde celular cerca del micrófono
- **Replay con parlante**: Reproducir desde parlantes externos
- **Replay de baja calidad**: Reproducir desde celular con volumen bajo

**Ejemplo práctico**:
```bash
# 1. Reproducir audio en celular
# 2. Abrir app de grabación en computadora
# 3. Grabar mientras reproduce
# 4. Guardar como: userA_replay_attempt1.wav
```

### 2. Ataque TTS (Text-to-Speech)

**Descripción**: Usar voz sintética para generar la frase.

**Herramientas gratuitas**:
- Google TTS (online)
- Amazon Polly (free tier)
- ElevenLabs (free tier)
- gTTS (Python library)

**Cómo hacerlo**:
```python
from gtts import gTTS
import os

# Generar audio sintético
text = "banking security is very important"
tts = gTTS(text=text, lang='es')  # o 'en' para inglés
tts.save("userA_tts_attempt1.mp3")

# Convertir a WAV si es necesario
os.system("ffmpeg -i userA_tts_attempt1.mp3 userA_tts_attempt1.wav")
```

### 3. Ataque de Impostor (otra persona)

**Descripción**: Otra persona intenta imitar o usar su propia voz.

**Cómo hacerlo**:
1. Pide a un amigo/familiar que grabe las frases
2. Intenta que imite la voz del usuario objetivo (opcional)
3. Guarda como: userB_as_userA_attempt1.wav

---

## 🗂️ Estructura del Dataset de Ataques

```
evaluation/dataset/spoof_attacks/
├── replay_attacks/
│   ├── userA_replay_celular_1.wav
│   ├── userA_replay_celular_2.wav
│   ├── userA_replay_parlante_1.wav
│   └── metadata.json
├── tts_attacks/
│   ├── userA_tts_google_1.wav
│   ├── userA_tts_elevenlabs_1.wav
│   └── metadata.json
├── impostor_attacks/
│   ├── userB_as_userA_1.wav
│   ├── userC_as_userA_1.wav
│   └── metadata.json
└── README.md
```

### Metadata.json (ejemplo)

```json
{
  "attacks": [
    {
      "filename": "userA_replay_celular_1.wav",
      "attack_type": "replay",
      "target_user": "piapobletech",
      "source_audio": "piapobletech_verification_1.wav",
      "device": "iPhone 13",
      "distance_cm": 30,
      "phrase": "banking security is very important",
      "date": "2024-12-20"
    },
    {
      "filename": "userA_tts_google_1.wav",
      "attack_type": "tts",
      "target_user": "piapobletech",
      "tts_engine": "Google TTS",
      "phrase": "banking security is very important",
      "date": "2024-12-20"
    }
  ]
}
```

---

## 🎙️ Procedimiento de Captura de Replay Attacks

### Opción 1: Usando la App Web (RECOMENDADO)

**Pasos**:
1. **Preparación**:
   - Abre un audio genuino en tu celular
   - Abre la app web en tu computadora
   - Inicia sesión como el usuario objetivo

2. **Captura**:
   - Inicia grabación en la app
   - Reproduce el audio desde el celular cerca del micrófono
   - Detén la grabación
   - Descarga el audio

3. **Organización**:
   - Renombra: `{usuario}_replay_{dispositivo}_{numero}.wav`
   - Mueve a: `evaluation/dataset/spoof_attacks/replay_attacks/`

### Opción 2: Usando Script Python

```python
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

def record_replay_attack(duration=5, target_user="userA", device="celular"):
    """
    Graba un ataque de replay.
    
    Args:
        duration: Duración en segundos
        target_user: Usuario objetivo
        device: Dispositivo usado para replay
    """
    print(f"🎙️  Grabando ataque de replay...")
    print(f"   Reproduce el audio AHORA desde tu {device}")
    print(f"   Grabando por {duration} segundos...")
    
    # Grabar
    fs = 16000  # Sample rate
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    
    # Guardar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{target_user}_replay_{device}_{timestamp}.wav"
    sf.write(filename, recording, fs)
    
    print(f"✅ Guardado: {filename}")
    return filename

# Uso
record_replay_attack(duration=5, target_user="piapobletech", device="iphone")
```

### Opción 3: Usando Audacity (Manual)

1. Abre Audacity
2. Configura entrada de micrófono
3. Click en "Grabar"
4. Reproduce audio desde celular
5. Click en "Detener"
6. Exportar como WAV

---

## 📊 Plan de Captura Mínimo

Para una evaluación básica pero válida:

### Por Usuario (4 usuarios)

| Tipo de Ataque | Cantidad | Total |
|----------------|----------|-------|
| Replay (celular) | 3 | 12 |
| Replay (parlante) | 2 | 8 |
| TTS (Google) | 2 | 8 |
| Impostor | 2 | 8 |
| **Total** | **9** | **36 ataques** |

**Tiempo estimado**: 2-3 horas

---

## 🧪 Script de Evaluación del Sistema Completo

Una vez tengas los ataques, usa este script:

```python
#!/usr/bin/env python3
"""
Evalúa el sistema completo con ataques reales.
"""

import sys
from pathlib import Path
import json
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade
from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_system_with_real_attacks(
    genuine_dir: Path,
    replay_dir: Path,
    tts_dir: Path,
    impostor_dir: Path,
    threshold_speaker: float = 0.65,
    threshold_antispoof: float = 0.5,
    threshold_text: float = 0.7
):
    """
    Evalúa el sistema completo con ataques reales.
    """
    
    voice_engine = VoiceBiometricEngineFacade()
    
    # Cargar voiceprints
    voiceprints = {}
    for user_dir in genuine_dir.iterdir():
        if not user_dir.is_dir():
            continue
        username = user_dir.name
        enrollment_audios = list(user_dir.glob(f"{username}_enrollment_*.wav"))
        
        # Crear voiceprint
        embeddings = []
        for audio_path in enrollment_audios:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            embedding = voice_engine.extract_embedding_only(audio_data, 'wav')
            embeddings.append(embedding)
        
        voiceprints[username] = np.mean(embeddings, axis=0)
    
    # Evaluar genuinos
    genuine_results = evaluate_genuine_attempts(
        genuine_dir, voiceprints, voice_engine,
        threshold_speaker, threshold_antispoof, threshold_text
    )
    
    # Evaluar ataques de replay
    replay_results = evaluate_attacks(
        replay_dir, voiceprints, voice_engine, "replay",
        threshold_speaker, threshold_antispoof, threshold_text
    )
    
    # Evaluar ataques TTS
    tts_results = evaluate_attacks(
        tts_dir, voiceprints, voice_engine, "tts",
        threshold_speaker, threshold_antispoof, threshold_text
    )
    
    # Evaluar impostores
    impostor_results = evaluate_attacks(
        impostor_dir, voiceprints, voice_engine, "impostor",
        threshold_speaker, threshold_antispoof, threshold_text
    )
    
    # Calcular métricas del sistema
    total_genuine = genuine_results["total"]
    genuine_accepted = genuine_results["accepted"]
    
    total_attacks = (
        replay_results["total"] +
        tts_results["total"] +
        impostor_results["total"]
    )
    
    attacks_accepted = (
        replay_results["accepted"] +
        tts_results["accepted"] +
        impostor_results["accepted"]
    )
    
    FRR_sistema = (total_genuine - genuine_accepted) / total_genuine * 100
    FAR_sistema = attacks_accepted / total_attacks * 100
    
    # Reporte
    report = {
        "system_metrics": {
            "FAR": FAR_sistema,
            "FRR": FRR_sistema,
            "thresholds": {
                "speaker": threshold_speaker,
                "antispoof": threshold_antispoof,
                "text": threshold_text
            }
        },
        "genuine": genuine_results,
        "attacks": {
            "replay": replay_results,
            "tts": tts_results,
            "impostor": impostor_results,
            "total": {
                "total": total_attacks,
                "accepted": attacks_accepted,
                "rate": FAR_sistema
            }
        }
    }
    
    return report


def evaluate_genuine_attempts(genuine_dir, voiceprints, voice_engine, 
                              threshold_speaker, threshold_antispoof, threshold_text):
    """Evalúa intentos genuinos."""
    
    total = 0
    accepted = 0
    rejected_by = {"speaker": 0, "antispoof": 0, "text": 0}
    
    for user_dir in genuine_dir.iterdir():
        if not user_dir.is_dir():
            continue
        
        username = user_dir.name
        voiceprint = voiceprints.get(username)
        if voiceprint is None:
            continue
        
        verification_audios = list(user_dir.glob(f"{username}_verification_*.wav"))
        
        for audio_path in verification_audios:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Extraer features completas
            features = voice_engine.extract_features(audio_data, 'wav')
            
            # Calcular similarity
            similarity = float(np.dot(features["embedding"], voiceprint) / 
                             (np.linalg.norm(features["embedding"]) * np.linalg.norm(voiceprint)))
            
            # Decisión del sistema (cascada)
            speaker_pass = similarity >= threshold_speaker
            antispoof_pass = features["anti_spoofing_score"] < threshold_antispoof
            # text_pass = True  # Asumimos texto correcto para genuinos
            
            total += 1
            
            if speaker_pass and antispoof_pass:
                accepted += 1
            else:
                if not speaker_pass:
                    rejected_by["speaker"] += 1
                if not antispoof_pass:
                    rejected_by["antispoof"] += 1
    
    return {
        "total": total,
        "accepted": accepted,
        "rejected": total - accepted,
        "rejected_by": rejected_by,
        "rate": (total - accepted) / total * 100 if total > 0 else 0
    }


def evaluate_attacks(attack_dir, voiceprints, voice_engine, attack_type,
                    threshold_speaker, threshold_antispoof, threshold_text):
    """Evalúa ataques de un tipo específico."""
    
    total = 0
    accepted = 0
    blocked_by = {"speaker": 0, "antispoof": 0, "text": 0}
    
    for audio_path in attack_dir.glob("*.wav"):
        # Extraer usuario objetivo del nombre del archivo
        # Formato: userA_replay_celular_1.wav
        parts = audio_path.stem.split('_')
        target_user = parts[0]
        
        voiceprint = voiceprints.get(target_user)
        if voiceprint is None:
            continue
        
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Extraer features
        features = voice_engine.extract_features(audio_data, 'wav')
        
        # Calcular similarity
        similarity = float(np.dot(features["embedding"], voiceprint) / 
                         (np.linalg.norm(features["embedding"]) * np.linalg.norm(voiceprint)))
        
        # Decisión del sistema
        speaker_pass = similarity >= threshold_speaker
        antispoof_pass = features["anti_spoofing_score"] < threshold_antispoof
        
        total += 1
        
        if speaker_pass and antispoof_pass:
            accepted += 1
        else:
            if not speaker_pass:
                blocked_by["speaker"] += 1
            if not antispoof_pass:
                blocked_by["antispoof"] += 1
    
    return {
        "type": attack_type,
        "total": total,
        "accepted": accepted,
        "blocked": total - accepted,
        "blocked_by": blocked_by,
        "rate": accepted / total * 100 if total > 0 else 0
    }


def main():
    """Ejecuta evaluación completa."""
    
    base_dir = Path(__file__).parent / "dataset"
    
    genuine_dir = base_dir / "recordings" / "auto_recordings_20251218"
    replay_dir = base_dir / "spoof_attacks" / "replay_attacks"
    tts_dir = base_dir / "spoof_attacks" / "tts_attacks"
    impostor_dir = base_dir / "spoof_attacks" / "impostor_attacks"
    
    # Verificar que existen los directorios
    if not replay_dir.exists():
        logger.error(f"Directorio de ataques replay no existe: {replay_dir}")
        logger.info("Crea los ataques primero siguiendo la guía.")
        return
    
    # Evaluar sistema
    report = evaluate_system_with_real_attacks(
        genuine_dir, replay_dir, tts_dir, impostor_dir,
        threshold_speaker=0.65,
        threshold_antispoof=0.5,
        threshold_text=0.7
    )
    
    # Guardar reporte
    output_file = Path(__file__).parent / "system_evaluation_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Imprimir resumen
    print("\n" + "="*60)
    print("EVALUACIÓN DEL SISTEMA COMPLETO")
    print("="*60)
    print(f"\nFAR del Sistema: {report['system_metrics']['FAR']:.2f}%")
    print(f"FRR del Sistema: {report['system_metrics']['FRR']:.2f}%")
    print(f"\nDesglose de Ataques:")
    print(f"  - Replay: {report['attacks']['replay']['rate']:.2f}% aceptados")
    print(f"  - TTS: {report['attacks']['tts']['rate']:.2f}% aceptados")
    print(f"  - Impostor: {report['attacks']['impostor']['rate']:.2f}% aceptados")
    print(f"\nReporte completo guardado en: {output_file}")


if __name__ == "__main__":
    main()
```

---

## ✅ Checklist de Implementación

### Fase 1: Captura de Ataques (2-3 horas)
- [ ] Crear directorios para ataques
- [ ] Capturar 12 ataques de replay (celular)
- [ ] Capturar 8 ataques de replay (parlante)
- [ ] Generar 8 ataques TTS
- [ ] Grabar 8 intentos de impostor
- [ ] Crear metadata.json para cada tipo

### Fase 2: Evaluación (30 min)
- [ ] Ejecutar script de evaluación
- [ ] Revisar resultados
- [ ] Generar gráficas

### Fase 3: Análisis (1 hora)
- [ ] Calcular FAR/FRR del sistema
- [ ] Identificar qué módulo bloquea cada ataque
- [ ] Documentar hallazgos

---

## 🎯 Resultado Esperado

Al final tendrás:

**Tabla de Resultados del Sistema**:

| Métrica | Valor |
|---------|-------|
| FAR Sistema (todos los ataques) | X% |
| FRR Sistema | Y% |
| FAR Replay | X1% |
| FAR TTS | X2% |
| FAR Impostor | X3% |

**Análisis por Módulo**:
- ¿Qué módulo bloquea más ataques?
- ¿Dónde está el cuello de botella?
- ¿El anti-spoofing funciona contra replay?

---

**¿Quieres que te ayude a crear los scripts de captura o prefieres empezar con la captura manual?**

