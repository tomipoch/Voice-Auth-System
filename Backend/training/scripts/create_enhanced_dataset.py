#!/usr/bin/env python3
"""
Crea dataset sintético mejorado y más realista para entrenamiento inmediato.
"""

import numpy as np
import soundfile as sf
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_enhanced_synthetic_dataset():
    """Crea dataset sintético mejorado con más realismo."""
    
    print("🧪 **CREANDO DATASET SINTÉTICO MEJORADO**")
    print("=" * 60)
    
    # Configuración del dataset
    config = {
        "num_speakers": 20,  # Más speakers
        "utterances_per_speaker": 50,  # Más utterances
        "genuine_samples": 200,  # Para anti-spoofing
        "spoof_samples": 200,
        "duration_range": (2.0, 8.0),  # Duración variable
        "sample_rate": 16000
    }
    
    base_dir = Path("../datasets/enhanced_synthetic")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📊 Configuración:")
    for key, value in config.items():
        print(f"   - {key}: {value}")
    
    # 1. Speaker Recognition Dataset
    print("\n📢 Creando dataset Speaker Recognition...")
    speaker_manifest = create_speaker_dataset(base_dir / "speaker_recognition", config)
    
    # 2. Anti-Spoofing Dataset  
    print("\n🛡️ Creando dataset Anti-Spoofing...")
    antispoofing_manifest = create_antispoofing_dataset(base_dir / "anti_spoofing", config)
    
    # 3. ASR Dataset
    print("\n🗣️ Creando dataset ASR...")
    asr_manifest = create_asr_dataset(base_dir / "asr", config)
    
    print(f"\n✅ **DATASET SINTÉTICO MEJORADO CREADO**")
    print(f"📁 Ubicación: {base_dir}")
    print(f"📊 Total archivos: {len(pd.read_csv(speaker_manifest)) + len(pd.read_csv(antispoofing_manifest)) + len(pd.read_csv(asr_manifest))}")
    
    return base_dir

def create_speaker_dataset(output_dir, config):
    """Crea dataset mejorado para speaker recognition."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    manifest_data = []
    
    for speaker_id in range(config["num_speakers"]):
        speaker_name = f"spk_{speaker_id:03d}"
        speaker_dir = audio_dir / speaker_name
        speaker_dir.mkdir(exist_ok=True)
        
        # Características únicas del speaker
        speaker_profile = generate_speaker_profile(speaker_id)
        
        for utt_id in range(config["utterances_per_speaker"]):
            # Duración variable
            duration = np.random.uniform(*config["duration_range"])
            
            # Generar audio con perfil del speaker
            audio = generate_realistic_speech(
                duration=duration,
                sample_rate=config["sample_rate"],
                speaker_profile=speaker_profile,
                utterance_id=utt_id
            )
            
            # Guardar archivo
            filename = f"{speaker_name}_utt_{utt_id:03d}.wav"
            file_path = speaker_dir / filename
            sf.write(str(file_path), audio, config["sample_rate"])
            
            # Añadir a manifest
            split = determine_split(utt_id, config["utterances_per_speaker"])
            manifest_data.append({
                'file_path': str(file_path.relative_to(output_dir.parent.parent)),
                'speaker_id': speaker_name,
                'duration': duration,
                'split': split,
                'gender': speaker_profile['gender'],
                'age_group': speaker_profile['age_group']
            })
    
    # Guardar manifest
    manifest_path = output_dir / "manifest.csv"
    pd.DataFrame(manifest_data).to_csv(manifest_path, index=False)
    
    logger.info(f"Speaker dataset creado: {len(manifest_data)} archivos")
    return str(manifest_path)

def create_antispoofing_dataset(output_dir, config):
    """Crea dataset mejorado para anti-spoofing."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    manifest_data = []
    
    # Audios genuine (bonafide)
    for i in range(config["genuine_samples"]):
        duration = np.random.uniform(*config["duration_range"])
        audio = generate_genuine_speech(duration, config["sample_rate"])
        
        filename = f"bonafide_{i:03d}.wav"
        file_path = audio_dir / filename
        sf.write(str(file_path), audio, config["sample_rate"])
        
        manifest_data.append({
            'file_path': str(file_path.relative_to(output_dir.parent.parent)),
            'label': 'bonafide',
            'attack_type': '-',
            'split': determine_split(i, config["genuine_samples"])
        })
    
    # Audios spoof con diferentes ataques
    attack_types = ['TTS', 'VC', 'Replay', 'Deepfake', 'Synthetic']
    
    for i in range(config["spoof_samples"]):
        duration = np.random.uniform(*config["duration_range"])
        attack_type = attack_types[i % len(attack_types)]
        
        audio = generate_spoof_speech(duration, config["sample_rate"], attack_type)
        
        filename = f"spoof_{attack_type}_{i:03d}.wav"
        file_path = audio_dir / filename
        sf.write(str(file_path), audio, config["sample_rate"])
        
        manifest_data.append({
            'file_path': str(file_path.relative_to(output_dir.parent.parent)),
            'label': 'spoof',
            'attack_type': attack_type,
            'split': determine_split(i, config["spoof_samples"])
        })
    
    # Guardar manifest
    manifest_path = output_dir / "antispoofing_manifest.csv"
    pd.DataFrame(manifest_data).to_csv(manifest_path, index=False)
    
    logger.info(f"Anti-spoofing dataset creado: {len(manifest_data)} archivos")
    return str(manifest_path)

def create_asr_dataset(output_dir, config):
    """Crea dataset para ASR con frases conocidas."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    # Frases para verificación
    phrases = [
        "Please verify my identity now",
        "My voice is my password", 
        "Authenticate using voice biometrics",
        "Voice identification system active",
        "Confirm identity with speech pattern"
    ]
    
    manifest_data = []
    
    for i, phrase in enumerate(phrases * 20):  # 100 samples total
        duration = len(phrase.split()) * 0.3 + np.random.uniform(1.0, 2.0)
        
        audio = generate_speech_with_text(
            phrase=phrase,
            duration=duration,
            sample_rate=config["sample_rate"]
        )
        
        filename = f"phrase_{i:03d}.wav"
        file_path = audio_dir / filename
        sf.write(str(file_path), audio, config["sample_rate"])
        
        manifest_data.append({
            'file_path': str(file_path.relative_to(output_dir.parent.parent)),
            'phrase': phrase,
            'duration': duration,
            'split': determine_split(i, 100)
        })
    
    # Guardar manifest
    manifest_path = output_dir / "asr_manifest.csv"
    pd.DataFrame(manifest_data).to_csv(manifest_path, index=False)
    
    logger.info(f"ASR dataset creado: {len(manifest_data)} archivos")
    return str(manifest_path)

def generate_speaker_profile(speaker_id):
    """Genera perfil único para cada speaker."""
    np.random.seed(speaker_id)  # Consistencia
    
    return {
        'gender': 'male' if speaker_id % 2 == 0 else 'female',
        'age_group': ['young', 'adult', 'senior'][speaker_id % 3],
        'base_f0': 100 + speaker_id * 5 + np.random.uniform(-10, 10),
        'formant_shift': speaker_id * 20 + np.random.uniform(-50, 50),
        'speaking_rate': 0.8 + (speaker_id % 5) * 0.1,
        'voice_quality': np.random.uniform(0.5, 1.0)
    }

def generate_realistic_speech(duration, sample_rate, speaker_profile, utterance_id):
    """Genera audio realista con características del speaker."""
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Pitch base del speaker
    f0_base = speaker_profile['base_f0']
    
    # Variación prosódica realista
    prosody = 1 + 0.3 * np.sin(2 * np.pi * 2 * t + utterance_id)
    f0 = f0_base * prosody
    
    # Formantes con shift del speaker
    formants = [
        800 + speaker_profile['formant_shift'],
        1200 + speaker_profile['formant_shift'],
        2500 + speaker_profile['formant_shift']
    ]
    
    # Generar señal
    signal = np.zeros_like(t)
    
    # Onda portadora
    carrier = np.sin(2 * np.pi * f0 * t)
    
    # Formantes con amplitudes variables
    for i, formant in enumerate(formants):
        amplitude = 0.4 / (i + 1) * speaker_profile['voice_quality']
        formant_signal = amplitude * np.sin(2 * np.pi * formant * t)
        signal += formant_signal * carrier
    
    # Ruido de fondo realista
    noise_level = 0.02 * (1 + utterance_id % 3)  # Variación de ruido
    signal += np.random.normal(0, noise_level, len(t))
    
    # Envolvente de speech
    envelope = create_speech_envelope(t, duration)
    signal *= envelope
    
    # Normalizar
    return signal / (np.max(np.abs(signal)) + 1e-8)

def generate_genuine_speech(duration, sample_rate):
    """Genera audio genuino con características naturales."""
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Características naturales
    f0 = 150 + 30 * np.sin(2 * np.pi * 1.5 * t)  # Variación natural
    
    signal = np.zeros_like(t)
    formants = [800, 1200, 2500, 3500]
    
    for i, formant in enumerate(formants):
        amplitude = 0.4 / (i + 1)
        signal += amplitude * np.sin(2 * np.pi * formant * t) * np.sin(2 * np.pi * f0 * t)
    
    # Ruido natural
    signal += np.random.normal(0, 0.03, len(t))
    
    # Envolvente natural
    envelope = create_speech_envelope(t, duration)
    signal *= envelope
    
    return signal / (np.max(np.abs(signal)) + 1e-8)

def generate_spoof_speech(duration, sample_rate, attack_type):
    """Genera audio spoof según tipo de ataque."""
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    if attack_type == 'TTS':
        # TTS: pitch más constante, artefactos
        f0 = 140  # Constante
        signal = np.sin(2 * np.pi * f0 * t)
        
        # Artefactos de síntesis
        signal += 0.1 * np.sin(2 * np.pi * 4000 * t)  # Artefacto alta frecuencia
        
    elif attack_type == 'VC':
        # Voice Conversion: pitch inestable
        f0 = 160 + 40 * np.sin(2 * np.pi * 5 * t)  # Inestable
        signal = np.sin(2 * np.pi * f0 * t)
        
    elif attack_type == 'Replay':
        # Replay: audio natural con reverb
        signal = generate_genuine_speech(duration, sample_rate)
        
        # Añadir reverberación
        delay_samples = int(0.15 * sample_rate)
        if len(signal) > delay_samples:
            echo = np.zeros_like(signal)
            echo[delay_samples:] = 0.4 * signal[:-delay_samples]
            signal += echo
            
    elif attack_type == 'Deepfake':
        # Deepfake: mezcla de características
        f0 = 145 + 25 * np.sin(2 * np.pi * 3 * t)
        signal = np.sin(2 * np.pi * f0 * t)
        
        # Artefactos de GAN
        signal += 0.05 * np.random.uniform(-1, 1, len(t))
        
    else:  # Synthetic
        # Completamente sintético
        f0 = 130
        signal = np.sin(2 * np.pi * f0 * t)
        signal += 0.3 * np.sin(2 * np.pi * 800 * t)
    
    # Normalizar
    return signal / (np.max(np.abs(signal)) + 1e-8)

def generate_speech_with_text(phrase, duration, sample_rate):
    """Genera audio que simula decir una frase específica."""
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simular patrones de speech basados en la frase
    words = phrase.split()
    num_words = len(words)
    
    signal = np.zeros_like(t)
    
    # Dividir tiempo por palabras
    word_duration = duration / num_words
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        end_time = (i + 1) * word_duration
        
        # Indices de tiempo para esta palabra
        start_idx = int(start_time * sample_rate)
        end_idx = int(end_time * sample_rate)
        
        if end_idx <= len(signal):
            word_t = t[start_idx:end_idx]
            
            # Frecuencia base según características de la palabra
            word_f0 = 150 + len(word) * 10 + i * 5
            
            # Generar señal para esta palabra
            word_signal = np.sin(2 * np.pi * word_f0 * word_t)
            
            # Añadir formantes
            for formant in [800, 1200, 2500]:
                word_signal += 0.3 * np.sin(2 * np.pi * formant * word_t)
            
            # Añadir a señal principal
            signal[start_idx:end_idx] = word_signal
    
    # Ruido de fondo
    signal += np.random.normal(0, 0.02, len(t))
    
    return signal / (np.max(np.abs(signal)) + 1e-8)

def create_speech_envelope(t, duration):
    """Crea envolvente realista de speech."""
    
    # Envolvente general
    envelope = np.ones_like(t)
    
    # Fade in/out
    fade_duration = 0.1  # 100ms
    fade_samples = int(fade_duration * len(t) / duration)
    
    # Fade in
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    
    # Fade out
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    
    # Variaciones de amplitud (simulando silabas)
    num_variations = int(duration * 3)  # ~3 variaciones por segundo
    for _ in range(num_variations):
        center = np.random.randint(fade_samples, len(t) - fade_samples)
        width = np.random.randint(500, 2000)
        amplitude = np.random.uniform(0.7, 1.0)
        
        start = max(0, center - width//2)
        end = min(len(t), center + width//2)
        
        envelope[start:end] *= amplitude
    
    return envelope

def determine_split(index, total):
    """Determina split train/dev/test."""
    ratio = index / total
    if ratio < 0.7:
        return 'train'
    elif ratio < 0.85:
        return 'dev'
    else:
        return 'test'

if __name__ == "__main__":
    create_enhanced_synthetic_dataset()