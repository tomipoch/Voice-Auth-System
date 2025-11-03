#!/usr/bin/env python3
"""
Test simple para verificar que los modelos están funcionando correctamente.
"""

import sys
import os
import numpy as np
import io
import wave
import torch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def generate_test_audio(duration=3.0, sample_rate=16000):
    """Genera audio de prueba sintético."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simula características de voz humana
    fundamental_freq = 150  # Frecuencia fundamental típica
    formants = [800, 1200, 2500]  # Formantes de vocales
    
    signal = np.zeros_like(t)
    
    # Genera formantes con ruido
    for formant in formants:
        signal += np.sin(2 * np.pi * formant * t) * np.random.normal(0.5, 0.1, len(t))
    
    # Añade ruido de fondo
    signal += np.random.normal(0, 0.05, len(t))
    
    # Normaliza
    signal = np.clip(signal, -1, 1)
    signal = (signal * 32767).astype(np.int16)
    
    # Convierte a bytes WAV
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal.tobytes())
    
    return buffer.getvalue()

def test_models():
    """Test de los modelos implementados."""
    print("🔬 **INICIANDO TESTS DE MODELOS BIOMÉTRICOS**")
    print("=" * 60)
    
    # Test 1: Model Manager
    print("\n📋 **TEST 1: Model Manager**")
    try:
        from infrastructure.biometrics.model_manager import ModelManager
        manager = ModelManager()
        
        models = manager.list_models()
        print(f"✅ Modelos configurados: {len(models)}")
        for model_id, config in models.items():
            print(f"   - {model_id}: {config.get('description', 'No description')}")
        
        print("✅ Model Manager funcional")
    except Exception as e:
        print(f"❌ Error en Model Manager: {e}")
    
    # Test 2: Speaker Recognition
    print("\n🎤 **TEST 2: Speaker Recognition (ECAPA-TDNN)**")
    try:
        from infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
        
        adapter = SpeakerEmbeddingAdapter(model_type="ecapa_tdnn")
        audio_data = generate_test_audio()
        
        embedding = adapter.extract_embedding(audio_data)
        print(f"✅ Embedding extraído: {len(embedding)} dimensiones")
        
        # Test similarity
        embedding2 = adapter.extract_embedding(generate_test_audio(duration=2.5))
        similarity = adapter.calculate_similarity(embedding, embedding2)
        print(f"✅ Similaridad calculada: {similarity:.4f}")
        
        print("✅ Speaker Recognition funcional")
    except Exception as e:
        print(f"❌ Error en Speaker Recognition: {e}")
    
    # Test 3: Anti-Spoofing
    print("\n🛡️ **TEST 3: Anti-Spoofing Detection**")
    try:
        from infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
        
        detector = SpoofDetectorAdapter()
        audio_data = generate_test_audio()
        
        is_genuine, confidence = detector.detect_spoofing(audio_data)
        print(f"✅ Detección: {'Genuino' if is_genuine else 'Spoofing'} (confianza: {confidence:.4f})")
        
        print("✅ Anti-Spoofing funcional")
    except Exception as e:
        print(f"❌ Error en Anti-Spoofing: {e}")
    
    # Test 4: ASR
    print("\n🗣️ **TEST 4: ASR (Automatic Speech Recognition)**")
    try:
        from infrastructure.biometrics.ASRAdapter import ASRAdapter
        
        asr = ASRAdapter()
        audio_data = generate_test_audio()
        
        transcript = asr.transcribe(audio_data)
        print(f"✅ Transcripción: '{transcript}'")
        
        # Test phrase verification
        is_match, confidence = asr.verify_phrase(audio_data, "hello world")
        print(f"✅ Verificación de frase: {'Match' if is_match else 'No match'} (confianza: {confidence:.4f})")
        
        print("✅ ASR funcional")
    except Exception as e:
        print(f"❌ Error en ASR: {e}")
    
    # Test 5: Dual Model Comparison
    print("\n🔄 **TEST 5: Dual Model Comparison (ECAPA vs x-vector)**")
    try:
        from infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
        
        adapter = SpeakerEmbeddingAdapter(model_type="ecapa_tdnn")
        audio_data = generate_test_audio()
        
        comparison = adapter.compare_models(audio_data, audio_data)
        print(f"✅ Comparación de modelos:")
        print(f"   - ECAPA-TDNN similaridad: {comparison['ecapa_tdnn_similarity']:.4f}")
        print(f"   - x-vector similaridad: {comparison['x_vector_similarity']:.4f}")
        print(f"   - Diferencia: {comparison['similarity_difference']:.4f}")
        
        print("✅ Dual Model Comparison funcional")
    except Exception as e:
        print(f"❌ Error en Dual Model Comparison: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 **TESTS COMPLETADOS**")

if __name__ == "__main__":
    test_models()