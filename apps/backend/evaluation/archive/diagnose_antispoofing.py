"""
Script de diagnóstico para investigar problemas en el módulo antispoofing.

Prueba:
1. Verificar convención de scores (0=bonafide, 1=spoof o inverso)
2. Comparar rangos de salida de AASIST vs RawNet2
3. Verificar si el preprocesamiento elimina artefactos importantes
"""

import sys
import logging
from pathlib import Path
import numpy as np
import torch
import torchaudio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
from src.infrastructure.biometrics.local_antispoof_models import build_local_model_paths, LocalAASISTModel, LocalRawNet2Model

logger = logging.getLogger(__name__)


def diagnose_model_outputs():
    """Diagnóstico de salidas de modelos individuales."""
    print("=" * 80)
    print("DIAGNÓSTICO DE MODELOS ANTISPOOFING")
    print("=" * 80)
    print()
    
    # Configuración
    device = torch.device("cpu")
    paths = build_local_model_paths()
    
    # Cargar modelos individuales
    print("1. CARGANDO MODELOS INDIVIDUALES...")
    aasist = LocalAASISTModel(device, paths)
    rawnet2 = LocalRawNet2Model(device, paths)
    
    if not aasist.available or not rawnet2.available:
        print("❌ Error: No se pudieron cargar los modelos")
        return
    
    print(f"✅ AASIST disponible: {aasist.available}")
    print(f"✅ RawNet2 disponible: {rawnet2.available}")
    print()
    
    # Obtener audios de prueba
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_dir = project_root / "infra" / "evaluation" / "dataset"
    
    genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    # Probar con muestras reales
    print("2. PROBANDO CON AUDIOS REALES...")
    print("-" * 80)
    
    # Probar con 3 genuinos, 3 TTS, 3 cloning
    genuine_files = list(genuine_dir.rglob("*.wav"))[:3]
    tts_files = list(tts_dir.rglob("*.wav"))[:3]
    cloning_files = list(cloning_dir.rglob("*.wav"))[:3]
    
    results = {
        'genuine': {'aasist': [], 'rawnet2': []},
        'tts': {'aasist': [], 'rawnet2': []},
        'cloning': {'aasist': [], 'rawnet2': []}
    }
    
    def process_audio(audio_path: Path, label: str):
        """Procesar un audio y obtener scores de ambos modelos."""
        waveform, sr = torchaudio.load(audio_path)
        
        # Resample si es necesario
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        # Mono
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Obtener scores
        aasist_score = aasist.predict_spoof_probability(waveform, 16000)
        rawnet2_score = rawnet2.predict_spoof_probability(waveform, 16000)
        
        results[label]['aasist'].append(aasist_score)
        results[label]['rawnet2'].append(rawnet2_score)
        
        print(f"  {audio_path.name[:30]:30s}  AASIST: {aasist_score:.4f}  RawNet2: {rawnet2_score:.4f}")
    
    print("\n📗 AUDIOS GENUINOS (esperado: score bajo ~0.0):")
    for audio_file in genuine_files:
        process_audio(audio_file, 'genuine')
    
    print("\n📕 ATAQUES TTS (esperado: score alto ~1.0):")
    for audio_file in tts_files:
        process_audio(audio_file, 'tts')
    
    print("\n📙 ATAQUES CLONING (esperado: score alto ~1.0):")
    for audio_file in cloning_files:
        process_audio(audio_file, 'cloning')
    
    # Análisis estadístico
    print("\n" + "=" * 80)
    print("3. ANÁLISIS ESTADÍSTICO")
    print("=" * 80)
    
    for label in ['genuine', 'tts', 'cloning']:
        aasist_scores = results[label]['aasist']
        rawnet2_scores = results[label]['rawnet2']
        
        print(f"\n{label.upper()}:")
        print(f"  AASIST  - Media: {np.mean(aasist_scores):.4f}, Std: {np.std(aasist_scores):.4f}, "
              f"Rango: [{np.min(aasist_scores):.4f} - {np.max(aasist_scores):.4f}]")
        print(f"  RawNet2 - Media: {np.mean(rawnet2_scores):.4f}, Std: {np.std(rawnet2_scores):.4f}, "
              f"Rango: [{np.min(rawnet2_scores):.4f} - {np.max(rawnet2_scores):.4f}]")
    
    # Diagnóstico de problemas
    print("\n" + "=" * 80)
    print("4. DIAGNÓSTICO DE PROBLEMAS")
    print("=" * 80)
    
    # Problema 1: Verificar si los scores están invertidos
    genuine_mean_aasist = np.mean(results['genuine']['aasist'])
    attack_mean_aasist = np.mean(results['tts']['aasist'] + results['cloning']['aasist'])
    
    genuine_mean_rawnet2 = np.mean(results['genuine']['rawnet2'])
    attack_mean_rawnet2 = np.mean(results['tts']['rawnet2'] + results['cloning']['rawnet2'])
    
    print("\n🔍 Problema 1: Convención de Scores")
    if genuine_mean_aasist > attack_mean_aasist:
        print(f"  ⚠️  AASIST: Genuinos ({genuine_mean_aasist:.4f}) > Ataques ({attack_mean_aasist:.4f})")
        print("      → Los scores pueden estar INVERTIDOS para AASIST")
    else:
        print(f"  ✅ AASIST: Genuinos ({genuine_mean_aasist:.4f}) < Ataques ({attack_mean_aasist:.4f})")
    
    if genuine_mean_rawnet2 > attack_mean_rawnet2:
        print(f"  ⚠️  RawNet2: Genuinos ({genuine_mean_rawnet2:.4f}) > Ataques ({attack_mean_rawnet2:.4f})")
        print("      → Los scores pueden estar INVERTIDOS para RawNet2")
    else:
        print(f"  ✅ RawNet2: Genuinos ({genuine_mean_rawnet2:.4f}) < Ataques ({attack_mean_rawnet2:.4f})")
    
    # Problema 2: Normalización de rangos
    print("\n🔍 Problema 2: Rangos de Salida")
    all_aasist = results['genuine']['aasist'] + results['tts']['aasist'] + results['cloning']['aasist']
    all_rawnet2 = results['genuine']['rawnet2'] + results['tts']['rawnet2'] + results['cloning']['rawnet2']
    
    aasist_range = np.max(all_aasist) - np.min(all_aasist)
    rawnet2_range = np.max(all_rawnet2) - np.min(all_rawnet2)
    
    print(f"  AASIST rango:  {aasist_range:.4f}  [{np.min(all_aasist):.4f} - {np.max(all_aasist):.4f}]")
    print(f"  RawNet2 rango: {rawnet2_range:.4f}  [{np.min(all_rawnet2):.4f} - {np.max(all_rawnet2):.4f}]")
    
    if abs(aasist_range - rawnet2_range) > 0.3:
        print(f"  ⚠️  Rangos muy diferentes (diferencia: {abs(aasist_range - rawnet2_range):.4f})")
        print("      → Se necesita normalización antes del ensemble")
    else:
        print("  ✅ Rangos similares")
    
    # Problema 3: Separabilidad
    print("\n🔍 Problema 3: Separabilidad de Clases")
    
    separation_aasist = abs(genuine_mean_aasist - attack_mean_aasist)
    separation_rawnet2 = abs(genuine_mean_rawnet2 - attack_mean_rawnet2)
    
    print(f"  AASIST separación:  {separation_aasist:.4f}")
    print(f"  RawNet2 separación: {separation_rawnet2:.4f}")
    
    if separation_aasist < 0.1:
        print("  ⚠️  AASIST: Separación muy baja (< 0.1)")
    if separation_rawnet2 < 0.1:
        print("  ⚠️  RawNet2: Separación muy baja (< 0.1)")
    
    # Probar el ensemble actual
    print("\n" + "=" * 80)
    print("5. PRUEBA DEL ENSEMBLE ACTUAL")
    print("=" * 80)
    
    detector = SpoofDetectorAdapter(use_gpu=False)
    
    print("\n📗 GENUINOS:")
    for audio_file in genuine_files:
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        ensemble_score = detector.detect_spoof(audio_data)
        print(f"  {audio_file.name[:30]:30s}  Ensemble: {ensemble_score:.4f}")
    
    print("\n📕 ATAQUES TTS:")
    for audio_file in tts_files:
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        ensemble_score = detector.detect_spoof(audio_data)
        print(f"  {audio_file.name[:30]:30s}  Ensemble: {ensemble_score:.4f}")
    
    print("\n📙 ATAQUES CLONING:")
    for audio_file in cloning_files:
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        ensemble_score = detector.detect_spoof(audio_data)
        print(f"  {audio_file.name[:30]:30s}  Ensemble: {ensemble_score:.4f}")
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    diagnose_model_outputs()
