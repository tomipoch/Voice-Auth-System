"""
Verificar la interpretación correcta de los scores de anti-spoofing.

Este script ayuda a identificar si los scores están invertidos.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

def verify_score_interpretation():
    """
    Verifica la interpretación de los scores.
    
    Expectativa:
    - Genuinos deberían tener spoof_probability BAJA (cerca de 0.0)
    - Ataques deberían tener spoof_probability ALTA (cerca de 1.0)
    """
    
    print("="*80)
    print("VERIFICACIÓN DE SCORES ANTI-SPOOFING")
    print("="*80)
    
    detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
    
    # Dataset está en infra/evaluation/dataset
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "tts"
    cloning_dir = dataset_dir / "cloning"
    
    print(f"\n📁 Dataset directory: {dataset_dir}")
    print(f"   Existe: {dataset_dir.exists()}")
    
    # Procesar algunos ejemplos de cada tipo
    print("\n📊 ANALIZANDO SCORES...")
    print("-" * 80)
    
    # Genuinos
    genuine_files = sorted(genuine_dir.rglob("*.wav"))[:5]
    print(f"\n✅ GENUINOS (deberían tener score BAJO, cerca de 0.0):")
    genuine_scores = []
    for audio_path in genuine_files:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        score = detector.detect_spoof(audio_data)
        genuine_scores.append(score)
        print(f"  {audio_path.name}: {score:.4f}")
    
    # TTS
    tts_files = sorted(tts_dir.rglob("*.wav"))[:5] if tts_dir.exists() else []
    if tts_files:
        print(f"\n🤖 TTS ATTACKS (deberían tener score ALTO, cerca de 1.0):")
        tts_scores = []
        for audio_path in tts_files:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            score = detector.detect_spoof(audio_data)
            tts_scores.append(score)
            print(f"  {audio_path.name}: {score:.4f}")
    
    # Cloning
    cloning_files = sorted(cloning_dir.rglob("*.wav"))[:5] if cloning_dir.exists() else []
    if cloning_files:
        print(f"\n🎭 VOICE CLONING (deberían tener score ALTO, cerca de 1.0):")
        cloning_scores = []
        for audio_path in cloning_files:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            score = detector.detect_spoof(audio_data)
            cloning_scores.append(score)
            print(f"  {audio_path.name}: {score:.4f}")
    
    # Análisis
    print("\n" + "="*80)
    print("📈 ANÁLISIS DE PROMEDIOS")
    print("="*80)
    
    genuine_mean = np.mean(genuine_scores)
    print(f"\n✅ Genuinos - Score promedio: {genuine_mean:.4f}")
    
    if tts_files:
        tts_mean = np.mean(tts_scores)
        print(f"🤖 TTS - Score promedio: {tts_mean:.4f}")
        
        if tts_mean < genuine_mean:
            print("\n⚠️  PROBLEMA DETECTADO:")
            print("    Los scores de TTS son MÁS BAJOS que los de genuinos")
            print("    Esto sugiere que los scores están INVERTIDOS o mal calibrados")
            print("\n💡 SOLUCIÓN:")
            print("    1. Verificar si los modelos devuelven 'genuineness' en lugar de 'spoof_prob'")
            print("    2. Invertir scores: spoof_prob = 1.0 - model_output")
            print("    3. O ajustar la selección de columna en el output del modelo")
    
    if cloning_files:
        cloning_mean = np.mean(cloning_scores)
        print(f"🎭 Cloning - Score promedio: {cloning_mean:.4f}")
        
        if cloning_mean < genuine_mean * 1.2:  # Cloning debería ser claramente más alto
            print("\n⚠️  ADVERTENCIA:")
            print("    Los scores de Cloning no son significativamente más altos que genuinos")
            print("    El modelo tiene dificultad distinguiendo voice cloning de voz real")
    
    print("\n" + "="*80)
    print("INTERPRETACIÓN ESPERADA:")
    print("="*80)
    print("✅ Genuinos: 0.0 - 0.3 (baja probabilidad de spoof)")
    print("🤖 TTS: 0.7 - 1.0 (alta probabilidad de spoof)")  
    print("🎭 Cloning: 0.7 - 1.0 (alta probabilidad de spoof)")
    print("="*80)

if __name__ == "__main__":
    verify_score_interpretation()
