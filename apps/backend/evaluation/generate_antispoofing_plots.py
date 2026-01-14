"""
Generar gráficos limpios para presentación - Evaluación de Antispoofing
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def calculate_bpcer(genuine_scores, threshold):
    """Calcular BPCER (% de genuinos rechazados)."""
    genuine_scores = np.array(genuine_scores)
    rejected = np.sum(genuine_scores >= threshold)
    total = len(genuine_scores)
    return (rejected / total * 100) if total > 0 else 0.0


def calculate_apcer(attack_scores, threshold):
    """Calcular APCER (% de ataques aceptados)."""
    attack_scores = np.array(attack_scores)
    accepted = np.sum(attack_scores < threshold)
    total = len(attack_scores)
    return (accepted / total * 100) if total > 0 else 0.0


def load_audio_scores(dataset_dir):
    """Cargar y calcular scores para todos los audios."""
    spoof_detector = SpoofDetectorAdapter(
        model_name="ensemble_antispoofing",
        use_gpu=True
    )
    
    # Directorios
    genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    # Procesar genuinos
    logger.info("Procesando audios genuinos...")
    genuine_scores = []
    for audio_path in genuine_dir.rglob("*.wav"):
        with open(audio_path, 'rb') as f:
            score = spoof_detector.detect_spoof(f.read())
            genuine_scores.append(score)
    
    # Procesar TTS
    logger.info("Procesando ataques TTS...")
    tts_scores = []
    for audio_path in tts_dir.rglob("*.wav"):
        with open(audio_path, 'rb') as f:
            score = spoof_detector.detect_spoof(f.read())
            tts_scores.append(score)
    
    # Procesar cloning
    logger.info("Procesando ataques de cloning...")
    cloning_scores = []
    for audio_path in cloning_dir.rglob("*.wav"):
        with open(audio_path, 'rb') as f:
            score = spoof_detector.detect_spoof(f.read())
            cloning_scores.append(score)
    
    return genuine_scores, tts_scores, cloning_scores


def generate_plots(genuine_scores, tts_scores, cloning_scores, threshold, output_dir):
    """Generar los 3 gráficos principales."""
    
    all_attacks = tts_scores + cloning_scores
    
    # Crear figura con 3 subplots
    fig = plt.figure(figsize=(24, 8))
    
    # ====================================================================
    # 1. DISTRIBUCIÓN DE SCORES (HISTOGRAMA)
    # ====================================================================
    ax1 = plt.subplot(1, 3, 1)
    bins = np.linspace(0, 1, 50)
    
    # Histogramas
    ax1.hist(genuine_scores, bins=bins, alpha=0.7, color='green', 
            label=f'Genuinos (n={len(genuine_scores)})', density=False, edgecolor='darkgreen', linewidth=1.5)
    ax1.hist(all_attacks, bins=bins, alpha=0.7, color='red', 
            label=f'Ataques (n={len(all_attacks)})', density=False, edgecolor='darkred', linewidth=1.5)
    
    # Línea del umbral
    ax1.axvline(x=threshold, color='blue', linestyle='--', 
               linewidth=3, label=f'Umbral = {threshold:.3f}')
    
    # Líneas de medias
    mean_genuine = np.mean(genuine_scores)
    mean_attacks = np.mean(all_attacks)
    ax1.axvline(x=mean_genuine, color='green', linestyle=':', alpha=0.7, linewidth=2)
    ax1.axvline(x=mean_attacks, color='red', linestyle=':', alpha=0.7, linewidth=2)
    
    ax1.set_xlabel('Spoof Score', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Densidad', fontsize=14, fontweight='bold')
    ax1.set_title('Distribución de Scores', fontsize=16, fontweight='bold', pad=15)
    ax1.legend(loc='upper center', fontsize=12, framealpha=0.95)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelsize=12)
    
    # ====================================================================
    # 2. MATRIZ DE CONFUSIÓN
    # ====================================================================
    ax2 = plt.subplot(1, 3, 2)
    
    # Calcular valores
    genuine_accepted = sum(1 for s in genuine_scores if s < threshold)
    genuine_rejected = len(genuine_scores) - genuine_accepted
    attacks_rejected = sum(1 for s in all_attacks if s >= threshold)
    attacks_accepted = len(all_attacks) - attacks_rejected
    
    # Matriz: [Real: Genuino, Real: Ataque] x [Pred: Genuino, Pred: Ataque]
    confusion_data = np.array([
        [genuine_accepted, genuine_rejected],
        [attacks_accepted, attacks_rejected]
    ])
    
    # Colores: verde para bueno, rojo para malo
    colors = np.array([
        ['#90EE90', '#FFB6B6'],  # Genuino: aceptado (bien), rechazado (mal)
        ['#FFB6B6', '#90EE90']   # Ataque: aceptado (mal), rechazado (bien)
    ])
    
    # Crear matriz con colores personalizados
    for i in range(2):
        for j in range(2):
            ax2.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, 
                                       facecolor=colors[i, j], edgecolor='black', linewidth=2))
    
    # Etiquetas
    ax2.set_xlim(-0.5, 1.5)
    ax2.set_ylim(-0.5, 1.5)
    ax2.set_xticks([0, 1])
    ax2.set_yticks([0, 1])
    ax2.set_xticklabels(['Pred: Genuino', 'Pred: Ataque'], fontsize=13, fontweight='bold')
    ax2.set_yticklabels(['Real: Genuino', 'Real: Ataque'], fontsize=13, fontweight='bold')
    ax2.invert_yaxis()
    ax2.tick_params(labelsize=12)
    
    # Valores en cada celda
    for i in range(2):
        for j in range(2):
            total = len(genuine_scores) if i == 0 else len(all_attacks)
            percentage = (confusion_data[i, j] / total * 100) if total > 0 else 0
            ax2.text(j, i, f'{confusion_data[i, j]}\n({percentage:.1f}%)',
                    ha="center", va="center", fontsize=14, fontweight='bold')
    
    ax2.set_title(f'Matriz de Confusión\n(Threshold={threshold:.4f})', fontsize=16, fontweight='bold', pad=15)
    ax2.set_xlabel('Predicción del Sistema', fontsize=14, fontweight='bold', labelpad=10)
    ax2.set_ylabel('Clase Real', fontsize=14, fontweight='bold', labelpad=10)
    
    # Añadir métricas debajo
    bpcer = (genuine_rejected / len(genuine_scores) * 100) if len(genuine_scores) > 0 else 0
    apcer = (attacks_accepted / len(all_attacks) * 100) if len(all_attacks) > 0 else 0
    accuracy = ((genuine_accepted + attacks_rejected) / (len(genuine_scores) + len(all_attacks)) * 100)
    
    metrics_text = f'BPCER={bpcer:.2f}% | APCER={apcer:.2f}% | Accuracy={accuracy:.2f}%'
    ax2.text(0.5, -0.15, metrics_text, transform=ax2.transAxes, 
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # ====================================================================
    # 3. RENDIMIENTO POR CATEGORÍA
    # ====================================================================
    ax3 = plt.subplot(1, 3, 3)
    
    # Calcular métricas por tipo
    apcer_tts = calculate_apcer(tts_scores, threshold)
    apcer_cloning = calculate_apcer(cloning_scores, threshold)
    detection_tts = 100 - apcer_tts
    detection_cloning = 100 - apcer_cloning
    genuine_acceptance = 100 - bpcer
    
    categories = ['TTS\nDetection', 'Cloning\nDetection', 'Genuine\nAcceptance']
    values = [detection_tts, detection_cloning, genuine_acceptance]
    colors_bars = ['#90EE90', '#FFD700', '#87CEEB']
    
    bars = ax3.bar(categories, values, color=colors_bars, edgecolor='black', linewidth=2, alpha=0.8)
    
    # Añadir valores y línea de 50%
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', 
                fontsize=14, fontweight='bold')
    
    ax3.axhline(y=50, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Umbral 50%')
    
    ax3.set_ylabel('Tasa de Éxito (%)', fontsize=14, fontweight='bold')
    ax3.set_title('Rendimiento por Categoría', fontsize=16, fontweight='bold', pad=15)
    ax3.set_ylim([0, 110])
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.tick_params(labelsize=12)
    ax3.legend(fontsize=11)
    
    # Ajustar layout y guardar
    plt.tight_layout()
    
    output_path = output_dir / "antispoofing_solo_final.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Gráficos guardados en: {output_path}")
    
    return {
        'apcer_tts': apcer_tts,
        'apcer_cloning': apcer_cloning,
        'bpcer': bpcer,
        'detection_tts': detection_tts,
        'detection_cloning': detection_cloning,
        'genuine_acceptance': genuine_acceptance
    }


def main():
    print("=" * 80)
    print("GENERACIÓN DE GRÁFICOS - ANTISPOOFING INDIVIDUAL")
    print("=" * 80)
    print()
    
    # Configuración
    base_dir = Path(__file__).parent.parent
    project_root = base_dir.parent.parent
    dataset_dir = project_root / "infra" / "evaluation" / "dataset"
    output_dir = Path(__file__).parent / "results"
    
    # Cargar scores (o usar los existentes del JSON)
    results_json = output_dir / "antispoofing_evaluation.json"
    
    if results_json.exists():
        logger.info("📊 Cargando scores existentes del JSON...")
        with open(results_json, 'r') as f:
            data = json.load(f)
        
        threshold = data['overall']['threshold']
        
        # Recargar scores para generar gráficos
        genuine_scores, tts_scores, cloning_scores = load_audio_scores(dataset_dir)
    else:
        logger.info("📊 Calculando scores nuevos...")
        genuine_scores, tts_scores, cloning_scores = load_audio_scores(dataset_dir)
        
        # Encontrar threshold óptimo
        from evaluate_antispoofing import AntiSpoofingEvaluator
        evaluator = AntiSpoofingEvaluator()
        optimal = evaluator.find_optimal_threshold(genuine_scores, tts_scores + cloning_scores)
        threshold = optimal['threshold']
    
    logger.info(f"\n🎯 Threshold usado: {threshold:.4f}")
    logger.info(f"📦 Datos: {len(genuine_scores)} genuinos, {len(tts_scores)} TTS, {len(cloning_scores)} cloning\n")
    
    # Generar gráficos
    metrics = generate_plots(genuine_scores, tts_scores, cloning_scores, threshold, output_dir)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("MÉTRICAS FINALES")
    print("=" * 80)
    print(f"TTS Detection:         {metrics['detection_tts']:.2f}%")
    print(f"Cloning Detection:     {metrics['detection_cloning']:.2f}%")
    print(f"Genuine Acceptance:    {metrics['genuine_acceptance']:.2f}%")
    print(f"BPCER:                 {metrics['bpcer']:.2f}%")
    print(f"APCER TTS:             {metrics['apcer_tts']:.2f}%")
    print(f"APCER Cloning:         {metrics['apcer_cloning']:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
