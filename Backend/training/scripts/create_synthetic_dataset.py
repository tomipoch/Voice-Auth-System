#!/usr/bin/env python3
"""
Script para crear un dataset sintético pequeño para probar el pipeline de entrenamiento.
Útil para validar que todo funciona antes de descargar datasets grandes.
"""

import os
import sys
import numpy as np
import soundfile as sf
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_speaker_data(output_dir: str, num_speakers: int = 10, 
                                  utterances_per_speaker: int = 20):
    """Genera dataset sintético para prueba de speaker recognition."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generando dataset sintético: {num_speakers} speakers, {utterances_per_speaker} utterances cada uno")
    
    # Crear directorio de audio
    audio_dir = output_path / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    manifest_data = []
    
    for speaker_id in range(num_speakers):
        speaker_name = f"speaker_{speaker_id:03d}"
        speaker_dir = audio_dir / speaker_name
        speaker_dir.mkdir(exist_ok=True)
        
        # Generar características únicas por speaker
        base_freq = 100 + speaker_id * 10  # Frecuencia base única
        formant_shift = speaker_id * 50     # Shift de formantes
        
        for utterance_id in range(utterances_per_speaker):
            # Generar audio sintético con características del speaker
            duration = 3.0  # 3 seconds
            sample_rate = 16000
            
            audio = generate_speaker_audio(
                duration=duration,
                sample_rate=sample_rate,
                base_freq=base_freq,
                formant_shift=formant_shift,
                speaker_id=speaker_id
            )
            
            # Guardar archivo
            filename = f"{speaker_name}_utt_{utterance_id:03d}.wav"
            file_path = speaker_dir / filename
            sf.write(str(file_path), audio, sample_rate)
            
            # Añadir a manifest
            split = "train" if utterance_id < utterances_per_speaker * 0.8 else "test"
            manifest_data.append({
                'file_path': str(file_path),
                'speaker_id': speaker_name,
                'duration': duration,
                'split': split
            })
    
    # Guardar manifest
    manifest_df = pd.DataFrame(manifest_data)
    manifest_path = output_path / "manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    
    logger.info(f"Dataset creado en: {output_path}")
    logger.info(f"Total archivos: {len(manifest_data)}")
    logger.info(f"Train: {len(manifest_df[manifest_df['split'] == 'train'])}")
    logger.info(f"Test: {len(manifest_df[manifest_df['split'] == 'test'])}")
    
    return str(manifest_path)

def generate_speaker_audio(duration: float, sample_rate: int, base_freq: float, 
                          formant_shift: float, speaker_id: int) -> np.ndarray:
    """Genera audio sintético con características específicas del speaker."""
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Frecuencia fundamental (pitch)
    f0 = base_freq + 50 * np.sin(2 * np.pi * 2 * t)  # Variación prosódica
    
    # Formantes típicos de vocales con shift específico del speaker
    formants = [
        800 + formant_shift,   # F1
        1200 + formant_shift,  # F2  
        2500 + formant_shift   # F3
    ]
    
    # Generar señal
    signal = np.zeros_like(t)
    
    # Onda portadora (pitch)
    carrier = np.sin(2 * np.pi * f0 * t)
    
    # Añadir formantes
    for i, formant in enumerate(formants):
        amplitude = 0.3 / (i + 1)  # Amplitud decreciente
        formant_signal = amplitude * np.sin(2 * np.pi * formant * t)
        signal += formant_signal * carrier
    
    # Añadir ruido característico del speaker
    np.random.seed(speaker_id)  # Ruido consistente por speaker
    noise = np.random.normal(0, 0.1, len(t))
    signal += noise
    
    # Envolvente temporal (simulando speech)
    envelope = np.exp(-0.5 * t) + 0.3  # Decay + baseline
    signal *= envelope
    
    # Normalizar
    signal = signal / (np.max(np.abs(signal)) + 1e-8)
    
    return signal

def generate_antispoofing_data(output_dir: str, num_genuine: int = 100, num_spoof: int = 100):
    """Genera dataset sintético para anti-spoofing."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generando dataset anti-spoofing: {num_genuine} genuine, {num_spoof} spoof")
    
    # Crear directorio de audio
    audio_dir = output_path / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    manifest_data = []
    
    # Generar audios genuine
    for i in range(num_genuine):
        audio = generate_genuine_audio()
        filename = f"genuine_{i:03d}.wav"
        file_path = audio_dir / filename
        sf.write(str(file_path), audio, 16000)
        
        manifest_data.append({
            'file_path': str(file_path),
            'label': 'bonafide',
            'attack_type': '-',
            'split': 'train' if i < num_genuine * 0.8 else 'test'
        })
    
    # Generar audios spoof
    for i in range(num_spoof):
        audio = generate_spoof_audio(attack_type=i % 3)  # 3 tipos de ataques
        filename = f"spoof_{i:03d}.wav"
        file_path = audio_dir / filename
        sf.write(str(file_path), audio, 16000)
        
        manifest_data.append({
            'file_path': str(file_path),
            'label': 'spoof',
            'attack_type': f'A{(i % 3) + 1:02d}',
            'split': 'train' if i < num_spoof * 0.8 else 'test'
        })
    
    # Guardar manifest
    manifest_df = pd.DataFrame(manifest_data)
    manifest_path = output_path / "antispoofing_manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    
    logger.info(f"Dataset anti-spoofing creado en: {output_path}")
    
    return str(manifest_path)

def generate_genuine_audio() -> np.ndarray:
    """Genera audio genuino (natural)."""
    duration = 4.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Audio natural con características humanas
    f0 = 150 + 30 * np.sin(2 * np.pi * 1.5 * t)  # Pitch natural
    
    # Múltiples formantes
    signal = np.zeros_like(t)
    formants = [800, 1200, 2500, 3500]
    
    for i, formant in enumerate(formants):
        amplitude = 0.4 / (i + 1)
        signal += amplitude * np.sin(2 * np.pi * formant * t) * np.sin(2 * np.pi * f0 * t)
    
    # Ruido natural
    signal += np.random.normal(0, 0.05, len(t))
    
    # Normalizar
    return signal / (np.max(np.abs(signal)) + 1e-8)

def generate_spoof_audio(attack_type: int) -> np.ndarray:
    """Genera audio sintético (spoof) con diferentes tipos de ataque."""
    duration = 4.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    if attack_type == 0:  # TTS-like
        # Audio más robotico, frecuencias exactas
        f0 = 140  # Pitch constante
        signal = np.sin(2 * np.pi * f0 * t)
        
        # Formantes exactos (no naturales)
        formants = [800, 1200, 2400]
        for formant in formants:
            signal += 0.3 * np.sin(2 * np.pi * formant * t)
            
    elif attack_type == 1:  # Voice conversion
        # Audio con artefactos de conversión
        f0 = 160 + 20 * np.sin(2 * np.pi * 3 * t)  # Pitch inestable
        signal = np.sin(2 * np.pi * f0 * t)
        
        # Artefactos en alta frecuencia
        signal += 0.2 * np.sin(2 * np.pi * 8000 * t)
        
    else:  # Replay attack
        # Audio natural pero con reverberación/eco
        signal = generate_genuine_audio()
        
        # Añadir eco
        delay_samples = int(0.1 * sample_rate)
        echo = np.zeros_like(signal)
        echo[delay_samples:] = 0.3 * signal[:-delay_samples]
        signal += echo
    
    # Normalizar
    return signal / (np.max(np.abs(signal)) + 1e-8)

def main():
    """Función principal."""
    base_dir = "./training/datasets/synthetic"
    
    print("🧪 **GENERANDO DATASETS SINTÉTICOS PARA PRUEBAS**")
    print("=" * 60)
    
    # Dataset speaker recognition
    print("📢 Generando dataset speaker recognition...")
    speaker_manifest = generate_synthetic_speaker_data(
        output_dir=f"{base_dir}/speaker_recognition",
        num_speakers=5,  # Pequeño para pruebas
        utterances_per_speaker=10
    )
    
    # Dataset anti-spoofing
    print("🛡️ Generando dataset anti-spoofing...")
    antispoofing_manifest = generate_antispoofing_data(
        output_dir=f"{base_dir}/anti_spoofing",
        num_genuine=50,  # Pequeño para pruebas
        num_spoof=50
    )
    
    print("\n✅ **DATASETS SINTÉTICOS CREADOS**")
    print(f"📁 Speaker Recognition: {speaker_manifest}")
    print(f"📁 Anti-Spoofing: {antispoofing_manifest}")
    print("\n🚀 **Ahora puedes probar el entrenamiento con:**")
    print("cd training/scripts")
    print("python train_models.py --model ecapa_tdnn --dry-run")

if __name__ == "__main__":
    main()