"""
Comparar scores de antispoofing entre evaluación individual y sistema integrado
para las mismas muestras de cloning.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def load_tdcf_results() -> List[Dict]:
    """Cargar resultados del sistema integrado."""
    results_file = Path(__file__).parent / "results" / "tdcf_system_evaluation.json"
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Extraer solo muestras de cloning de attack_results
    cloning_results = []
    for sample in data['attack_results']:
        if sample['attack_type'] == 'cloning':
            cloning_results.append({
                'filename': sample['filename'],
                'stage1_antispoof_score': sample['result']['stage1_antispoof_score']
            })
    
    return cloning_results


def score_cloning_individually() -> Dict[str, float]:
    """Obtener scores de antispoofing evaluando cloning individualmente."""
    # Mismo directorio que usa evaluate_antispoofing.py
    base_dir = Path(__file__).parent.parent
    project_root = base_dir.parent.parent
    dataset_dir = project_root / "infra" / "evaluation" / "dataset"
    cloning_dir = dataset_dir / "cloning"
    
    if not cloning_dir.exists():
        logger.error(f"❌ Directorio no encontrado: {cloning_dir}")
        return {}
    
    # Inicializar detector
    spoof_detector = SpoofDetectorAdapter(
        model_name="ensemble_antispoofing",
        use_gpu=True
    )
    
    # Procesar cada archivo
    scores_by_file = {}
    audio_files = list(cloning_dir.rglob("*.wav"))
    
    logger.info(f"\n🔍 Procesando {len(audio_files)} audios de cloning...\n")
    
    for audio_path in audio_files:
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            score = spoof_detector.detect_spoof(audio_data)
            
            # Usar path relativo como key
            rel_path = str(audio_path.relative_to(cloning_dir))
            scores_by_file[rel_path] = score
            
        except Exception as e:
            logger.error(f"Error procesando {audio_path.name}: {e}")
    
    return scores_by_file


def main():
    print("=" * 80)
    print("COMPARACIÓN DE SCORES: EVALUACIÓN INDIVIDUAL VS SISTEMA INTEGRADO")
    print("=" * 80)
    
    # 1. Obtener scores del sistema integrado (tdcf)
    logger.info("\n📊 Cargando resultados del sistema integrado...")
    tdcf_results = load_tdcf_results()
    
    # 2. Obtener scores evaluando individualmente
    logger.info("\n🔬 Evaluando cloning individualmente...")
    individual_scores = score_cloning_individually()
    
    # 3. Comparar
    print("\n" + "=" * 80)
    print("COMPARACIÓN DE SCORES")
    print("=" * 80)
    
    threshold = 0.994
    
    # Scores del sistema integrado
    tdcf_scores = [r['stage1_antispoof_score'] for r in tdcf_results]
    tdcf_mean = np.mean(tdcf_scores)
    tdcf_rejected = sum(1 for s in tdcf_scores if s >= threshold)
    
    # Scores individuales
    individual_list = list(individual_scores.values())
    individual_mean = np.mean(individual_list)
    individual_rejected = sum(1 for s in individual_list if s >= threshold)
    
    print(f"\n📈 SISTEMA INTEGRADO (n={len(tdcf_scores)}):")
    print(f"   Score promedio:    {tdcf_mean:.4f}")
    print(f"   Rechazados:        {tdcf_rejected}/{len(tdcf_scores)} ({tdcf_rejected/len(tdcf_scores)*100:.1f}%)")
    print(f"   Threshold:         {threshold}")
    
    print(f"\n📈 EVALUACIÓN INDIVIDUAL (n={len(individual_list)}):")
    print(f"   Score promedio:    {individual_mean:.4f}")
    print(f"   Rechazados:        {individual_rejected}/{len(individual_list)} ({individual_rejected/len(individual_list)*100:.1f}%)")
    print(f"   Threshold:         {threshold}")
    
    # Diferencia
    print(f"\n🔍 DIFERENCIA:")
    print(f"   Δ Score promedio:  {abs(tdcf_mean - individual_mean):.4f}")
    print(f"   Δ Rechazo:         {abs(tdcf_rejected - individual_rejected)} muestras")
    
    # Análisis detallado si hay diferencia
    if abs(tdcf_rejected - individual_rejected) > 0:
        print(f"\n⚠️  HAY DIFERENCIA EN DETECCIÓN")
        print(f"\n   Distribución de scores (Sistema Integrado):")
        print(f"   Min:  {min(tdcf_scores):.4f}")
        print(f"   Q1:   {np.percentile(tdcf_scores, 25):.4f}")
        print(f"   Med:  {np.median(tdcf_scores):.4f}")
        print(f"   Q3:   {np.percentile(tdcf_scores, 75):.4f}")
        print(f"   Max:  {max(tdcf_scores):.4f}")
        
        print(f"\n   Distribución de scores (Individual):")
        print(f"   Min:  {min(individual_list):.4f}")
        print(f"   Q1:   {np.percentile(individual_list, 25):.4f}")
        print(f"   Med:  {np.median(individual_list):.4f}")
        print(f"   Q3:   {np.percentile(individual_list, 75):.4f}")
        print(f"   Max:  {max(individual_list):.4f}")
        
        # Muestras que pasan en uno pero no en otro
        if len(tdcf_scores) == len(individual_list):
            differences = []
            for i, (tdcf_s, ind_s) in enumerate(zip(tdcf_scores, individual_list)):
                if (tdcf_s >= threshold) != (ind_s >= threshold):
                    differences.append({
                        'index': i,
                        'tdcf': tdcf_s,
                        'individual': ind_s,
                        'tdcf_rejected': tdcf_s >= threshold,
                        'ind_rejected': ind_s >= threshold
                    })
            
            if differences:
                print(f"\n   🔴 Muestras con decisión diferente: {len(differences)}")
                for d in differences[:10]:  # Mostrar primeros 10
                    print(f"      Muestra {d['index']}: TDCF={d['tdcf']:.4f} (reject={d['tdcf_rejected']}) | Individual={d['individual']:.4f} (reject={d['ind_rejected']})")
    
    else:
        print(f"\n✅ AMBAS EVALUACIONES DAN EL MISMO RESULTADO")
        print(f"   Pero según antispoofing_evaluation.json, APCER = 29.73%")
        print(f"   Eso significa que con threshold 0.5 se detecta 70% de cloning")
        print(f"   Probemos con threshold 0.5...")
        
        # Probar con threshold 0.5
        tdcf_rejected_05 = sum(1 for s in tdcf_scores if s >= 0.5)
        individual_rejected_05 = sum(1 for s in individual_list if s >= 0.5)
        
        print(f"\n📊 CON THRESHOLD 0.5:")
        print(f"   Sistema Integrado:   {tdcf_rejected_05}/{len(tdcf_scores)} ({tdcf_rejected_05/len(tdcf_scores)*100:.1f}%)")
        print(f"   Evaluación Individual: {individual_rejected_05}/{len(individual_list)} ({individual_rejected_05/len(individual_list)*100:.1f}%)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
