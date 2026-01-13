"""
Encontrar el threshold óptimo para AASIST-L analizando todas las métricas.
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))
sys.path.insert(0, str(backend_dir / "evaluation"))

from scripts.analyze_antispoofing_corrected import CorrectedAntiSpoofingAnalyzer


def find_optimal_threshold():
    """Encontrar el threshold óptimo para AASIST-L."""
    
    print("="*80)
    print("BÚSQUEDA DE THRESHOLD ÓPTIMO PARA AASIST-L")
    print("="*80)
    
    # Dataset paths
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    # Load analyzer
    analyzer = CorrectedAntiSpoofingAnalyzer(model_name="ensemble_antispoofing")
    
    # Load scores
    print("\n📊 Cargando scores con AASIST-L...")
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    genuine_scores, _ = analyzer.load_and_score_audios(genuine_files, "genuine")
    tts_scores = []
    if tts_files:
        tts_scores, _ = analyzer.load_and_score_audios(tts_files, "tts")
    cloning_scores, _ = analyzer.load_and_score_audios(cloning_files, "cloning")
    
    genuine_scores = np.array(genuine_scores)
    tts_scores = np.array(tts_scores) if len(tts_scores) > 0 else np.array([])
    cloning_scores = np.array(cloning_scores)
    
    # Estadísticas de scores
    print("\n📈 Distribución de scores con AASIST-L:")
    print(f"   Genuinos:  mean={genuine_scores.mean():.3f}, std={genuine_scores.std():.3f}, "
          f"min={genuine_scores.min():.3f}, max={genuine_scores.max():.3f}")
    print(f"   Cloning:   mean={cloning_scores.mean():.3f}, std={cloning_scores.std():.3f}, "
          f"min={cloning_scores.min():.3f}, max={cloning_scores.max():.3f}")
    if len(tts_scores) > 0:
        print(f"   TTS:       mean={tts_scores.mean():.3f}, std={tts_scores.std():.3f}, "
              f"min={tts_scores.min():.3f}, max={tts_scores.max():.3f}")
    
    # Analizar thresholds
    print("\n🔍 Analizando thresholds de 0.0 a 1.0...")
    thresholds = np.arange(0.0, 1.01, 0.01)
    
    results = []
    for t in thresholds:
        bpcer = analyzer.calculate_bpcer(genuine_scores, t)
        apcer_cloning = analyzer.calculate_apcer(cloning_scores, t)
        
        if len(tts_scores) > 0:
            apcer_tts = analyzer.calculate_apcer(tts_scores, t)
            all_attacks = np.concatenate([tts_scores, cloning_scores])
            apcer_all = analyzer.calculate_apcer(all_attacks, t)
        else:
            apcer_tts = 0
            apcer_all = apcer_cloning
        
        acer = analyzer.calculate_acer(bpcer, apcer_all)
        
        results.append({
            'threshold': t,
            'bpcer': bpcer,
            'apcer_cloning': apcer_cloning,
            'apcer_tts': apcer_tts,
            'apcer_all': apcer_all,
            'acer': acer,
            'detection_cloning': 100 - apcer_cloning,
            'detection_tts': 100 - apcer_tts
        })
    
    # Encontrar thresholds óptimos según diferentes criterios
    print("\n" + "="*80)
    print("THRESHOLDS ÓPTIMOS SEGÚN DIFERENTES CRITERIOS")
    print("="*80)
    
    # 1. Mínimo ACER
    min_acer_idx = min(range(len(results)), key=lambda i: results[i]['acer'])
    min_acer = results[min_acer_idx]
    
    print(f"\n1️⃣  MÍNIMO ACER (Error promedio mínimo):")
    print(f"   Threshold: {min_acer['threshold']:.2f}")
    print(f"   ACER: {min_acer['acer']:.2f}%")
    print(f"   BPCER: {min_acer['bpcer']:.2f}%")
    print(f"   APCER Cloning: {min_acer['apcer_cloning']:.2f}%")
    print(f"   APCER TTS: {min_acer['apcer_tts']:.2f}%")
    
    # 2. BPCER < 50% con mejor detección de cloning
    candidates_50 = [r for r in results if r['bpcer'] < 50]
    if candidates_50:
        best_50 = min(candidates_50, key=lambda r: r['apcer_cloning'])
        print(f"\n2️⃣  MEJOR BALANCE (BPCER < 50%):")
        print(f"   Threshold: {best_50['threshold']:.2f}")
        print(f"   BPCER: {best_50['bpcer']:.2f}%")
        print(f"   APCER Cloning: {best_50['apcer_cloning']:.2f}%")
        print(f"   Detección Cloning: {best_50['detection_cloning']:.2f}%")
        print(f"   ACER: {best_50['acer']:.2f}%")
    
    # 3. Detección de cloning > 50%
    candidates_det = [r for r in results if r['detection_cloning'] > 50]
    if candidates_det:
        best_det = min(candidates_det, key=lambda r: r['bpcer'])
        print(f"\n3️⃣  MEJOR DETECCIÓN CLONING (> 50%):")
        print(f"   Threshold: {best_det['threshold']:.2f}")
        print(f"   Detección Cloning: {best_det['detection_cloning']:.2f}%")
        print(f"   BPCER: {best_det['bpcer']:.2f}%")
        print(f"   APCER Cloning: {best_det['apcer_cloning']:.2f}%")
        print(f"   ACER: {best_det['acer']:.2f}%")
    
    # 4. Balance pragmático (BPCER ~40%, mejor cloning posible)
    candidates_40 = [r for r in results if 35 <= r['bpcer'] <= 45]
    if candidates_40:
        best_40 = min(candidates_40, key=lambda r: r['apcer_cloning'])
        print(f"\n4️⃣  BALANCE PRAGMÁTICO (BPCER ~40%):")
        print(f"   Threshold: {best_40['threshold']:.2f}")
        print(f"   BPCER: {best_40['bpcer']:.2f}%")
        print(f"   APCER Cloning: {best_40['apcer_cloning']:.2f}%")
        print(f"   Detección Cloning: {best_40['detection_cloning']:.2f}%")
        print(f"   ACER: {best_40['acer']:.2f}%")
    
    # Visualización
    print("\n📊 Generando gráfico de análisis...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Análisis de Threshold para AASIST-L', fontsize=16, fontweight='bold')
    
    thresholds_list = [r['threshold'] for r in results]
    
    # BPCER vs APCER
    ax = axes[0, 0]
    ax.plot(thresholds_list, [r['bpcer'] for r in results], 'g-', linewidth=2, label='BPCER')
    ax.plot(thresholds_list, [r['apcer_cloning'] for r in results], 'orange', linewidth=2, label='APCER Cloning')
    ax.plot(thresholds_list, [r['apcer_tts'] for r in results], 'r--', linewidth=1.5, label='APCER TTS')
    ax.axvline(min_acer['threshold'], color='purple', linestyle='--', label=f"Óptimo ACER ({min_acer['threshold']:.2f})")
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Error Rate (%)', fontsize=12)
    ax.set_title('BPCER vs APCER', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # ACER
    ax = axes[0, 1]
    ax.plot(thresholds_list, [r['acer'] for r in results], 'b-', linewidth=2)
    ax.axvline(min_acer['threshold'], color='red', linestyle='--', 
               label=f"Mínimo: {min_acer['threshold']:.2f}")
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('ACER (%)', fontsize=12)
    ax.set_title('ACER por Threshold', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Detección
    ax = axes[1, 0]
    ax.plot(thresholds_list, [r['detection_cloning'] for r in results], 'orange', linewidth=2, label='Detección Cloning')
    ax.plot(thresholds_list, [r['detection_tts'] for r in results], 'r--', linewidth=1.5, label='Detección TTS')
    ax.axhline(50, color='gray', linestyle=':', label='50% detección')
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Tasa de Detección (%)', fontsize=12)
    ax.set_title('Tasa de Detección de Ataques', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Trade-off
    ax = axes[1, 1]
    ax.plot([r['bpcer'] for r in results], [r['apcer_cloning'] for r in results], 
            'purple', linewidth=2, label='Frontera Pareto')
    ax.scatter([min_acer['bpcer']], [min_acer['apcer_cloning']], 
               s=200, c='red', marker='*', label=f"Óptimo ACER", zorder=5)
    if candidates_40:
        ax.scatter([best_40['bpcer']], [best_40['apcer_cloning']], 
                   s=150, c='green', marker='o', label=f"Pragmático", zorder=5)
    ax.plot([0, 100], [100, 0], 'gray', linestyle='--', alpha=0.5, label='Random')
    ax.set_xlabel('BPCER (%)', fontsize=12)
    ax.set_ylabel('APCER Cloning (%)', fontsize=12)
    ax.set_title('Trade-off BPCER vs APCER', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path("evaluation/plots/antispoofing/aasist_l/threshold_analysis.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico guardado: {output_path}")
    
    # Recomendación final
    print("\n" + "="*80)
    print("RECOMENDACIÓN FINAL")
    print("="*80)
    
    recommended = best_40 if candidates_40 else min_acer
    
    print(f"""
THRESHOLD RECOMENDADO: {recommended['threshold']:.2f}

Métricas con este threshold:
- BPCER: {recommended['bpcer']:.2f}% (usuarios genuinos rechazados)
- APCER Cloning: {recommended['apcer_cloning']:.2f}% (ataques cloning aceptados)
- APCER TTS: {recommended['apcer_tts']:.2f}% (ataques TTS aceptados)
- ACER: {recommended['acer']:.2f}% (error promedio)
- Detección Cloning: {recommended['detection_cloning']:.2f}%
- Detección TTS: {recommended['detection_tts']:.2f}%

Este threshold ofrece el mejor balance entre usabilidad y seguridad con AASIST-L.
""")


if __name__ == "__main__":
    find_optimal_threshold()
