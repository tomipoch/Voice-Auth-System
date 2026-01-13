"""
Generar gráficos comparativos:
1. AASIST base con threshold 0.4
2. AASIST-L con threshold 0.28
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))
sys.path.insert(0, str(backend_dir / "evaluation"))

from scripts.analyze_antispoofing_corrected import CorrectedAntiSpoofingAnalyzer
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def generate_comparison_plots():
    """Generar gráficos para AASIST base (0.4) y AASIST-L (0.28)."""
    
    print("="*80)
    print("GENERACIÓN DE GRÁFICOS COMPARATIVOS")
    print("="*80)
    
    # Dataset paths
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    print(f"\n📁 Dataset: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning")
    
    # ============================================================================
    # 1. AASIST BASE con threshold 0.4
    # ============================================================================
    print("\n" + "="*80)
    print("1️⃣  AASIST BASE - Threshold 0.4")
    print("="*80)
    
    # Necesitamos cargar con AASIST base (sin AASIST-L)
    # Temporalmente renombrar AASIST-L para forzar uso de base
    aasist_l_path = Path(__file__).parent.parent.parent / "models" / "anti-spoofing" / "aasist" / "AASIST-L.pth"
    aasist_l_backup = None
    
    if aasist_l_path.exists():
        aasist_l_backup = aasist_l_path.with_suffix('.pth.backup')
        aasist_l_path.rename(aasist_l_backup)
        print("   Temporalmente deshabilitando AASIST-L para usar AASIST base...")
    
    try:
        analyzer_base = CorrectedAntiSpoofingAnalyzer(model_name="ensemble_antispoofing")
        
        print("   Procesando audios con AASIST base...")
        genuine_scores_base, _ = analyzer_base.load_and_score_audios(genuine_files, "genuine")
        tts_scores_base = []
        if tts_files:
            tts_scores_base, _ = analyzer_base.load_and_score_audios(tts_files, "tts")
        cloning_scores_base, _ = analyzer_base.load_and_score_audios(cloning_files, "cloning")
        
        genuine_scores_base = np.array(genuine_scores_base)
        tts_scores_base = np.array(tts_scores_base) if len(tts_scores_base) > 0 else np.array([])
        cloning_scores_base = np.array(cloning_scores_base)
        
        # Métricas con threshold 0.4
        threshold_base = 0.4
        bpcer_base = analyzer_base.calculate_bpcer(genuine_scores_base, threshold_base)
        apcer_cloning_base = analyzer_base.calculate_apcer(cloning_scores_base, threshold_base)
        apcer_tts_base = analyzer_base.calculate_apcer(tts_scores_base, threshold_base) if len(tts_scores_base) > 0 else None
        
        print(f"\n   ✅ AASIST Base - Threshold {threshold_base}:")
        print(f"      BPCER: {bpcer_base:.2f}%")
        print(f"      APCER Cloning: {apcer_cloning_base:.2f}%")
        print(f"      APCER TTS: {apcer_tts_base:.2f}%" if apcer_tts_base else "      APCER TTS: N/A")
        
    finally:
        # Restaurar AASIST-L
        if aasist_l_backup and aasist_l_backup.exists():
            aasist_l_backup.rename(aasist_l_path)
            print("   AASIST-L restaurado")
    
    # ============================================================================
    # 2. AASIST-L con threshold 0.28
    # ============================================================================
    print("\n" + "="*80)
    print("2️⃣  AASIST-L - Threshold 0.28")
    print("="*80)
    
    analyzer_l = CorrectedAntiSpoofingAnalyzer(model_name="ensemble_antispoofing")
    
    print("   Procesando audios con AASIST-L...")
    genuine_scores_l, _ = analyzer_l.load_and_score_audios(genuine_files, "genuine")
    tts_scores_l = []
    if tts_files:
        tts_scores_l, _ = analyzer_l.load_and_score_audios(tts_files, "tts")
    cloning_scores_l, _ = analyzer_l.load_and_score_audios(cloning_files, "cloning")
    
    genuine_scores_l = np.array(genuine_scores_l)
    tts_scores_l = np.array(tts_scores_l) if len(tts_scores_l) > 0 else np.array([])
    cloning_scores_l = np.array(cloning_scores_l)
    
    # Métricas con threshold 0.28
    threshold_l = 0.28
    bpcer_l = analyzer_l.calculate_bpcer(genuine_scores_l, threshold_l)
    apcer_cloning_l = analyzer_l.calculate_apcer(cloning_scores_l, threshold_l)
    apcer_tts_l = analyzer_l.calculate_apcer(tts_scores_l, threshold_l) if len(tts_scores_l) > 0 else None
    
    print(f"\n   ✅ AASIST-L - Threshold {threshold_l}:")
    print(f"      BPCER: {bpcer_l:.2f}%")
    print(f"      APCER Cloning: {apcer_cloning_l:.2f}%")
    print(f"      APCER TTS: {apcer_tts_l:.2f}%" if apcer_tts_l else "      APCER TTS: N/A")
    
    # ============================================================================
    # 3. GENERAR GRÁFICOS
    # ============================================================================
    print("\n" + "="*80)
    print("📊 GENERANDO GRÁFICOS COMPARATIVOS")
    print("="*80)
    
    # Gráfico para AASIST base
    print("\n   Generando gráficos AASIST base...")
    output_base = Path("evaluation/plots/antispoofing/aasist_base_threshold_04")
    output_base.mkdir(parents=True, exist_ok=True)
    
    fig = create_custom_plot(
        genuine_scores_base, tts_scores_base, cloning_scores_base,
        threshold_base, "AASIST Base", analyzer_base
    )
    plot_path_base = output_base / "antispoofing_aasist_base_04.png"
    fig.savefig(plot_path_base, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"   ✅ {plot_path_base}")
    
    # Gráfico para AASIST-L
    print("   Generando gráficos AASIST-L...")
    output_l = Path("evaluation/plots/antispoofing/aasist_l_threshold_028")
    output_l.mkdir(parents=True, exist_ok=True)
    
    fig = create_custom_plot(
        genuine_scores_l, tts_scores_l, cloning_scores_l,
        threshold_l, "AASIST-L", analyzer_l
    )
    plot_path_l = output_l / "antispoofing_aasist_l_028.png"
    fig.savefig(plot_path_l, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"   ✅ {plot_path_l}")
    
    # Comparación lado a lado
    print("   Generando comparación lado a lado...")
    fig = create_side_by_side_comparison(
        genuine_scores_base, tts_scores_base, cloning_scores_base, threshold_base,
        genuine_scores_l, tts_scores_l, cloning_scores_l, threshold_l,
        analyzer_base
    )
    comparison_path = Path("evaluation/plots/antispoofing/comparison_aasist_vs_aasist_l.png")
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(comparison_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"   ✅ {comparison_path}")
    
    print("\n" + "="*80)
    print("✅ GRÁFICOS GENERADOS EXITOSAMENTE")
    print("="*80)


def create_custom_plot(genuine, tts, cloning, threshold, model_name, analyzer):
    """Crear gráfico personalizado con threshold marcado."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Anti-Spoofing Analysis - {model_name} (Threshold {threshold})', 
                 fontsize=16, fontweight='bold')
    
    # Histogram
    ax = axes[0, 0]
    ax.hist(genuine, bins=30, alpha=0.6, label='Genuine', color='green', edgecolor='black')
    if len(tts) > 0:
        ax.hist(tts, bins=30, alpha=0.6, label='TTS', color='red', edgecolor='black')
    ax.hist(cloning, bins=30, alpha=0.6, label='Cloning', color='orange', edgecolor='black')
    ax.axvline(threshold, color='purple', linestyle='--', linewidth=2.5, 
               label=f'Threshold {threshold}')
    ax.set_xlabel('Spoof Probability Score', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Score Distribution', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Box plot
    ax = axes[0, 1]
    data = [genuine, cloning]
    labels = ['Genuine', 'Cloning']
    colors = ['lightgreen', 'lightsalmon']
    if len(tts) > 0:
        data.insert(1, tts)
        labels.insert(1, 'TTS')
        colors.insert(1, 'lightcoral')
    
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.axhline(threshold, color='purple', linestyle='--', linewidth=2, 
               label=f'Threshold {threshold}')
    ax.set_ylabel('Spoof Probability Score', fontsize=12)
    ax.set_title('Score Distribution by Type', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # BPCER/APCER curves
    ax = axes[1, 0]
    thresholds = np.arange(0.0, 1.01, 0.01)
    
    bpcers = [analyzer.calculate_bpcer(genuine, t) for t in thresholds]
    apcers_cloning = [analyzer.calculate_apcer(cloning, t) for t in thresholds]
    
    ax.plot(thresholds, bpcers, 'g-', linewidth=2, label='BPCER (Genuine Rejected)')
    ax.plot(thresholds, apcers_cloning, 'orange', linewidth=2, label='APCER Cloning')
    
    if len(tts) > 0:
        apcers_tts = [analyzer.calculate_apcer(tts, t) for t in thresholds]
        ax.plot(thresholds, apcers_tts, 'r--', linewidth=1.5, alpha=0.7, label='APCER TTS')
    
    ax.axvline(threshold, color='purple', linestyle='--', linewidth=2.5, 
               label=f'Current: {threshold}')
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Error Rate (%)', fontsize=12)
    ax.set_title('BPCER vs APCER', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Metrics at threshold
    ax = axes[1, 1]
    ax.axis('off')
    
    bpcer = analyzer.calculate_bpcer(genuine, threshold)
    apcer_cloning = analyzer.calculate_apcer(cloning, threshold)
    apcer_tts = analyzer.calculate_apcer(tts, threshold) if len(tts) > 0 else None
    
    metrics_text = f"""
    METRICS AT THRESHOLD {threshold}
    
    BPCER: {bpcer:.2f}%
    (Genuine users rejected)
    
    APCER Cloning: {apcer_cloning:.2f}%
    (Cloning attacks accepted)
    
    Detection Cloning: {100-apcer_cloning:.2f}%
    """
    
    if apcer_tts is not None:
        metrics_text += f"""
    APCER TTS: {apcer_tts:.2f}%
    (TTS attacks accepted)
    
    Detection TTS: {100-apcer_tts:.2f}%
    """
    
    ax.text(0.1, 0.5, metrics_text, fontsize=14, family='monospace',
            verticalalignment='center', bbox=dict(boxstyle='round', 
            facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    return fig


def create_side_by_side_comparison(genuine_base, tts_base, cloning_base, threshold_base,
                                   genuine_l, tts_l, cloning_l, threshold_l, analyzer):
    """Crear comparación lado a lado."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Comparison: AASIST Base (0.4) vs AASIST-L (0.28)', 
                 fontsize=16, fontweight='bold')
    
    # Histograms comparison
    ax = axes[0, 0]
    ax.hist(genuine_base, bins=30, alpha=0.4, label='Genuine (Base)', color='green', edgecolor='black')
    ax.hist(cloning_base, bins=30, alpha=0.4, label='Cloning (Base)', color='orange', edgecolor='black')
    ax.axvline(threshold_base, color='blue', linestyle='--', linewidth=2, label=f'Threshold Base {threshold_base}')
    ax.set_xlabel('Score', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('AASIST Base Distribution', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[0, 1]
    ax.hist(genuine_l, bins=30, alpha=0.4, label='Genuine (L)', color='green', edgecolor='black')
    ax.hist(cloning_l, bins=30, alpha=0.4, label='Cloning (L)', color='orange', edgecolor='black')
    ax.axvline(threshold_l, color='purple', linestyle='--', linewidth=2, label=f'Threshold L {threshold_l}')
    ax.set_xlabel('Score', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('AASIST-L Distribution', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # BPCER/APCER comparison
    thresholds = np.arange(0.0, 1.01, 0.01)
    
    ax = axes[1, 0]
    bpcers_base = [analyzer.calculate_bpcer(genuine_base, t) for t in thresholds]
    apcers_base = [analyzer.calculate_apcer(cloning_base, t) for t in thresholds]
    ax.plot(thresholds, bpcers_base, 'g-', linewidth=2, label='BPCER')
    ax.plot(thresholds, apcers_base, 'orange', linewidth=2, label='APCER Cloning')
    ax.axvline(threshold_base, color='blue', linestyle='--', linewidth=2)
    ax.set_xlabel('Threshold', fontsize=11)
    ax.set_ylabel('Error Rate (%)', fontsize=11)
    ax.set_title('AASIST Base - BPCER vs APCER', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[1, 1]
    bpcers_l = [analyzer.calculate_bpcer(genuine_l, t) for t in thresholds]
    apcers_l = [analyzer.calculate_apcer(cloning_l, t) for t in thresholds]
    ax.plot(thresholds, bpcers_l, 'g-', linewidth=2, label='BPCER')
    ax.plot(thresholds, apcers_l, 'orange', linewidth=2, label='APCER Cloning')
    ax.axvline(threshold_l, color='purple', linestyle='--', linewidth=2)
    ax.set_xlabel('Threshold', fontsize=11)
    ax.set_ylabel('Error Rate (%)', fontsize=11)
    ax.set_title('AASIST-L - BPCER vs APCER', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    generate_comparison_plots()
