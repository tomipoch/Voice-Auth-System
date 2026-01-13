"""
Evaluar sistema anti-spoofing con AASIST-L en lugar de AASIST base.

Compara métricas usando:
- AASIST-L (55%) + RawNet2 (45%) ensemble
- Threshold 0.4
"""

import sys
from pathlib import Path
import numpy as np
import logging

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))
sys.path.insert(0, str(backend_dir / "evaluation"))

from scripts.analyze_antispoofing_corrected import CorrectedAntiSpoofingAnalyzer

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def evaluate_aasist_l():
    """Evaluar anti-spoofing con AASIST-L."""
    
    print("="*80)
    print("EVALUACIÓN CON AASIST-L")
    print("="*80)
    
    # Dataset paths
    dataset_dir = Path(__file__).parent.parent.parent.parent.parent / "infra" / "evaluation" / "dataset"
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    print(f"\n📁 Dataset: {dataset_dir}")
    
    # Initialize analyzer (usará AASIST-L automáticamente si está disponible)
    print("\n🔧 Inicializando analizador con AASIST-L...")
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
    print("\n🔄 Procesando audios con AASIST-L...")
    genuine_scores, _ = analyzer.load_and_score_audios(genuine_files, "genuine")
    
    tts_scores = []
    if tts_files:
        tts_scores, _ = analyzer.load_and_score_audios(tts_files, "tts")
    
    cloning_scores, _ = analyzer.load_and_score_audios(cloning_files, "cloning")
    
    genuine_scores = np.array(genuine_scores)
    tts_scores = np.array(tts_scores) if len(tts_scores) > 0 else np.array([])
    cloning_scores = np.array(cloning_scores)
    
    # Calcular métricas con threshold 0.4
    threshold = 0.4
    
    print("\n" + "="*80)
    print(f"MÉTRICAS CON AASIST-L (Threshold {threshold})")
    print("="*80)
    
    bpcer = analyzer.calculate_bpcer(genuine_scores, threshold)
    apcer_cloning = analyzer.calculate_apcer(cloning_scores, threshold)
    
    if len(tts_scores) > 0:
        apcer_tts = analyzer.calculate_apcer(tts_scores, threshold)
        all_attacks = np.concatenate([tts_scores, cloning_scores])
        apcer_all = analyzer.calculate_apcer(all_attacks, threshold)
    else:
        apcer_tts = None
        apcer_all = apcer_cloning
    
    acer = analyzer.calculate_acer(bpcer, apcer_all)
    
    print(f"""
RESULTADOS:
-----------
BPCER (Genuinos rechazados):        {bpcer:.2f}%
APCER Cloning (Cloning aceptado):   {apcer_cloning:.2f}%
APCER TTS (TTS aceptado):           {apcer_tts:.2f}% {'' if apcer_tts else '(N/A)'}
ACER (Error promedio):              {acer:.2f}%

DETECCIÓN:
----------
Tasa detección Cloning:             {100 - apcer_cloning:.2f}%
Tasa detección TTS:                 {100 - apcer_tts:.2f}% {'' if apcer_tts else '(N/A)'}
""")
    
    # Comparación con métricas anteriores (AASIST base)
    print("="*80)
    print("COMPARACIÓN: AASIST-L vs AASIST Base")
    print("="*80)
    
    # Métricas anteriores con AASIST base y threshold 0.4
    prev_bpcer = 46.94
    prev_apcer_cloning = 54.05
    prev_apcer_tts = 98.63
    prev_acer = 76.48
    prev_det_cloning = 45.95
    prev_det_tts = 1.37
    
    print(f"""
Métrica                  | AASIST Base | AASIST-L    | Mejora
-------------------------|-------------|-------------|-------------
BPCER                    | {prev_bpcer:5.2f}%      | {bpcer:5.2f}%      | {prev_bpcer - bpcer:+.2f}%
APCER Cloning            | {prev_apcer_cloning:5.2f}%      | {apcer_cloning:5.2f}%      | {prev_apcer_cloning - apcer_cloning:+.2f}%
APCER TTS                | {prev_apcer_tts:5.2f}%      | {apcer_tts:5.2f}%      | {prev_apcer_tts - apcer_tts:+.2f}%
ACER                     | {prev_acer:5.2f}%      | {acer:5.2f}%      | {prev_acer - acer:+.2f}%
Detección Cloning        | {prev_det_cloning:5.2f}%      | {100-apcer_cloning:5.2f}%      | {(100-apcer_cloning) - prev_det_cloning:+.2f}%
Detección TTS            | {prev_det_tts:5.2f}%      | {100-apcer_tts:5.2f}%      | {(100-apcer_tts) - prev_det_tts:+.2f}%
""")
    
    # Análisis de mejora
    print("="*80)
    print("ANÁLISIS DE MEJORA")
    print("="*80)
    
    if bpcer < prev_bpcer:
        print(f"✅ BPCER mejoró: {prev_bpcer - bpcer:.2f}% menos usuarios genuinos rechazados")
    else:
        print(f"⚠️  BPCER empeoró: {bpcer - prev_bpcer:.2f}% más usuarios genuinos rechazados")
    
    if apcer_cloning < prev_apcer_cloning:
        print(f"✅ Detección de Cloning mejoró: {prev_apcer_cloning - apcer_cloning:.2f}% menos ataques aceptados")
    else:
        print(f"⚠️  Detección de Cloning empeoró: {apcer_cloning - prev_apcer_cloning:.2f}% más ataques aceptados")
    
    if apcer_tts and apcer_tts < prev_apcer_tts:
        print(f"✅ Detección de TTS mejoró: {prev_apcer_tts - apcer_tts:.2f}% menos ataques aceptados")
    else:
        print(f"⚠️  Detección de TTS sigue siendo crítica: {apcer_tts:.2f}% de ataques aceptados")
    
    if acer < prev_acer:
        print(f"✅ ACER mejoró: {prev_acer - acer:.2f}% de reducción en error total")
    else:
        print(f"⚠️  ACER empeoró: {acer - prev_acer:.2f}% de aumento en error total")
    
    # Generar reporte
    print("\n📝 Generando reporte completo...")
    output_dir = Path("evaluation/plots/antispoofing/aasist_l")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = analyzer.generate_report(
        genuine_scores, tts_scores, cloning_scores, output_dir
    )
    
    print(f"✅ Reporte guardado: {report_path}")
    
    # Generar visualizaciones
    print("📊 Generando visualizaciones...")
    plots_path = analyzer.create_visualizations(
        genuine_scores, tts_scores, cloning_scores, output_dir
    )
    print(f"✅ Gráficos guardados: {plots_path}")
    
    print("\n" + "="*80)
    print("✅ EVALUACIÓN CON AASIST-L COMPLETADA")
    print("="*80)


if __name__ == "__main__":
    evaluate_aasist_l()
