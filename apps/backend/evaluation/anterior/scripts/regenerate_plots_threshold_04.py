"""
Regenerate anti-spoofing plots with threshold 0.4

This script regenerates all anti-spoofing visualizations using
the optimized threshold of 0.4 instead of 0.7.

The plots will be saved to:
- evaluation/plots/antispoofing/threshold_04/
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from evaluation.scripts.analyze_antispoofing_corrected import CorrectedAntiSpoofingAnalyzer
import numpy as np


def main():
    print("="*80)
    print("REGENERANDO GRÁFICOS CON THRESHOLD 0.4")
    print("="*80)
    
    # Dataset paths
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    print(f"\n📁 Dataset: {dataset_dir}")
    
    # Initialize analyzer
    analyzer = CorrectedAntiSpoofingAnalyzer(model_name="ensemble_antispoofing")
    
    # Load audios
    print("\n📊 Cargando audios...")
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    print(f"   Genuinos: {len(genuine_files)}")
    print(f"   TTS: {len(tts_files)}")
    print(f"   Cloning: {len(cloning_files)}")
    
    # Get scores
    print("\n🔄 Procesando audios...")
    genuine_scores, genuine_files_used = analyzer.load_and_score_audios(genuine_files, "genuine")
    
    tts_scores = []
    tts_files_used = []
    if tts_files:
        tts_scores, tts_files_used = analyzer.load_and_score_audios(tts_files, "tts")
    
    cloning_scores, cloning_files_used = analyzer.load_and_score_audios(cloning_files, "cloning")
    
    genuine_scores = np.array(genuine_scores)
    tts_scores = np.array(tts_scores) if len(tts_scores) > 0 else np.array([])
    cloning_scores = np.array(cloning_scores)
    
    # Generate plots with threshold 0.4 highlighted
    print("\n📊 Generando gráficos...")
    
    # Create output directory
    output_dir = Path("evaluation/plots/antispoofing/threshold_04")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate comprehensive report and plots
    if len(tts_scores) > 0:
        report_path = analyzer.generate_report(
            genuine_scores,
            tts_scores,
            cloning_scores,
            output_dir
        )
        print(f"\n✅ Reporte generado: {report_path}")
    
    # Generate visualizations - THIS IS THE KEY METHOD
    print("\n🎨 Generando visualizaciones...")
    plots_path = analyzer.create_visualizations(
        genuine_scores,
        tts_scores if len(tts_scores) > 0 else np.array([]),
        cloning_scores,
        output_dir
    )
    print(f"✅ Gráficos generados: {plots_path}")
    
    print("\n" + "="*80)
    print("RESUMEN DE ARCHIVOS GENERADOS")
    print("="*80)
    
    plot_files = list(output_dir.glob("*.png"))
    if plot_files:
        print(f"\n📁 Gráficos guardados en: {output_dir}/")
        for plot_file in sorted(plot_files):
            print(f"   ✅ {plot_file.name}")
    
    print(f"\n📝 Reporte: {output_dir / 'ANTISPOOFING_CORRECTED_REPORT.txt'}")
    
    # Key metrics with threshold 0.4
    bpcer_04 = analyzer.calculate_bpcer(genuine_scores, 0.4)
    apcer_cloning_04 = analyzer.calculate_apcer(cloning_scores, 0.4)
    
    if len(tts_scores) > 0:
        apcer_tts_04 = analyzer.calculate_apcer(tts_scores, 0.4)
        all_attacks = np.concatenate([tts_scores, cloning_scores])
        apcer_all_04 = analyzer.calculate_apcer(all_attacks, 0.4)
    else:
        apcer_tts_04 = None
        apcer_all_04 = apcer_cloning_04
    
    acer_04 = analyzer.calculate_acer(bpcer_04, apcer_all_04)
    
    print("\n" + "="*80)
    print("MÉTRICAS CON THRESHOLD 0.4")
    print("="*80)
    print(f"""
BPCER: {bpcer_04:.2f}%
APCER Cloning: {apcer_cloning_04:.2f}%
APCER TTS: {apcer_tts_04:.2f}% {'' if apcer_tts_04 else '(N/A)'}
ACER: {acer_04:.2f}%

Detección Cloning: {100 - apcer_cloning_04:.2f}%
Detección TTS: {100 - apcer_tts_04:.2f}% {'' if apcer_tts_04 else '(N/A)'}
""")
    
    print("\n✅ Gráficos regenerados exitosamente")
    print(f"📁 Ubicación: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
