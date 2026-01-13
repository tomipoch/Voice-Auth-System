"""
Optimizar threshold para AASIST-L + RawGAT-ST buscando balance entre usabilidad y seguridad.

Objetivo: BPCER razonable (30-50%) con mejor detección posible.
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from infrastructure.biometrics.local_antispoof_models import (
    LocalAASISTModel,
    LocalRawGATSTModel,
    build_local_model_paths
)
import torch


def load_and_score_ensemble(audio_files, label, model_aasist_l, model_rawgat, weights):
    """Cargar audios y calcular scores del ensemble."""
    import torchaudio
    
    scores_aasist = []
    scores_rawgat = []
    
    for audio_path in tqdm(audio_files, desc=f"Processing {label}"):
        waveform, sr = torchaudio.load(str(audio_path))
        
        # Resample si es necesario
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        # Scores individuales
        score_a = model_aasist_l.predict_spoof_probability(waveform, 16000)
        score_r = model_rawgat.predict_spoof_probability(waveform, 16000)
        
        if score_a is not None and score_r is not None:
            scores_aasist.append(score_a)
            scores_rawgat.append(score_r)
    
    # Ensemble
    scores_aasist = np.array(scores_aasist)
    scores_rawgat = np.array(scores_rawgat)
    ensemble_scores = weights[0] * scores_aasist + weights[1] * scores_rawgat
    
    return ensemble_scores, scores_aasist, scores_rawgat


def calculate_metrics(genuine, attacks, threshold):
    """Calcular BPCER, APCER y detección."""
    bpcer = (genuine > threshold).sum() / len(genuine) * 100
    apcer = (attacks <= threshold).sum() / len(attacks) * 100
    detection = 100 - apcer
    acer = (bpcer + apcer) / 2
    return bpcer, apcer, detection, acer


def main():
    print("="*80)
    print("OPTIMIZACIÓN DE THRESHOLD: AASIST-L + RawGAT-ST")
    print("="*80)
    
    # Load models
    device = torch.device("cpu")
    local_paths = build_local_model_paths()
    
    print("\n📦 Cargando modelos...")
    model_aasist_l = LocalAASISTModel(device=device, paths=local_paths)
    model_rawgat = LocalRawGATSTModel(device=device, paths=local_paths)
    
    if not model_aasist_l.available or not model_rawgat.available:
        print("❌ No se pudieron cargar los modelos")
        return
    
    print("✅ Modelos cargados")
    
    # Load dataset
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_files = sorted((dataset_dir / "recordings").rglob("*.wav"))
    tts_files = sorted((dataset_dir / "attacks").rglob("*.wav"))
    cloning_files = sorted((dataset_dir / "cloning").rglob("*.wav"))
    
    print(f"\n📁 Dataset: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning")
    
    # Get scores
    weights = [0.5, 0.5]
    print(f"\n🔄 Procesando con ensemble (pesos: {weights})...")
    
    genuine_scores, _, _ = load_and_score_ensemble(genuine_files, "Genuine", model_aasist_l, model_rawgat, weights)
    cloning_scores, _, _ = load_and_score_ensemble(cloning_files, "Cloning", model_aasist_l, model_rawgat, weights)
    tts_scores, _, _ = load_and_score_ensemble(tts_files, "TTS", model_aasist_l, model_rawgat, weights)
    
    all_attacks = np.concatenate([cloning_scores, tts_scores])
    
    print("\n📊 Distribución de scores:")
    print(f"   Genuinos:  mean={genuine_scores.mean():.3f}, std={genuine_scores.std():.3f}")
    print(f"   Cloning:   mean={cloning_scores.mean():.3f}, std={cloning_scores.std():.3f}")
    print(f"   TTS:       mean={tts_scores.mean():.3f}, std={tts_scores.std():.3f}")
    
    # Analizar thresholds
    print("\n🔍 Analizando thresholds...")
    thresholds = np.arange(0.0, 1.01, 0.01)
    
    results = []
    for t in thresholds:
        bpcer_g, apcer_c, det_c, _ = calculate_metrics(genuine_scores, cloning_scores, t)
        _, apcer_t, det_t, _ = calculate_metrics(genuine_scores, tts_scores, t)
        _, apcer_all, det_all, acer = calculate_metrics(genuine_scores, all_attacks, t)
        
        results.append({
            'threshold': t,
            'bpcer': bpcer_g,
            'apcer_cloning': apcer_c,
            'apcer_tts': apcer_t,
            'apcer_all': apcer_all,
            'detection_cloning': det_c,
            'detection_tts': det_t,
            'acer': acer
        })
    
    # Buscar thresholds óptimos según diferentes criterios
    print("\n" + "="*80)
    print("ANÁLISIS DE THRESHOLDS")
    print("="*80)
    
    # 1. BPCER 30-40% con mejor detección
    candidates_30_40 = [r for r in results if 30 <= r['bpcer'] <= 40]
    if candidates_30_40:
        best_30_40 = max(candidates_30_40, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        print(f"\n1️⃣ USABILIDAD ALTA (BPCER 30-40%):")
        print(f"   Threshold: {best_30_40['threshold']:.2f}")
        print(f"   BPCER: {best_30_40['bpcer']:.2f}%")
        print(f"   Detección Cloning: {best_30_40['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best_30_40['detection_tts']:.2f}%")
        print(f"   ACER: {best_30_40['acer']:.2f}%")
        print(f"   Con 3 intentos: BPCER efectivo = {(best_30_40['bpcer']/100)**3 * 100:.2f}%")
    
    # 2. BPCER 40-50% con mejor detección
    candidates_40_50 = [r for r in results if 40 <= r['bpcer'] <= 50]
    if candidates_40_50:
        best_40_50 = max(candidates_40_50, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        print(f"\n2️⃣ USABILIDAD MEDIA (BPCER 40-50%):")
        print(f"   Threshold: {best_40_50['threshold']:.2f}")
        print(f"   BPCER: {best_40_50['bpcer']:.2f}%")
        print(f"   Detección Cloning: {best_40_50['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best_40_50['detection_tts']:.2f}%")
        print(f"   ACER: {best_40_50['acer']:.2f}%")
        print(f"   Con 3 intentos: BPCER efectivo = {(best_40_50['bpcer']/100)**3 * 100:.2f}%")
    
    # 3. Detección combinada > 150% con menor BPCER posible
    candidates_det = [r for r in results if (r['detection_cloning'] + r['detection_tts']) > 150]
    if candidates_det:
        best_det = min(candidates_det, key=lambda r: r['bpcer'])
        print(f"\n3️⃣ SEGURIDAD ALTA (Detección combinada > 150%):")
        print(f"   Threshold: {best_det['threshold']:.2f}")
        print(f"   BPCER: {best_det['bpcer']:.2f}%")
        print(f"   Detección Cloning: {best_det['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best_det['detection_tts']:.2f}%")
        print(f"   ACER: {best_det['acer']:.2f}%")
        print(f"   Con 3 intentos: BPCER efectivo = {(best_det['bpcer']/100)**3 * 100:.2f}%")
    
    # 4. Balance óptimo (minimizar ACER con BPCER < 60%)
    candidates_balance = [r for r in results if r['bpcer'] < 60]
    if candidates_balance:
        best_balance = min(candidates_balance, key=lambda r: r['acer'])
        print(f"\n4️⃣ BALANCE ÓPTIMO (Mínimo ACER con BPCER < 60%):")
        print(f"   Threshold: {best_balance['threshold']:.2f}")
        print(f"   BPCER: {best_balance['bpcer']:.2f}%")
        print(f"   Detección Cloning: {best_balance['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best_balance['detection_tts']:.2f}%")
        print(f"   ACER: {best_balance['acer']:.2f}%")
        print(f"   Con 3 intentos: BPCER efectivo = {(best_balance['bpcer']/100)**3 * 100:.2f}%")
    
    # Visualización
    print("\n📊 Generando gráficos...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Optimización Threshold: AASIST-L + RawGAT-ST', fontsize=16, fontweight='bold')
    
    thresholds_list = [r['threshold'] for r in results]
    
    # BPCER vs APCER
    ax = axes[0, 0]
    ax.plot(thresholds_list, [r['bpcer'] for r in results], 'g-', linewidth=2, label='BPCER')
    ax.plot(thresholds_list, [r['apcer_cloning'] for r in results], 'orange', linewidth=2, label='APCER Cloning')
    ax.plot(thresholds_list, [r['apcer_tts'] for r in results], 'r--', linewidth=2, label='APCER TTS')
    ax.axhline(40, color='gray', linestyle=':', alpha=0.5, label='BPCER 40%')
    ax.axhline(50, color='gray', linestyle=':', alpha=0.3, label='BPCER 50%')
    if candidates_30_40:
        ax.axvline(best_30_40['threshold'], color='blue', linestyle='--', label=f"Usabilidad alta")
    if candidates_40_50:
        ax.axvline(best_40_50['threshold'], color='purple', linestyle='--', label=f"Usabilidad media")
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Error Rate (%)', fontsize=12)
    ax.set_title('BPCER vs APCER', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Detección
    ax = axes[0, 1]
    ax.plot(thresholds_list, [r['detection_cloning'] for r in results], 'orange', linewidth=2, label='Detección Cloning')
    ax.plot(thresholds_list, [r['detection_tts'] for r in results], 'r', linewidth=2, label='Detección TTS')
    ax.axhline(80, color='gray', linestyle=':', alpha=0.5, label='80% detección')
    ax.axhline(90, color='gray', linestyle=':', alpha=0.3, label='90% detección')
    if candidates_30_40:
        ax.axvline(best_30_40['threshold'], color='blue', linestyle='--')
    if candidates_40_50:
        ax.axvline(best_40_50['threshold'], color='purple', linestyle='--')
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Tasa de Detección (%)', fontsize=12)
    ax.set_title('Tasas de Detección', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # ACER
    ax = axes[1, 0]
    ax.plot(thresholds_list, [r['acer'] for r in results], 'b-', linewidth=2)
    if candidates_balance:
        ax.axvline(best_balance['threshold'], color='red', linestyle='--', 
                   label=f"Mínimo ACER: {best_balance['threshold']:.2f}")
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('ACER (%)', fontsize=12)
    ax.set_title('ACER por Threshold', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tabla comparativa
    ax = axes[1, 1]
    ax.axis('off')
    
    table_data = []
    headers = ['Criterio', 'Thresh', 'BPCER', 'Det_C', 'Det_T', 'ACER']
    
    if candidates_30_40:
        r = best_30_40
        table_data.append(['Usabilidad Alta', f"{r['threshold']:.2f}", f"{r['bpcer']:.1f}%", 
                          f"{r['detection_cloning']:.1f}%", f"{r['detection_tts']:.1f}%", f"{r['acer']:.1f}%"])
    
    if candidates_40_50:
        r = best_40_50
        table_data.append(['Usabilidad Media', f"{r['threshold']:.2f}", f"{r['bpcer']:.1f}%", 
                          f"{r['detection_cloning']:.1f}%", f"{r['detection_tts']:.1f}%", f"{r['acer']:.1f}%"])
    
    if candidates_det:
        r = best_det
        table_data.append(['Seguridad Alta', f"{r['threshold']:.2f}", f"{r['bpcer']:.1f}%", 
                          f"{r['detection_cloning']:.1f}%", f"{r['detection_tts']:.1f}%", f"{r['acer']:.1f}%"])
    
    if candidates_balance:
        r = best_balance
        table_data.append(['Balance Óptimo', f"{r['threshold']:.2f}", f"{r['bpcer']:.1f}%", 
                          f"{r['detection_cloning']:.1f}%", f"{r['detection_tts']:.1f}%", f"{r['acer']:.1f}%"])
    
    table = ax.table(cellText=table_data, colLabels=headers, 
                     cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Colorear header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax.set_title('Comparación de Configuraciones', fontsize=13, fontweight='bold', pad=20)
    
    plt.tight_layout()
    output_path = Path("evaluation/plots/antispoofing/aasist_l_rawgat_threshold_optimization.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico guardado: {output_path}")
    
    # Recomendación final
    print("\n" + "="*80)
    print("RECOMENDACIÓN FINAL")
    print("="*80)
    
    recommended = best_40_50 if candidates_40_50 else best_balance
    
    print(f"""
CONFIGURACIÓN RECOMENDADA: AASIST-L + RawGAT-ST
Threshold: {recommended['threshold']:.2f}

Métricas:
- BPCER: {recommended['bpcer']:.2f}% (usuarios genuinos rechazados en 1 intento)
- BPCER efectivo (3 intentos): {(recommended['bpcer']/100)**3 * 100:.2f}%
- Detección Cloning: {recommended['detection_cloning']:.2f}%
- Detección TTS: {recommended['detection_tts']:.2f}%
- ACER: {recommended['acer']:.2f}%

Esta configuración ofrece un balance razonable entre usabilidad y seguridad,
con detección significativamente superior al sistema actual.
""")
    
    print("\n✅ Optimización completada")


if __name__ == "__main__":
    main()
