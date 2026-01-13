"""
Evaluar modelos anti-spoofing individualmente y en ensemble para determinar
cuál configuración produce las mejores métricas.

Modelos a evaluar:
- AASIST base
- AASIST-L
- RawNet2
- RawGAT-ST

Ensembles a evaluar:
- AASIST + RawNet2 (actual)
- AASIST-L + RawNet2
- AASIST-L + RawGAT-ST
- AASIST + RawGAT-ST
- Triple: AASIST-L + RawNet2 + RawGAT-ST
"""

import sys
from pathlib import Path
import numpy as np
import torch
import torchaudio
from tqdm import tqdm
import logging

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from infrastructure.biometrics.local_antispoof_models import (
    LocalAASISTModel,
    LocalRawNet2Model,
    LocalRawGATSTModel,
    build_local_model_paths
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_and_score_files(model, files, label):
    """Cargar y puntuar archivos con un modelo."""
    scores = []
    for audio_path in tqdm(files, desc=f"Processing {label}"):
        try:
            waveform, sr = torchaudio.load(audio_path)
            if waveform.ndim > 1:
                waveform = waveform.mean(dim=0)
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                waveform = resampler(waveform)
            
            score = model.predict_spoof_probability(waveform, 16000)
            if score is not None:
                scores.append(score)
        except Exception as e:
            logger.warning(f"Error processing {audio_path}: {e}")
            continue
    
    return np.array(scores)


def calculate_metrics(genuine_scores, attack_scores, threshold):
    """Calcular BPCER, APCER y detección."""
    bpcer = np.mean(genuine_scores >= threshold) * 100
    apcer = np.mean(attack_scores < threshold) * 100
    detection = 100 - apcer
    return bpcer, apcer, detection


def evaluate_model(model_name, model, dataset_dir):
    """Evaluar un modelo individual."""
    print(f"\n{'='*80}")
    print(f"EVALUANDO: {model_name}")
    print(f"{'='*80}")
    
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    print(f"Archivos: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning")
    
    # Score audios
    genuine_scores = load_and_score_files(model, genuine_files, "Genuine")
    tts_scores = load_and_score_files(model, tts_files, "TTS") if tts_files else np.array([])
    cloning_scores = load_and_score_files(model, cloning_files, "Cloning")
    
    print(f"\nDistribución de scores:")
    print(f"  Genuinos:  mean={genuine_scores.mean():.3f}, std={genuine_scores.std():.3f}")
    print(f"  Cloning:   mean={cloning_scores.mean():.3f}, std={cloning_scores.std():.3f}")
    if len(tts_scores) > 0:
        print(f"  TTS:       mean={tts_scores.mean():.3f}, std={tts_scores.std():.3f}")
    
    # Buscar threshold óptimo
    thresholds = np.arange(0.0, 1.01, 0.01)
    best_threshold = None
    best_acer = float('inf')
    
    for t in thresholds:
        bpcer, apcer_cloning, _ = calculate_metrics(genuine_scores, cloning_scores, t)
        if len(tts_scores) > 0:
            _, apcer_tts, _ = calculate_metrics(genuine_scores, tts_scores, t)
            apcer = (apcer_cloning + apcer_tts) / 2
        else:
            apcer = apcer_cloning
        
        acer = (bpcer + apcer) / 2
        
        if acer < best_acer:
            best_acer = acer
            best_threshold = t
    
    # Métricas con threshold óptimo
    bpcer, apcer_cloning, det_cloning = calculate_metrics(genuine_scores, cloning_scores, best_threshold)
    if len(tts_scores) > 0:
        _, apcer_tts, det_tts = calculate_metrics(genuine_scores, tts_scores, best_threshold)
    else:
        apcer_tts, det_tts = None, None
    
    print(f"\n✅ Threshold óptimo: {best_threshold:.2f}")
    print(f"   BPCER: {bpcer:.2f}%")
    print(f"   APCER Cloning: {apcer_cloning:.2f}% (Detección: {det_cloning:.2f}%)")
    if apcer_tts is not None:
        print(f"   APCER TTS: {apcer_tts:.2f}% (Detección: {det_tts:.2f}%)")
    print(f"   ACER: {best_acer:.2f}%")
    
    return {
        'model': model_name,
        'threshold': best_threshold,
        'bpcer': bpcer,
        'apcer_cloning': apcer_cloning,
        'apcer_tts': apcer_tts,
        'det_cloning': det_cloning,
        'det_tts': det_tts,
        'acer': best_acer,
        'genuine_scores': genuine_scores,
        'cloning_scores': cloning_scores,
        'tts_scores': tts_scores
    }


def evaluate_ensemble(name, models, weights, genuine_files, tts_files, cloning_files):
    """Evaluar un ensemble de modelos."""
    print(f"\n{'='*80}")
    print(f"EVALUANDO ENSEMBLE: {name}")
    print(f"{'='*80}")
    print(f"Pesos: {weights}")
    
    # Score audios con cada modelo
    all_genuine_scores = []
    all_cloning_scores = []
    all_tts_scores = []
    
    for model_name, model in models.items():
        print(f"\nProcesando con {model_name}...")
        genuine = load_and_score_files(model, genuine_files, f"Genuine ({model_name})")
        cloning = load_and_score_files(model, cloning_files, f"Cloning ({model_name})")
        tts = load_and_score_files(model, tts_files, f"TTS ({model_name})") if tts_files else np.array([])
        
        all_genuine_scores.append(genuine)
        all_cloning_scores.append(cloning)
        all_tts_scores.append(tts)
    
    # Calcular scores del ensemble
    genuine_ensemble = sum(w * scores for w, scores in zip(weights, all_genuine_scores))
    cloning_ensemble = sum(w * scores for w, scores in zip(weights, all_cloning_scores))
    tts_ensemble = sum(w * scores for w, scores in zip(weights, all_tts_scores)) if len(all_tts_scores[0]) > 0 else np.array([])
    
    print(f"\nDistribución de scores del ensemble:")
    print(f"  Genuinos:  mean={genuine_ensemble.mean():.3f}, std={genuine_ensemble.std():.3f}")
    print(f"  Cloning:   mean={cloning_ensemble.mean():.3f}, std={cloning_ensemble.std():.3f}")
    if len(tts_ensemble) > 0:
        print(f"  TTS:       mean={tts_ensemble.mean():.3f}, std={tts_ensemble.std():.3f}")
    
    # Buscar threshold óptimo
    thresholds = np.arange(0.0, 1.01, 0.01)
    best_threshold = None
    best_acer = float('inf')
    
    for t in thresholds:
        bpcer, apcer_cloning, _ = calculate_metrics(genuine_ensemble, cloning_ensemble, t)
        if len(tts_ensemble) > 0:
            _, apcer_tts, _ = calculate_metrics(genuine_ensemble, tts_ensemble, t)
            apcer = (apcer_cloning + apcer_tts) / 2
        else:
            apcer = apcer_cloning
        
        acer = (bpcer + apcer) / 2
        
        if acer < best_acer:
            best_acer = acer
            best_threshold = t
    
    # Métricas con threshold óptimo
    bpcer, apcer_cloning, det_cloning = calculate_metrics(genuine_ensemble, cloning_ensemble, best_threshold)
    if len(tts_ensemble) > 0:
        _, apcer_tts, det_tts = calculate_metrics(genuine_ensemble, tts_ensemble, best_threshold)
    else:
        apcer_tts, det_tts = None, None
    
    print(f"\n✅ Threshold óptimo: {best_threshold:.2f}")
    print(f"   BPCER: {bpcer:.2f}%")
    print(f"   APCER Cloning: {apcer_cloning:.2f}% (Detección: {det_cloning:.2f}%)")
    if apcer_tts is not None:
        print(f"   APCER TTS: {apcer_tts:.2f}% (Detección: {det_tts:.2f}%)")
    print(f"   ACER: {best_acer:.2f}%")
    
    return {
        'ensemble': name,
        'threshold': best_threshold,
        'bpcer': bpcer,
        'apcer_cloning': apcer_cloning,
        'apcer_tts': apcer_tts,
        'det_cloning': det_cloning,
        'det_tts': det_tts,
        'acer': best_acer
    }


def main():
    print("="*80)
    print("EVALUACIÓN COMPLETA DE MODELOS ANTI-SPOOFING")
    print("="*80)
    
    # Paths
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    device = torch.device("cpu")
    local_paths = build_local_model_paths()
    
    # Cargar modelos
    print("\n📦 Cargando modelos...")
    
    # Deshabilitar temporalmente AASIST-L para cargar AASIST base
    aasist_l_path = local_paths.aasist_dir / "AASIST-L.pth"
    aasist_l_backup = None
    if aasist_l_path.exists():
        aasist_l_backup = aasist_l_path.with_suffix('.pth.backup_eval')
        aasist_l_path.rename(aasist_l_backup)
    
    aasist_base = LocalAASISTModel(device, local_paths)
    
    # Restaurar AASIST-L
    if aasist_l_backup:
        aasist_l_backup.rename(aasist_l_path)
    
    aasist_l = LocalAASISTModel(device, local_paths)
    rawnet2 = LocalRawNet2Model(device, local_paths)
    rawgat_st = LocalRawGATSTModel(device, local_paths)
    
    print(f"   AASIST base: {'✅' if aasist_base.available else '❌'}")
    print(f"   AASIST-L: {'✅' if aasist_l.available else '❌'}")
    print(f"   RawNet2: {'✅' if rawnet2.available else '❌'}")
    print(f"   RawGAT-ST: {'✅' if rawgat_st.available else '❌'}")
    
    # Dataset files
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    # EVALUACIÓN INDIVIDUAL
    results = []
    
    if aasist_base.available:
        # Deshabilitar AASIST-L temporalmente
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        results.append(evaluate_model("AASIST Base", aasist_base, dataset_dir))
        if aasist_l_backup:
            aasist_l_backup.rename(aasist_l_path)
    
    if aasist_l.available:
        results.append(evaluate_model("AASIST-L", aasist_l, dataset_dir))
    
    if rawnet2.available:
        results.append(evaluate_model("RawNet2", rawnet2, dataset_dir))
    
    if rawgat_st.available:
        results.append(evaluate_model("RawGAT-ST", rawgat_st, dataset_dir))
    
    # EVALUACIÓN ENSEMBLES
    ensemble_results = []
    
    if aasist_base.available and rawnet2.available:
        # Deshabilitar AASIST-L
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        
        ensemble_results.append(evaluate_ensemble(
            "AASIST + RawNet2 (actual)",
            {'AASIST': aasist_base, 'RawNet2': rawnet2},
            [0.55, 0.45],
            genuine_files, tts_files, cloning_files
        ))
        
        if aasist_l_backup:
            aasist_l_backup.rename(aasist_l_path)
    
    if aasist_l.available and rawnet2.available:
        ensemble_results.append(evaluate_ensemble(
            "AASIST-L + RawNet2",
            {'AASIST-L': aasist_l, 'RawNet2': rawnet2},
            [0.55, 0.45],
            genuine_files, tts_files, cloning_files
        ))
    
    if aasist_l.available and rawgat_st.available:
        ensemble_results.append(evaluate_ensemble(
            "AASIST-L + RawGAT-ST",
            {'AASIST-L': aasist_l, 'RawGAT-ST': rawgat_st},
            [0.5, 0.5],
            genuine_files, tts_files, cloning_files
        ))
    
    if aasist_base.available and rawgat_st.available:
        # Deshabilitar AASIST-L
        if aasist_l_path.exists():
            aasist_l_path.rename(aasist_l_backup)
        
        ensemble_results.append(evaluate_ensemble(
            "AASIST + RawGAT-ST",
            {'AASIST': aasist_base, 'RawGAT-ST': rawgat_st},
            [0.5, 0.5],
            genuine_files, tts_files, cloning_files
        ))
        
        if aasist_l_backup:
            aasist_l_backup.rename(aasist_l_path)
    
    if aasist_l.available and rawnet2.available and rawgat_st.available:
        ensemble_results.append(evaluate_ensemble(
            "AASIST-L + RawNet2 + RawGAT-ST",
            {'AASIST-L': aasist_l, 'RawNet2': rawnet2, 'RawGAT-ST': rawgat_st},
            [0.4, 0.3, 0.3],
            genuine_files, tts_files, cloning_files
        ))
    
    # RESUMEN FINAL
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    
    print("\n📊 MODELOS INDIVIDUALES:")
    print(f"{'Modelo':<20} {'Thresh':<8} {'BPCER':<8} {'APCER_C':<10} {'Det_C':<8} {'ACER':<8}")
    print("-" * 80)
    for r in results:
        print(f"{r['model']:<20} {r['threshold']:<8.2f} {r['bpcer']:<8.2f} {r['apcer_cloning']:<10.2f} {r['det_cloning']:<8.2f} {r['acer']:<8.2f}")
    
    print("\n🔗 ENSEMBLES:")
    print(f"{'Ensemble':<35} {'Thresh':<8} {'BPCER':<8} {'APCER_C':<10} {'Det_C':<8} {'ACER':<8}")
    print("-" * 80)
    for r in ensemble_results:
        print(f"{r['ensemble']:<35} {r['threshold']:<8.2f} {r['bpcer']:<8.2f} {r['apcer_cloning']:<10.2f} {r['det_cloning']:<8.2f} {r['acer']:<8.2f}")
    
    # Mejor configuración
    all_configs = results + ensemble_results
    best = min(all_configs, key=lambda x: x.get('acer', float('inf')))
    
    print("\n" + "="*80)
    print("🏆 MEJOR CONFIGURACIÓN")
    print("="*80)
    print(f"Modelo/Ensemble: {best.get('model') or best.get('ensemble')}")
    print(f"Threshold: {best['threshold']:.2f}")
    print(f"BPCER: {best['bpcer']:.2f}%")
    print(f"APCER Cloning: {best['apcer_cloning']:.2f}% (Detección: {best['det_cloning']:.2f}%)")
    if best['apcer_tts'] is not None:
        print(f"APCER TTS: {best['apcer_tts']:.2f}% (Detección: {best['det_tts']:.2f}%)")
    print(f"ACER: {best['acer']:.2f}%")
    
    print("\n✅ Evaluación completa finalizada")


if __name__ == "__main__":
    main()
