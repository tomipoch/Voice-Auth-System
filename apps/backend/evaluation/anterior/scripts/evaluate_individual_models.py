"""
Evaluar modelos anti-spoofing individuales vs ensemble para identificar
cuál modelo contribuye mejor a las métricas.

Evalúa:
1. AASIST solo
2. RawNet2 solo  
3. Ensemble AASIST (55%) + RawNet2 (45%)
4. AASIST-L solo
5. Ensemble AASIST-L (55%) + RawNet2 (45%)
"""

import sys
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

import torch
from infrastructure.biometrics.local_antispoof_models import (
    LocalAASISTModel,
    LocalRawNet2Model,
    build_local_model_paths
)
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)


def load_audio(filepath):
    """Cargar audio con torchaudio."""
    import torchaudio
    waveform, sample_rate = torchaudio.load(filepath)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    return waveform.squeeze(0), 16000


def evaluate_individual_models():
    """Evaluar cada modelo individualmente."""
    
    print("="*80)
    print("EVALUACIÓN DE MODELOS INDIVIDUALES VS ENSEMBLE")
    print("="*80)
    
    # Dataset
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav"))
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    print(f"\n📁 Dataset: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning")
    
    # Cargar modelos
    device = torch.device("cpu")
    local_paths = build_local_model_paths()
    
    print("\n🔧 Cargando modelos...")
    
    # Temporalmente deshabilitar AASIST-L para cargar AASIST base
    aasist_l_path = local_paths.aasist_dir / "AASIST-L.pth"
    aasist_l_backup = None
    if aasist_l_path.exists():
        aasist_l_backup = aasist_l_path.with_suffix('.pth.backup')
        aasist_l_path.rename(aasist_l_backup)
    
    try:
        aasist_base = LocalAASISTModel(device=device, paths=local_paths)
        if not aasist_base.available:
            print("❌ AASIST base no disponible")
            return
        print("   ✅ AASIST base cargado")
    finally:
        if aasist_l_backup and aasist_l_backup.exists():
            aasist_l_backup.rename(aasist_l_path)
    
    # Cargar AASIST-L
    aasist_l = LocalAASISTModel(device=device, paths=local_paths)
    if not aasist_l.available:
        print("❌ AASIST-L no disponible")
        return
    print("   ✅ AASIST-L cargado")
    
    # Cargar RawNet2
    rawnet2 = LocalRawNet2Model(device=device, paths=local_paths)
    if not rawnet2.available:
        print("❌ RawNet2 no disponible")
        return
    print("   ✅ RawNet2 cargado")
    
    # Procesar todos los audios
    print("\n🔄 Procesando audios...")
    
    results = {
        'genuine': {'aasist_base': [], 'aasist_l': [], 'rawnet2': []},
        'tts': {'aasist_base': [], 'aasist_l': [], 'rawnet2': []},
        'cloning': {'aasist_base': [], 'aasist_l': [], 'rawnet2': []}
    }
    
    # Procesar genuinos
    print(f"   Procesando {len(genuine_files)} genuinos...")
    for i, filepath in enumerate(genuine_files):
        if (i + 1) % 20 == 0:
            print(f"      {i+1}/{len(genuine_files)}")
        
        waveform, sr = load_audio(filepath)
        waveform_tensor = waveform.unsqueeze(0)
        
        # Temporalmente deshabilitar AASIST-L
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        aasist_base_model = LocalAASISTModel(device=device, paths=local_paths)
        score_base = aasist_base_model.predict_spoof_probability(waveform_tensor, sr)
        if aasist_l_backup.exists():
            aasist_l_backup.rename(aasist_l_path)
        
        score_l = aasist_l.predict_spoof_probability(waveform_tensor, sr)
        score_rawnet2 = rawnet2.predict_spoof_probability(waveform_tensor, sr)
        
        if score_base is not None:
            results['genuine']['aasist_base'].append(score_base)
        if score_l is not None:
            results['genuine']['aasist_l'].append(score_l)
        if score_rawnet2 is not None:
            results['genuine']['rawnet2'].append(score_rawnet2)
    
    # Procesar TTS
    print(f"   Procesando {len(tts_files)} TTS...")
    for i, filepath in enumerate(tts_files):
        if (i + 1) % 20 == 0:
            print(f"      {i+1}/{len(tts_files)}")
        
        waveform, sr = load_audio(filepath)
        waveform_tensor = waveform.unsqueeze(0)
        
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        aasist_base_model = LocalAASISTModel(device=device, paths=local_paths)
        score_base = aasist_base_model.predict_spoof_probability(waveform_tensor, sr)
        if aasist_l_backup.exists():
            aasist_l_backup.rename(aasist_l_path)
        
        score_l = aasist_l.predict_spoof_probability(waveform_tensor, sr)
        score_rawnet2 = rawnet2.predict_spoof_probability(waveform_tensor, sr)
        
        if score_base is not None:
            results['tts']['aasist_base'].append(score_base)
        if score_l is not None:
            results['tts']['aasist_l'].append(score_l)
        if score_rawnet2 is not None:
            results['tts']['rawnet2'].append(score_rawnet2)
    
    # Procesar Cloning
    print(f"   Procesando {len(cloning_files)} cloning...")
    for i, filepath in enumerate(cloning_files):
        if (i + 1) % 20 == 0:
            print(f"      {i+1}/{len(cloning_files)}")
        
        waveform, sr = load_audio(filepath)
        waveform_tensor = waveform.unsqueeze(0)
        
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        aasist_base_model = LocalAASISTModel(device=device, paths=local_paths)
        score_base = aasist_base_model.predict_spoof_probability(waveform_tensor, sr)
        if aasist_l_backup.exists():
            aasist_l_backup.rename(aasist_l_path)
        
        score_l = aasist_l.predict_spoof_probability(waveform_tensor, sr)
        score_rawnet2 = rawnet2.predict_spoof_probability(waveform_tensor, sr)
        
        if score_base is not None:
            results['cloning']['aasist_base'].append(score_base)
        if score_l is not None:
            results['cloning']['aasist_l'].append(score_l)
        if score_rawnet2 is not None:
            results['cloning']['rawnet2'].append(score_rawnet2)
    
    # Convertir a arrays
    for category in results:
        for model in results[category]:
            results[category][model] = np.array(results[category][model])
    
    # Analizar resultados
    print("\n" + "="*80)
    print("DISTRIBUCIÓN DE SCORES POR MODELO")
    print("="*80)
    
    print("\n📊 AASIST Base:")
    print(f"   Genuinos:  mean={results['genuine']['aasist_base'].mean():.3f}, std={results['genuine']['aasist_base'].std():.3f}")
    print(f"   TTS:       mean={results['tts']['aasist_base'].mean():.3f}, std={results['tts']['aasist_base'].std():.3f}")
    print(f"   Cloning:   mean={results['cloning']['aasist_base'].mean():.3f}, std={results['cloning']['aasist_base'].std():.3f}")
    
    print("\n📊 AASIST-L:")
    print(f"   Genuinos:  mean={results['genuine']['aasist_l'].mean():.3f}, std={results['genuine']['aasist_l'].std():.3f}")
    print(f"   TTS:       mean={results['tts']['aasist_l'].mean():.3f}, std={results['tts']['aasist_l'].std():.3f}")
    print(f"   Cloning:   mean={results['cloning']['aasist_l'].mean():.3f}, std={results['cloning']['aasist_l'].std():.3f}")
    
    print("\n📊 RawNet2:")
    print(f"   Genuinos:  mean={results['genuine']['rawnet2'].mean():.3f}, std={results['genuine']['rawnet2'].std():.3f}")
    print(f"   TTS:       mean={results['tts']['rawnet2'].mean():.3f}, std={results['tts']['rawnet2'].std():.3f}")
    print(f"   Cloning:   mean={results['cloning']['rawnet2'].mean():.3f}, std={results['cloning']['rawnet2'].std():.3f}")
    
    # Calcular métricas con diferentes configuraciones
    print("\n" + "="*80)
    print("MÉTRICAS POR MODELO (Threshold óptimo individual)")
    print("="*80)
    
    # Función auxiliar
    def calc_metrics(genuine, attacks, threshold):
        bpcer = (genuine > threshold).sum() / len(genuine) * 100
        apcer = (attacks < threshold).sum() / len(attacks) * 100
        acer = (bpcer + apcer) / 2
        detection = 100 - apcer
        return bpcer, apcer, acer, detection
    
    # Evaluar cada modelo solo
    configs = [
        ("AASIST Base solo", results['genuine']['aasist_base'], results['cloning']['aasist_base'], results['tts']['aasist_base']),
        ("AASIST-L solo", results['genuine']['aasist_l'], results['cloning']['aasist_l'], results['tts']['aasist_l']),
        ("RawNet2 solo", results['genuine']['rawnet2'], results['cloning']['rawnet2'], results['tts']['rawnet2']),
    ]
    
    best_results = []
    
    for name, genuine, cloning, tts in configs:
        # Buscar threshold óptimo
        best_acer = float('inf')
        best_threshold = 0
        best_metrics = None
        
        for t in np.arange(0.0, 1.0, 0.01):
            bpcer, apcer_c, _, det_c = calc_metrics(genuine, cloning, t)
            _, apcer_t, _, det_t = calc_metrics(genuine, tts, t)
            acer = (bpcer + apcer_c) / 2
            
            if acer < best_acer:
                best_acer = acer
                best_threshold = t
                best_metrics = (bpcer, apcer_c, apcer_t, det_c, det_t, acer)
        
        best_results.append((name, best_threshold, best_metrics))
        
        bpcer, apcer_c, apcer_t, det_c, det_t, acer = best_metrics
        print(f"\n{name}:")
        print(f"   Threshold óptimo: {best_threshold:.2f}")
        print(f"   BPCER: {bpcer:.2f}%")
        print(f"   APCER Cloning: {apcer_c:.2f}%  (Detección: {det_c:.2f}%)")
        print(f"   APCER TTS: {apcer_t:.2f}%  (Detección: {det_t:.2f}%)")
        print(f"   ACER: {acer:.2f}%")
    
    # Evaluar ensembles
    print("\n" + "="*80)
    print("MÉTRICAS DE ENSEMBLES (55% AASIST + 45% RawNet2)")
    print("="*80)
    
    # Ensemble AASIST base + RawNet2
    genuine_ensemble_base = 0.55 * results['genuine']['aasist_base'] + 0.45 * results['genuine']['rawnet2']
    cloning_ensemble_base = 0.55 * results['cloning']['aasist_base'] + 0.45 * results['cloning']['rawnet2']
    tts_ensemble_base = 0.55 * results['tts']['aasist_base'] + 0.45 * results['tts']['rawnet2']
    
    best_acer = float('inf')
    for t in np.arange(0.0, 1.0, 0.01):
        bpcer, apcer_c, _, det_c = calc_metrics(genuine_ensemble_base, cloning_ensemble_base, t)
        _, apcer_t, _, det_t = calc_metrics(genuine_ensemble_base, tts_ensemble_base, t)
        acer = (bpcer + apcer_c) / 2
        if acer < best_acer:
            best_acer = acer
            best_threshold_base = t
            best_metrics_base = (bpcer, apcer_c, apcer_t, det_c, det_t, acer)
    
    bpcer, apcer_c, apcer_t, det_c, det_t, acer = best_metrics_base
    print(f"\nEnsemble AASIST Base + RawNet2:")
    print(f"   Threshold óptimo: {best_threshold_base:.2f}")
    print(f"   BPCER: {bpcer:.2f}%")
    print(f"   APCER Cloning: {apcer_c:.2f}%  (Detección: {det_c:.2f}%)")
    print(f"   APCER TTS: {apcer_t:.2f}%  (Detección: {det_t:.2f}%)")
    print(f"   ACER: {acer:.2f}%")
    
    # Ensemble AASIST-L + RawNet2
    genuine_ensemble_l = 0.55 * results['genuine']['aasist_l'] + 0.45 * results['genuine']['rawnet2']
    cloning_ensemble_l = 0.55 * results['cloning']['aasist_l'] + 0.45 * results['cloning']['rawnet2']
    tts_ensemble_l = 0.55 * results['tts']['aasist_l'] + 0.45 * results['tts']['rawnet2']
    
    best_acer = float('inf')
    for t in np.arange(0.0, 1.0, 0.01):
        bpcer, apcer_c, _, det_c = calc_metrics(genuine_ensemble_l, cloning_ensemble_l, t)
        _, apcer_t, _, det_t = calc_metrics(genuine_ensemble_l, tts_ensemble_l, t)
        acer = (bpcer + apcer_c) / 2
        if acer < best_acer:
            best_acer = acer
            best_threshold_l = t
            best_metrics_l = (bpcer, apcer_c, apcer_t, det_c, det_t, acer)
    
    bpcer, apcer_c, apcer_t, det_c, det_t, acer = best_metrics_l
    print(f"\nEnsemble AASIST-L + RawNet2:")
    print(f"   Threshold óptimo: {best_threshold_l:.2f}")
    print(f"   BPCER: {bpcer:.2f}%")
    print(f"   APCER Cloning: {apcer_c:.2f}%  (Detección: {det_c:.2f}%)")
    print(f"   APCER TTS: {apcer_t:.2f}%  (Detección: {det_t:.2f}%)")
    print(f"   ACER: {acer:.2f}%")
    
    # Conclusión
    print("\n" + "="*80)
    print("CONCLUSIÓN")
    print("="*80)
    
    # Encontrar mejor configuración
    all_configs = best_results + [
        ("Ensemble AASIST Base + RawNet2", best_threshold_base, best_metrics_base),
        ("Ensemble AASIST-L + RawNet2", best_threshold_l, best_metrics_l)
    ]
    
    best_config = min(all_configs, key=lambda x: x[2][5])  # Mínimo ACER
    
    print(f"\n✅ MEJOR CONFIGURACIÓN: {best_config[0]}")
    print(f"   Threshold: {best_config[1]:.2f}")
    print(f"   ACER: {best_config[2][5]:.2f}%")
    print(f"   BPCER: {best_config[2][0]:.2f}%")
    print(f"   Detección Cloning: {best_config[2][3]:.2f}%")


if __name__ == "__main__":
    evaluate_individual_models()
