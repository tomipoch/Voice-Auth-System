"""
Optimizar threshold para RawGAT-ST solo, buscando BPCER razonable (30-50%).
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from infrastructure.biometrics.local_antispoof_models import (
    LocalRawGATSTModel,
    build_local_model_paths
)
import torch


def load_and_score(audio_files, label, model):
    """Cargar audios y calcular scores."""
    import torchaudio
    
    scores = []
    
    for audio_path in tqdm(audio_files, desc=f"Processing {label}"):
        waveform, sr = torchaudio.load(str(audio_path))
        
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        
        score = model.predict_spoof_probability(waveform, 16000)
        if score is not None:
            scores.append(score)
    
    return np.array(scores)


def calculate_metrics(genuine, attacks, threshold):
    """Calcular métricas."""
    bpcer = (genuine > threshold).sum() / len(genuine) * 100
    apcer = (attacks <= threshold).sum() / len(attacks) * 100
    detection = 100 - apcer
    acer = (bpcer + apcer) / 2
    return bpcer, apcer, detection, acer


def main():
    print("="*80)
    print("OPTIMIZACIÓN DE THRESHOLD: RawGAT-ST (SOLO)")
    print("="*80)
    
    # Load model
    device = torch.device("cpu")
    local_paths = build_local_model_paths()
    
    print("\n📦 Cargando RawGAT-ST...")
    model = LocalRawGATSTModel(device=device, paths=local_paths)
    
    if not model.available:
        print("❌ No se pudo cargar RawGAT-ST")
        return
    
    print("✅ RawGAT-ST cargado")
    
    # Load dataset
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_files = sorted((dataset_dir / "recordings").rglob("*.wav"))
    tts_files = sorted((dataset_dir / "attacks").rglob("*.wav"))
    cloning_files = sorted((dataset_dir / "cloning").rglob("*.wav"))
    
    print(f"\n📁 Dataset: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning")
    
    # Get scores
    print("\n🔄 Procesando audios...")
    genuine_scores = load_and_score(genuine_files, "Genuine", model)
    cloning_scores = load_and_score(cloning_files, "Cloning", model)
    tts_scores = load_and_score(tts_files, "TTS", model)
    
    all_attacks = np.concatenate([cloning_scores, tts_scores])
    
    print("\n📊 Distribución de scores:")
    print(f"   Genuinos:  mean={genuine_scores.mean():.3f}, std={genuine_scores.std():.3f}, min={genuine_scores.min():.3f}, max={genuine_scores.max():.3f}")
    print(f"   Cloning:   mean={cloning_scores.mean():.3f}, std={cloning_scores.std():.3f}, min={cloning_scores.min():.3f}, max={cloning_scores.max():.3f}")
    print(f"   TTS:       mean={tts_scores.mean():.3f}, std={tts_scores.std():.3f}, min={tts_scores.min():.3f}, max={tts_scores.max():.3f}")
    
    # Analizar thresholds
    print("\n🔍 Analizando thresholds de 0.0 a 1.0...")
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
    
    # Buscar configuraciones óptimas
    print("\n" + "="*80)
    print("CONFIGURACIONES ÓPTIMAS PARA DIFERENTES OBJETIVOS")
    print("="*80)
    
    configs = []
    
    # 1. BPCER 30-40%
    candidates_30_40 = [r for r in results if 30 <= r['bpcer'] <= 40]
    if candidates_30_40:
        best = max(candidates_30_40, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        configs.append(('Usabilidad Alta', best))
        print(f"\n1️⃣ USABILIDAD ALTA (BPCER 30-40%):")
        print(f"   Threshold: {best['threshold']:.2f}")
        print(f"   BPCER: {best['bpcer']:.2f}%")
        print(f"   BPCER efectivo (3 intentos): {(best['bpcer']/100)**3 * 100:.2f}%")
        print(f"   Detección Cloning: {best['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best['detection_tts']:.2f}%")
        print(f"   ACER: {best['acer']:.2f}%")
    
    # 2. BPCER 40-50%
    candidates_40_50 = [r for r in results if 40 <= r['bpcer'] <= 50]
    if candidates_40_50:
        best = max(candidates_40_50, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        configs.append(('Usabilidad Media', best))
        print(f"\n2️⃣ USABILIDAD MEDIA (BPCER 40-50%):")
        print(f"   Threshold: {best['threshold']:.2f}")
        print(f"   BPCER: {best['bpcer']:.2f}%")
        print(f"   BPCER efectivo (3 intentos): {(best['bpcer']/100)**3 * 100:.2f}%")
        print(f"   Detección Cloning: {best['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best['detection_tts']:.2f}%")
        print(f"   ACER: {best['acer']:.2f}%")
    
    # 3. BPCER 50-60%
    candidates_50_60 = [r for r in results if 50 <= r['bpcer'] <= 60]
    if candidates_50_60:
        best = max(candidates_50_60, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        configs.append(('Balance', best))
        print(f"\n3️⃣ BALANCE (BPCER 50-60%):")
        print(f"   Threshold: {best['threshold']:.2f}")
        print(f"   BPCER: {best['bpcer']:.2f}%")
        print(f"   BPCER efectivo (3 intentos): {(best['bpcer']/100)**3 * 100:.2f}%")
        print(f"   Detección Cloning: {best['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best['detection_tts']:.2f}%")
        print(f"   ACER: {best['acer']:.2f}%")
    
    # 4. Máxima detección con BPCER < 70%
    candidates_det = [r for r in results if r['bpcer'] < 70]
    if candidates_det:
        best = max(candidates_det, key=lambda r: r['detection_cloning'] + r['detection_tts'])
        configs.append(('Máxima Detección', best))
        print(f"\n4️⃣ MÁXIMA DETECCIÓN (BPCER < 70%):")
        print(f"   Threshold: {best['threshold']:.2f}")
        print(f"   BPCER: {best['bpcer']:.2f}%")
        print(f"   BPCER efectivo (3 intentos): {(best['bpcer']/100)**3 * 100:.2f}%")
        print(f"   Detección Cloning: {best['detection_cloning']:.2f}%")
        print(f"   Detección TTS: {best['detection_tts']:.2f}%")
        print(f"   ACER: {best['acer']:.2f}%")
    
    # Visualización
    print("\n📊 Generando gráficos...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Optimización Threshold: RawGAT-ST (Solo)', fontsize=16, fontweight='bold')
    
    thresholds_list = [r['threshold'] for r in results]
    colors = ['blue', 'purple', 'green', 'red']
    
    # BPCER vs APCER
    ax = axes[0, 0]
    ax.plot(thresholds_list, [r['bpcer'] for r in results], 'g-', linewidth=2, label='BPCER')
    ax.plot(thresholds_list, [r['apcer_cloning'] for r in results], 'orange', linewidth=2, label='APCER Cloning')
    ax.plot(thresholds_list, [r['apcer_tts'] for r in results], 'r--', linewidth=2, label='APCER TTS')
    for i, (name, config) in enumerate(configs):
        ax.axvline(config['threshold'], color=colors[i], linestyle='--', alpha=0.7, label=name)
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Error Rate (%)', fontsize=12)
    ax.set_title('BPCER vs APCER', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Detección
    ax = axes[0, 1]
    ax.plot(thresholds_list, [r['detection_cloning'] for r in results], 'orange', linewidth=2, label='Detección Cloning')
    ax.plot(thresholds_list, [r['detection_tts'] for r in results], 'r', linewidth=2, label='Detección TTS')
    ax.axhline(80, color='gray', linestyle=':', alpha=0.5, label='80%')
    ax.axhline(90, color='gray', linestyle=':', alpha=0.3, label='90%')
    for i, (name, config) in enumerate(configs):
        ax.axvline(config['threshold'], color=colors[i], linestyle='--', alpha=0.7)
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Tasa de Detección (%)', fontsize=12)
    ax.set_title('Tasas de Detección', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # ACER
    ax = axes[1, 0]
    ax.plot(thresholds_list, [r['acer'] for r in results], 'b-', linewidth=2)
    for i, (name, config) in enumerate(configs):
        ax.axvline(config['threshold'], color=colors[i], linestyle='--', alpha=0.7, label=name)
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('ACER (%)', fontsize=12)
    ax.set_title('ACER por Threshold', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Tabla comparativa
    ax = axes[1, 1]
    ax.axis('off')
    
    table_data = []
    headers = ['Configuración', 'Thresh', 'BPCER', 'BPCER_3x', 'Det_C', 'Det_T', 'ACER']
    
    for name, config in configs:
        bpcer_3x = (config['bpcer']/100)**3 * 100
        table_data.append([
            name, 
            f"{config['threshold']:.2f}", 
            f"{config['bpcer']:.1f}%",
            f"{bpcer_3x:.2f}%",
            f"{config['detection_cloning']:.1f}%", 
            f"{config['detection_tts']:.1f}%", 
            f"{config['acer']:.1f}%"
        ])
    
    table = ax.table(cellText=table_data, colLabels=headers, 
                     cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2.5)
    
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax.set_title('Comparación de Configuraciones', fontsize=13, fontweight='bold', pad=20)
    
    plt.tight_layout()
    output_path = Path("evaluation/plots/antispoofing/rawgat_st_threshold_optimization.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico guardado: {output_path}")
    
    # Recomendación final
    print("\n" + "="*80)
    print("RECOMENDACIÓN FINAL")
    print("="*80)
    
    # Elegir la configuración con BPCER 40-50% si existe, sino la más cercana
    recommended = None
    if candidates_40_50:
        recommended = max(candidates_40_50, key=lambda r: r['detection_cloning'] + r['detection_tts'])
    elif candidates_30_40:
        recommended = max(candidates_30_40, key=lambda r: r['detection_cloning'] + r['detection_tts'])
    elif candidates_50_60:
        recommended = max(candidates_50_60, key=lambda r: r['detection_cloning'] + r['detection_tts'])
    
    if recommended:
        bpcer_3x = (recommended['bpcer']/100)**3 * 100
        
        print(f"""
CONFIGURACIÓN RECOMENDADA: RawGAT-ST (SOLO)
Threshold: {recommended['threshold']:.2f}

Métricas por intento:
- BPCER: {recommended['bpcer']:.2f}% (usuarios genuinos rechazados)
- Detección Cloning: {recommended['detection_cloning']:.2f}%
- Detección TTS: {recommended['detection_tts']:.2f}%
- ACER: {recommended['acer']:.2f}%

Con 3 intentos permitidos:
- BPCER efectivo: {bpcer_3x:.2f}%
- Experiencia: {100-bpcer_3x:.2f}% usuarios genuinos pasan en ≤3 intentos

Comparación vs sistema actual (AASIST + RawNet2):
- Detección Cloning: {recommended['detection_cloning']:.1f}% vs 21.6% (+{recommended['detection_cloning']-21.6:.1f}%)
- Detección TTS: {recommended['detection_tts']:.1f}% vs 0.0% (+{recommended['detection_tts']:.1f}%)
- BPCER (1 intento): {recommended['bpcer']:.1f}% vs 2.0% ({recommended['bpcer']-2.0:+.1f}%)
- BPCER (3 intentos): {bpcer_3x:.2f}% vs 0.01%

VENTAJAS:
✅ Detección TTS mejorada significativamente (de 0% a {recommended['detection_tts']:.1f}%)
✅ Detección Cloning mejorada (de 21.6% a {recommended['detection_cloning']:.1f}%)
✅ Modelo único = más simple, más rápido

TRADE-OFF:
⚠️  Mayor BPCER que sistema actual, pero manejable con reintentos
⚠️  Usuarios genuinos necesitarán 1-2 intentos en promedio
""")
    
    print("\n✅ Análisis completado")


if __name__ == "__main__":
    main()
