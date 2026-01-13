# Ejemplos de Configuración de Datasets

Este archivo muestra ejemplos de cómo estructurar los archivos JSON necesarios para la evaluación.

---

## 📝 Text Verification - transcription_tests.json

Ubicación: `dataset/text_verification/transcription_tests.json`

```json
[
  {
    "audio": "audio001.wav",
    "text": "el perro juega en el jardín con la pelota"
  },
  {
    "audio": "audio002.wav",
    "text": "buenos días señor garcía cómo está usted"
  },
  {
    "audio": "audio003.wav",
    "text": "necesito verificar mi identidad para acceder a mi cuenta"
  },
  {
    "audio": "audio004.wav",
    "text": "la casa grande tiene tres pisos y un ático"
  },
  {
    "audio": "audio005.wav",
    "text": "me gustaría hacer una transferencia bancaria por favor"
  }
]
```

---

## 📝 Text Verification - phrase_matching_tests.json

Ubicación: `dataset/text_verification/phrase_matching_tests.json`

```json
[
  {
    "audio": "phrase_test_001.wav",
    "expected_phrase": "el gato negro duerme en el tejado",
    "test_phrases": [
      "el gato negro duerme en el tejado",
      "el perro blanco corre por el jardín",
      "la luna brilla en la noche oscura"
    ]
  },
  {
    "audio": "phrase_test_002.wav",
    "expected_phrase": "quiero realizar una operación bancaria",
    "test_phrases": [
      "quiero realizar una operación bancaria",
      "necesito consultar mi saldo disponible",
      "deseo cambiar mi contraseña de acceso"
    ]
  },
  {
    "audio": "phrase_test_003.wav",
    "expected_phrase": "la seguridad es muy importante",
    "test_phrases": [
      "la seguridad es muy importante",
      "el sistema funciona correctamente",
      "la tecnología avanza rápidamente"
    ]
  }
]
```

---

## 📂 Estructura Completa de Ejemplo

### Speaker Recognition

```
dataset/speaker_recognition/
├── enrollment/
│   ├── user_001/
│   │   ├── enrollment_sample_1.wav
│   │   ├── enrollment_sample_2.wav
│   │   ├── enrollment_sample_3.wav
│   │   ├── enrollment_sample_4.wav
│   │   └── enrollment_sample_5.wav
│   ├── user_002/
│   │   └── ...
│   └── user_003/
│       └── ...
│
├── genuine/
│   ├── user_001/
│   │   ├── test_genuine_1.wav
│   │   ├── test_genuine_2.wav
│   │   └── test_genuine_3.wav
│   ├── user_002/
│   │   └── ...
│   └── user_003/
│       └── ...
│
└── impostor/
    ├── user_001_vs_user_002.wav  # user_001 reclama, user_002 habla
    ├── user_001_vs_user_003.wav
    ├── user_002_vs_user_001.wav
    ├── user_002_vs_user_003.wav
    ├── user_003_vs_user_001.wav
    └── user_003_vs_user_002.wav
```

### Text Verification

```
dataset/text_verification/
├── transcription_tests.json      # Archivo de configuración
├── phrase_matching_tests.json    # Archivo de configuración
├── audio001.wav
├── audio002.wav
├── audio003.wav
├── phrase_test_001.wav
├── phrase_test_002.wav
└── phrase_test_003.wav
```

### Anti-Spoofing

```
dataset/antispoofing/
├── genuine/
│   ├── genuine_001.wav
│   ├── genuine_002.wav
│   ├── genuine_003.wav
│   └── ...
│
├── tts/
│   ├── tts_attack_001.wav
│   ├── tts_attack_002.wav
│   ├── tts_attack_003.wav
│   └── ...
│
└── cloning/
    ├── cloning_attack_001.wav
    ├── cloning_attack_002.wav
    ├── cloning_attack_003.wav
    └── ...
```

### Complete System

```
dataset/complete_system/
├── efficiency_test/
│   ├── efficiency_001.wav
│   ├── efficiency_002.wav
│   └── ...
│
├── snr_robustness/
│   └── genuine/
│       ├── high_snr_001.wav    # SNR > 20 dB
│       ├── high_snr_002.wav
│       ├── medium_snr_001.wav  # SNR 10-20 dB
│       ├── medium_snr_002.wav
│       ├── low_snr_001.wav     # SNR < 10 dB
│       └── low_snr_002.wav
│
├── duration_sensitivity/
│   ├── genuine/
│   │   ├── very_short_001.wav  # < 2 segundos
│   │   ├── short_001.wav       # 2-4 segundos
│   │   ├── medium_001.wav      # 4-6 segundos
│   │   └── long_001.wav        # > 6 segundos
│   └── spoof/
│       ├── spoof_short_001.wav
│       ├── spoof_medium_001.wav
│       └── spoof_long_001.wav
│
└── antispoofing/
    ├── genuine/
    │   ├── genuine_001.wav
    │   └── ...
    └── spoof/
        ├── spoof_001.wav
        └── ...
```

---

## 🎵 Requisitos de Audio

Todos los archivos de audio deben cumplir:

- **Formato:** WAV
- **Sample Rate:** 16000 Hz (16 kHz)
- **Canales:** Mono (1 canal)
- **Bit Depth:** 16 bits
- **Duración:**
  - Enrollment: 3-10 segundos (óptimo: 5 segundos)
  - Verification: 2-8 segundos (óptimo: 4 segundos)

---

## 🔧 Conversión de Audio

Si tienes audios en otros formatos, puedes convertirlos con:

```bash
# Usando ffmpeg
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav

# Usando sox
sox input.mp3 -r 16000 -c 1 -b 16 output.wav
```

---

## 📊 Recomendaciones de Tamaño del Dataset

Para obtener resultados significativos:

| Módulo | Mínimo Recomendado | Óptimo |
|--------|-------------------|--------|
| **Speaker Recognition** | 3 usuarios, 5 muestras c/u | 10+ usuarios, 10+ muestras |
| **Text Verification** | 20 audios de transcripción, 10 de phrase matching | 100+ audios de transcripción, 50+ phrase matching |
| **Anti-Spoofing** | 50 genuinos, 50 ataques | 200+ genuinos, 200+ ataques (balanceado TTS/Cloning) |
| **Complete System** | 30 audios por categoría | 100+ audios por categoría |

---

## ✅ Checklist de Preparación

Antes de ejecutar los scripts, verifica:

- [ ] Todos los audios están en formato WAV, 16kHz, mono, 16-bit
- [ ] Los archivos JSON tienen la estructura correcta
- [ ] Los nombres de archivo siguen las convenciones (user_vs_user para impostores)
- [ ] Las carpetas tienen suficientes muestras para estadísticas significativas
- [ ] Los audios tienen la duración adecuada (2-10 segundos)
- [ ] Los audios de diferentes SNR están correctamente categorizados
- [ ] Los audios genuinos y de ataque están balanceados

---

## 🚀 Próximos Pasos

1. Preparar los datasets según estas estructuras
2. Verificar la calidad de audio con herramientas como Audacity
3. Ejecutar los scripts de evaluación uno por uno
4. Revisar los reportes generados en `results/`
5. Analizar las métricas y ajustar según sea necesario

---

**Nota:** Estos son solo ejemplos. Adapta la estructura a tus necesidades específicas.
