"""
Compare anti-spoofing performance with different thresholds.

Evaluates the system with both threshold 0.7 (previous) and 0.4 (proposed)
on the same dataset to provide fair comparison.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from evaluation.scripts.analyze_antispoofing_corrected import CorrectedAntiSpoofingAnalyzer


def main():
    print("="*80)
    print("COMPARACIÓN DE THRESHOLDS: 0.7 vs 0.4")
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
    genuine_scores, _ = analyzer.load_and_score_audios(genuine_files, "genuine")
    cloning_scores, _ = analyzer.load_and_score_audios(cloning_files, "cloning")
    
    if tts_files:
        tts_scores, _ = analyzer.load_and_score_audios(tts_files, "tts")
    else:
        tts_scores = []
    
    genuine_scores = np.array(genuine_scores)
    cloning_scores = np.array(cloning_scores)
    tts_scores = np.array(tts_scores) if len(tts_scores) > 0 else np.array([])
    
    # Evaluate both thresholds
    thresholds = [0.7, 0.4]
    results = {}
    
    for threshold in thresholds:
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
        
        # Calculate with retries
        frr_1_retry = bpcer / 100
        frr_2_retries = 1 - (1 - bpcer/100)**2
        frr_3_retries = 1 - (1 - bpcer/100)**3
        
        results[threshold] = {
            'bpcer': bpcer,
            'apcer_tts': apcer_tts,
            'apcer_cloning': apcer_cloning,
            'apcer_all': apcer_all,
            'acer': acer,
            'detection_cloning': 100 - apcer_cloning,
            'detection_tts': 100 - apcer_tts if apcer_tts else None,
            'frr_1': frr_1_retry * 100,
            'frr_2': frr_2_retries * 100,
            'frr_3': frr_3_retries * 100
        }
    
    # Print comparison table
    print("\n" + "="*80)
    print("TABLA COMPARATIVA")
    print("="*80)
    
    print(f"\n{'Métrica':<30} | {'Threshold 0.7':>15} | {'Threshold 0.4':>15} | {'Cambio':>12}")
    print("-" * 80)
    
    # BPCER
    bpcer_07 = results[0.7]['bpcer']
    bpcer_04 = results[0.4]['bpcer']
    delta_bpcer = bpcer_04 - bpcer_07
    print(f"{'BPCER (genuinos rechazados)':<30} | {bpcer_07:>14.2f}% | {bpcer_04:>14.2f}% | {delta_bpcer:>+11.2f}pp")
    
    # APCER Cloning
    apcer_c_07 = results[0.7]['apcer_cloning']
    apcer_c_04 = results[0.4]['apcer_cloning']
    delta_apcer_c = apcer_c_04 - apcer_c_07
    print(f"{'APCER Cloning (aceptados)':<30} | {apcer_c_07:>14.2f}% | {apcer_c_04:>14.2f}% | {delta_apcer_c:>+11.2f}pp")
    
    # Detection Cloning
    det_c_07 = results[0.7]['detection_cloning']
    det_c_04 = results[0.4]['detection_cloning']
    delta_det_c = det_c_04 - det_c_07
    print(f"{'Detección Cloning':<30} | {det_c_07:>14.2f}% | {det_c_04:>14.2f}% | {delta_det_c:>+11.2f}pp")
    
    # APCER TTS
    if results[0.7]['apcer_tts']:
        apcer_t_07 = results[0.7]['apcer_tts']
        apcer_t_04 = results[0.4]['apcer_tts']
        delta_apcer_t = apcer_t_04 - apcer_t_07
        print(f"{'APCER TTS (aceptados)':<30} | {apcer_t_07:>14.2f}% | {apcer_t_04:>14.2f}% | {delta_apcer_t:>+11.2f}pp")
        
        det_t_07 = results[0.7]['detection_tts']
        det_t_04 = results[0.4]['detection_tts']
        delta_det_t = det_t_04 - det_t_07
        print(f"{'Detección TTS':<30} | {det_t_07:>14.2f}% | {det_t_04:>14.2f}% | {delta_det_t:>+11.2f}pp")
    
    # ACER
    acer_07 = results[0.7]['acer']
    acer_04 = results[0.4]['acer']
    delta_acer = acer_04 - acer_07
    print(f"{'ACER (error promedio)':<30} | {acer_07:>14.2f}% | {acer_04:>14.2f}% | {delta_acer:>+11.2f}pp")
    
    # FRR with retries
    print("\n" + "-" * 80)
    print("FRR Efectivo con Reintentos:")
    print("-" * 80)
    
    frr2_07 = results[0.7]['frr_2']
    frr2_04 = results[0.4]['frr_2']
    delta_frr2 = frr2_04 - frr2_07
    print(f"{'FRR (2 reintentos)':<30} | {frr2_07:>14.2f}% | {frr2_04:>14.2f}% | {delta_frr2:>+11.2f}pp")
    
    frr3_07 = results[0.7]['frr_3']
    frr3_04 = results[0.4]['frr_3']
    delta_frr3 = frr3_04 - frr3_07
    print(f"{'FRR (3 reintentos)':<30} | {frr3_07:>14.2f}% | {frr3_04:>14.2f}% | {delta_frr3:>+11.2f}pp")
    
    # System impact
    print("\n" + "="*80)
    print("IMPACTO EN EL SISTEMA COMPLETO")
    print("="*80)
    
    sr_pass_rate = 0.8378  # Speaker Recognition
    asr_pass_rate = 1.0  # ASR
    
    # Threshold 0.7
    as_pass_rate_07 = 1 - (bpcer_07 / 100)
    system_accept_07 = sr_pass_rate * as_pass_rate_07 * asr_pass_rate
    
    # Threshold 0.4 (con 2 reintentos)
    as_pass_rate_04 = 1 - (frr2_04 / 100)
    system_accept_04 = sr_pass_rate * as_pass_rate_04 * asr_pass_rate
    
    # Attack pass rate (cloning)
    cloning_pass_07 = 0.20 * (apcer_c_07 / 100) * 1.0
    cloning_pass_04 = 0.20 * (apcer_c_04 / 100) * 1.0
    
    print(f"\n📊 Usuario Legítimo:")
    print(f"   Threshold 0.7: SR (83.78%) → AS ({as_pass_rate_07*100:.2f}%) → ASR (100%) = {system_accept_07*100:.2f}%")
    print(f"   Threshold 0.4 (2 reintentos): SR (83.78%) → AS ({as_pass_rate_04*100:.2f}%) → ASR (100%) = {system_accept_04*100:.2f}%")
    print(f"   Mejora: {(system_accept_04 - system_accept_07)*100:+.2f}pp")
    
    print(f"\n🎭 Ataque Cloning:")
    print(f"   Threshold 0.7: SR (20%) → AS ({100-det_c_07:.2f}%) → ASR (100%) = {cloning_pass_07*100:.2f}% pasa")
    print(f"   Threshold 0.4: SR (20%) → AS ({100-det_c_04:.2f}%) → ASR (100%) = {cloning_pass_04*100:.2f}% pasa")
    print(f"   Diferencia: {(cloning_pass_04 - cloning_pass_07)*100:+.2f}pp más ataques pasan")
    
    # Analysis
    print("\n" + "="*80)
    print("ANÁLISIS Y RECOMENDACIÓN")
    print("="*80)
    
    if delta_det_c > 10:
        print("\n✅ MEJORA SIGNIFICATIVA con threshold 0.4:")
        print(f"   - Detección de cloning mejora {delta_det_c:.1f}pp")
        print(f"   - Aceptación de usuarios mejora {(system_accept_04 - system_accept_07)*100:.1f}pp")
        print(f"   - Trade-off: {(cloning_pass_04 - cloning_pass_07)*100:.1f}pp más ataques pasan (aceptable)")
    elif abs(delta_det_c) < 5:
        print("\n⚠️  MEJORA MARGINAL con threshold 0.4:")
        print(f"   - Detección de cloning similar ({delta_det_c:+.1f}pp)")
        print(f"   - BPCER más alto ({delta_bpcer:+.1f}pp)")
        print("   - Considerar mantener threshold 0.7")
    else:
        print("\n❌ EMPEORAMIENTO con threshold 0.4:")
        print(f"   - Detección de cloning empeora {delta_det_c:.1f}pp")
        print("   - Mantener threshold 0.7")
    
    print("\n📝 DATOS PARA LA TESIS:")
    print("-" * 80)
    print(f"""
Configuración: Ensemble AASIST (55%) + RawNet2 (45%)
Dataset: {len(genuine_files)} genuinos, {len(tts_files)} TTS, {len(cloning_files)} cloning

Threshold seleccionado: 0.4
- BPCER: {bpcer_04:.2f}%
- APCER Cloning: {apcer_c_04:.2f}% (Detección: {det_c_04:.2f}%)
- APCER TTS: {apcer_t_04:.2f}% (Detección: {det_t_04:.2f}%)
- ACER: {acer_04:.2f}%
- FRR efectivo (2 reintentos): {frr2_04:.2f}%
- Usuarios aceptados (sistema completo): {system_accept_04*100:.2f}%

Justificación: Balance pragmático entre detección de ataques y usabilidad.
El sistema confía en Speaker Recognition (FAR 0.90%) como primera línea de defensa.
""")


if __name__ == "__main__":
    main()
