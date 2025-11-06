# Audio Samples para Testing

Esta carpeta contiene muestras de audio para probar el sistema de biometría vocal.

## 📁 Estructura de Carpetas

### `enrollment/`
Audios para el proceso de enrollment (registro de usuario):
- `voice_auth_sample.wav` - "voice authentication is working well"
- `verify_identity_sample.wav` - "please verify my identity now"
- `banking_security_sample.wav` - "banking security is very important"

### `verification/`
Audios para el proceso de verificación:
- `hello_world_sample.wav` - "hello world how are you today"
- `biometric_security_sample.wav` - "biometric systems provide security"

### `spoofing/`
Audios sintéticos para testing de anti-spoofing (opcional):
- Audios generados por TTS o deepfakes para probar detección

## 🎤 Especificaciones de Audio

- **Formato**: WAV
- **Frecuencia**: 16000 Hz (16kHz)
- **Canales**: Mono (1 canal)
- **Duración**: 3-5 segundos por frase
- **Bit depth**: 16-bit

## 📝 Frases a Grabar

1. **voice_auth_sample.wav**: "voice authentication is working well"
2. **verify_identity_sample.wav**: "please verify my identity now"  
3. **banking_security_sample.wav**: "banking security is very important"
4. **hello_world_sample.wav**: "hello world how are you today"
5. **biometric_security_sample.wav**: "biometric systems provide security"

## 🧪 Cómo Usar

```python
# Ejemplo de uso en tests
audio_path = "Backend/audio_samples/enrollment/voice_auth_sample.wav"
with open(audio_path, 'rb') as f:
    audio_data = f.read()
    
# Usar en los adapters
speaker_adapter = SpeakerEmbeddingAdapter()
embedding = speaker_adapter.extract_embedding(audio_data, "wav")
```

## ⚙️ Conversión de Formato (si es necesario)

Si grabas en otro formato, puedes convertir con:

```bash
# Con ffmpeg
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav

# Con Python (si tienes librería)
import librosa
import soundfile as sf

audio, sr = librosa.load('input.m4a', sr=16000, mono=True)
sf.write('output.wav', audio, 16000)
```