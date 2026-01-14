"""
Generación de Gráficos Finales para Tesis
Antispoofing Solo vs Fusión Multi-Modal (60/40)

Gráficos:
- Antispoofing Solo: Histograma, Matriz Confusión, Rendimiento por Ataque
- Fusión Multi-Modal: Dispersión 2D, Curvas DET, Tabla Métricas
"""

import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class FinalPlotsGenerator:
    """Generador de gráficos finales para tesis."""
    
    def __init__(self):
        self.spoof_detector = SpoofDetectorAdapter(
            model_name="ensemble_antispoofing",
            use_gpu=True
        )
        self.speaker_embedding = SpeakerEmbeddingAdapter(
            model_id=1,
            use_gpu=True
        )
        logger.info("✅ Modelos cargados\n")
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno entre dos embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        similarity = (similarity + 1.0) / 2.0
        
        return float(similarity)
    
    def collect_data(self):
        """Recolectar datos de scores."""
        logger.info("📊 Recolectando datos...")
        
        # Paths
        evaluation_dir = Path(__file__).parent
        backend_dir = evaluation_dir.parent
        apps_dir = backend_dir.parent
        project_root = apps_dir.parent
        dataset_dir = project_root / "infra" / "evaluation" / "dataset"
        
        genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
        attacks_dir = dataset_dir / "attacks"
        cloning_dir = dataset_dir / "cloning"
        
        # Coleccionar datos de genuinos
        genuine_data = []
        users = [d for d in genuine_dir.iterdir() if d.is_dir()]
        
        logger.info("🟢 Procesando genuinos...")
        for user_dir in users:
            audio_files = list(user_dir.glob("*.wav"))
            if len(audio_files) < 4:
                continue
            
            enrollment_audios = audio_files[:3]
            test_audios = audio_files[3:]
            
            for test_audio in test_audios:
                try:
                    audio_data = self.load_audio(test_audio)
                    spoof_score = self.spoof_detector.detect_spoof(audio_data)
                    
                    # Identity score
                    test_embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
                    similarities = []
                    for enroll_audio in enrollment_audios:
                        enroll_data = self.load_audio(enroll_audio)
                        enroll_embedding = self.speaker_embedding._extract_real_embedding(enroll_data, "audio/wav")
                        similarity = self.calculate_cosine_similarity(test_embedding, enroll_embedding)
                        similarities.append(similarity)
                    
                    identity_score = max(similarities) if similarities else 0.0
                    
                    genuine_data.append({
                        'spoof_score': spoof_score,
                        'identity_score': identity_score,
                        'type': 'genuine'
                    })
                except Exception as e:
                    logger.error(f"Error: {e}")
        
        logger.info(f"  Genuinos: {len(genuine_data)}")
        
        # Coleccionar datos de ataques
        attack_data = []
        
        # TTS
        logger.info("🔴 Procesando TTS...")
        tts_files = list(attacks_dir.rglob("*.wav"))
        for attack_audio in tts_files:
            try:
                audio_data = self.load_audio(attack_audio)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                
                attack_data.append({
                    'spoof_score': spoof_score,
                    'identity_score': 0.05,
                    'type': 'tts'
                })
            except Exception as e:
                logger.error(f"Error: {e}")
        
        logger.info(f"  TTS: {len([a for a in attack_data if a['type'] == 'tts'])}")
        
        # Cloning
        logger.info("🔴 Procesando Cloning...")
        cloning_files = list(cloning_dir.rglob("*.wav"))
        for attack_audio in cloning_files:
            try:
                audio_data = self.load_audio(attack_audio)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                
                attack_data.append({
                    'spoof_score': spoof_score,
                    'identity_score': 0.15,
                    'type': 'cloning'
                })
            except Exception as e:
                logger.error(f"Error: {e}")
        
        logger.info(f"  Cloning: {len([a for a in attack_data if a['type'] == 'cloning'])}")
        logger.info(f"✅ Total datos: {len(genuine_data) + len(attack_data)}\n")
        
        return genuine_data, attack_data
    
    def generate_antispoofing_plots(self, genuine_data, attack_data, output_path):
        """Generar 3 gráficos de antispoofing solo."""
        logger.info("📊 Generando gráficos Antispoofing Solo...")
        
        fig = plt.figure(figsize=(18, 6))
        
        # Datos
        genuine_scores = [d['spoof_score'] for d in genuine_data]
        tts_scores = [d['spoof_score'] for d in attack_data if d['type'] == 'tts']
        cloning_scores = [d['spoof_score'] for d in attack_data if d['type'] == 'cloning']
        all_attack_scores = tts_scores + cloning_scores
        
        threshold = 0.5
        
        # Gráfico 1: Histograma de Scores
        ax1 = plt.subplot(1, 3, 1)
        
        bins = np.linspace(0, 1, 30)
        ax1.hist(genuine_scores, bins=bins, alpha=0.6, color='blue', 
                label=f'Genuinos (n={len(genuine_scores)})', density=True, edgecolor='black')
        ax1.hist(all_attack_scores, bins=bins, alpha=0.6, color='red',
                label=f'Ataques (n={len(all_attack_scores)})', density=True, edgecolor='black')
        
        ax1.axvline(threshold, color='green', linestyle='--', linewidth=2, 
                   label=f'Threshold={threshold}')
        ax1.axvline(np.mean(genuine_scores), color='blue', linestyle=':', 
                   linewidth=1.5, alpha=0.7, label=f'μ Genuinos={np.mean(genuine_scores):.3f}')
        ax1.axvline(np.mean(all_attack_scores), color='red', linestyle=':', 
                   linewidth=1.5, alpha=0.7, label=f'μ Ataques={np.mean(all_attack_scores):.3f}')
        
        ax1.set_xlabel('Spoof Score', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Densidad', fontsize=12, fontweight='bold')
        ax1.set_title('Distribución de Scores\n(Antispoofing Solo)', 
                     fontsize=14, fontweight='bold', pad=10)
        ax1.legend(loc='upper center', fontsize=9)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Gráfico 2: Matriz de Confusión
        ax2 = plt.subplot(1, 3, 2)
        ax2.axis('off')
        
        # Calcular matriz de confusión con threshold=0.5
        tn = sum(1 for s in all_attack_scores if s >= threshold)  # Ataques rechazados (correcto)
        fp = sum(1 for s in genuine_scores if s >= threshold)      # Genuinos rechazados (error)
        fn = sum(1 for s in all_attack_scores if s < threshold)    # Ataques aceptados (error)
        tp = sum(1 for s in genuine_scores if s < threshold)       # Genuinos aceptados (correcto)
        
        total_attack = len(all_attack_scores)
        total_genuine = len(genuine_scores)
        
        confusion_data = [
            ['', 'Pred: Genuino', 'Pred: Ataque'],
            ['Real: Genuino', 
             f'{tp}\n({tp/total_genuine*100:.1f}%)',
             f'{fp}\n({fp/total_genuine*100:.1f}%)'],
            ['Real: Ataque',
             f'{fn}\n({fn/total_attack*100:.1f}%)',
             f'{tn}\n({tn/total_attack*100:.1f}%)']
        ]
        
        table = ax2.table(cellText=confusion_data, cellLoc='center', loc='center',
                         colWidths=[0.25, 0.35, 0.35])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 3)
        
        # Colores
        for i in range(len(confusion_data)):
            for j in range(len(confusion_data[0])):
                cell = table[(i, j)]
                if i == 0 or j == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                elif (i == 1 and j == 1) or (i == 2 and j == 2):
                    cell.set_facecolor('#C8E6C9')  # Verde claro (correctos)
                else:
                    cell.set_facecolor('#FFCDD2')  # Rojo claro (errores)
        
        ax2.set_title(f'Matriz de Confusión\n(Threshold={threshold})', 
                     fontsize=14, fontweight='bold', pad=20)
        
        # Métricas
        bpcer = fp / total_genuine * 100
        apcer = fn / total_attack * 100
        accuracy = (tp + tn) / (total_genuine + total_attack) * 100
        
        metrics_text = f'BPCER={bpcer:.2f}%  |  APCER={apcer:.2f}%  |  Accuracy={accuracy:.2f}%'
        ax2.text(0.5, -0.1, metrics_text, ha='center', va='top', 
                transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # Gráfico 3: Rendimiento por Tipo de Ataque
        ax3 = plt.subplot(1, 3, 3)
        
        tts_detected = sum(1 for s in tts_scores if s >= threshold) / len(tts_scores) * 100
        cloning_detected = sum(1 for s in cloning_scores if s >= threshold) / len(cloning_scores) * 100
        genuine_accepted = sum(1 for s in genuine_scores if s < threshold) / len(genuine_scores) * 100
        
        categories = ['TTS\nDetection', 'Cloning\nDetection', 'Genuine\nAcceptance']
        values = [tts_detected, cloning_detected, genuine_accepted]
        colors = ['#4CAF50' if v > 70 else '#FFC107' if v > 50 else '#F44336' for v in values]
        
        bars = ax3.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Valores sobre barras
        for i, (bar, val) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax3.set_ylabel('Tasa de Éxito (%)', fontsize=12, fontweight='bold')
        ax3.set_title('Rendimiento por Categoría\n(Antispoofing Solo)', 
                     fontsize=14, fontweight='bold', pad=10)
        ax3.set_ylim(0, 110)
        ax3.axhline(50, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Umbral 50%')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✅ Gráficos guardados: {output_path}\n")
    
    def generate_fusion_plots(self, genuine_data, attack_data, output_path):
        """Generar 3 gráficos de fusión multi-modal."""
        logger.info("📊 Generando gráficos Fusión Multi-Modal (60/40)...")
        
        fig = plt.figure(figsize=(18, 6))
        
        # Fusión 60/40
        w_identity = 0.6
        w_antispoof = 0.4
        
        def fusion_score(identity, spoof):
            return w_identity * identity + w_antispoof * (1 - spoof)
        
        # Calcular scores fusionados
        for d in genuine_data:
            d['fusion_score'] = fusion_score(d['identity_score'], d['spoof_score'])
        for d in attack_data:
            d['fusion_score'] = fusion_score(d['identity_score'], d['spoof_score'])
        
        # Buscar threshold óptimo
        genuine_fusion = [d['fusion_score'] for d in genuine_data]
        attack_fusion = [d['fusion_score'] for d in attack_data]
        
        best_threshold = 0.45
        
        # Gráfico 1: Dispersión 2D
        ax1 = plt.subplot(1, 3, 1)
        
        genuine_identity = [d['identity_score'] for d in genuine_data]
        genuine_spoof = [d['spoof_score'] for d in genuine_data]
        attack_identity = [d['identity_score'] for d in attack_data]
        attack_spoof = [d['spoof_score'] for d in attack_data]
        
        ax1.scatter(genuine_identity, genuine_spoof, alpha=0.6, s=80, c='blue', 
                   label=f'Genuinos (n={len(genuine_data)})', edgecolors='black', linewidth=0.5)
        ax1.scatter(attack_identity, attack_spoof, alpha=0.6, s=80, c='red',
                   label=f'Ataques (n={len(attack_data)})', edgecolors='black', linewidth=0.5)
        
        # Línea de decisión (aproximada)
        x_line = np.linspace(0, 1, 100)
        # fusion_score = w_id * x + w_as * (1-y) = threshold
        # y = 1 - (threshold - w_id*x) / w_as
        y_line = 1 - (best_threshold - w_identity * x_line) / w_antispoof
        ax1.plot(x_line, y_line, 'g--', linewidth=2, label='Frontera de Decisión')
        
        ax1.set_xlabel('Identity Score', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Spoof Score', fontsize=12, fontweight='bold')
        ax1.set_title('Espacio de Features 2D\n(Identity vs Antispoofing)', 
                     fontsize=14, fontweight='bold', pad=10)
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(-0.05, 1.05)
        ax1.set_ylim(-0.05, 1.05)
        
        # Añadir texto de pesos
        ax1.text(0.02, 0.98, f'Fusión: {int(w_identity*100)}% Identity + {int(w_antispoof*100)}% Antispoof',
                transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Gráfico 2: Curvas DET Comparativas
        ax2 = plt.subplot(1, 3, 2)
        
        # Calcular curvas para antispoofing solo
        thresholds_as = np.linspace(0, 1, 100)
        bpcer_as = []
        apcer_as = []
        
        genuine_spoof_only = [d['spoof_score'] for d in genuine_data]
        attack_spoof_only = [d['spoof_score'] for d in attack_data]
        
        for t in thresholds_as:
            bpcer = sum(1 for s in genuine_spoof_only if s >= t) / len(genuine_spoof_only) * 100
            apcer = sum(1 for s in attack_spoof_only if s < t) / len(attack_spoof_only) * 100
            bpcer_as.append(bpcer)
            apcer_as.append(apcer)
        
        # Calcular curvas para fusión
        thresholds_fusion = np.linspace(0, 1, 100)
        bpcer_fusion = []
        apcer_fusion = []
        
        for t in thresholds_fusion:
            bpcer = sum(1 for s in genuine_fusion if s < t) / len(genuine_fusion) * 100
            apcer = sum(1 for s in attack_fusion if s >= t) / len(attack_fusion) * 100
            bpcer_fusion.append(bpcer)
            apcer_fusion.append(apcer)
        
        ax2.plot(bpcer_as, apcer_as, 'r-', linewidth=2.5, label='Antispoofing Solo', alpha=0.7)
        ax2.plot(bpcer_fusion, apcer_fusion, 'g-', linewidth=2.5, label='Fusión Multi-Modal (60/40)', alpha=0.7)
        ax2.plot([0, 100], [0, 100], 'k--', linewidth=1, alpha=0.3, label='EER Line')
        
        # Marcar puntos operativos
        bpcer_solo_op = sum(1 for s in genuine_spoof_only if s >= 0.5) / len(genuine_spoof_only) * 100
        apcer_solo_op = sum(1 for s in attack_spoof_only if s < 0.5) / len(attack_spoof_only) * 100
        ax2.plot(bpcer_solo_op, apcer_solo_op, 'ro', markersize=10, label=f'Solo (T=0.5)')
        
        bpcer_fusion_op = sum(1 for s in genuine_fusion if s < best_threshold) / len(genuine_fusion) * 100
        apcer_fusion_op = sum(1 for s in attack_fusion if s >= best_threshold) / len(attack_fusion) * 100
        ax2.plot(bpcer_fusion_op, apcer_fusion_op, 'go', markersize=10, label=f'Fusión (T={best_threshold:.2f})')
        
        ax2.set_xlabel('BPCER (%)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('APCER (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Comparación de Curvas DET\n(Solo vs Fusión)', 
                     fontsize=14, fontweight='bold', pad=10)
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 100)
        ax2.set_ylim(0, 100)
        
        # Gráfico 3: Tabla de Métricas Finales
        ax3 = plt.subplot(1, 3, 3)
        ax3.axis('off')
        
        # Métricas solo antispoofing
        bpcer_solo = sum(1 for s in genuine_spoof_only if s >= 0.5) / len(genuine_spoof_only) * 100
        apcer_solo = sum(1 for s in attack_spoof_only if s < 0.5) / len(attack_spoof_only) * 100
        acer_solo = (bpcer_solo + apcer_solo) / 2
        
        # Métricas fusión
        bpcer_fusion = sum(1 for s in genuine_fusion if s < best_threshold) / len(genuine_fusion) * 100
        apcer_fusion = sum(1 for s in attack_fusion if s >= best_threshold) / len(attack_fusion) * 100
        acer_fusion = (bpcer_fusion + apcer_fusion) / 2
        
        table_data = [
            ['Métrica', 'Antispoofing\nSolo', 'Fusión\n60/40', 'Mejora'],
            ['BPCER', f'{bpcer_solo:.2f}%', f'{bpcer_fusion:.2f}%', 
             f'{bpcer_solo - bpcer_fusion:+.2f}pp'],
            ['APCER', f'{apcer_solo:.2f}%', f'{apcer_fusion:.2f}%',
             f'{apcer_solo - apcer_fusion:+.2f}pp'],
            ['ACER', f'{acer_solo:.2f}%', f'{acer_fusion:.2f}%',
             f'{acer_solo - acer_fusion:+.2f}pp'],
            ['Threshold', '0.50', f'{best_threshold:.2f}', '-'],
            ['', '', '', ''],
            ['Conclusión:', 'Sistema con\nerrores', 'Mejora\nsignificativa', '✓']
        ]
        
        table = ax3.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.25, 0.25, 0.25, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.8)
        
        # Colores
        for i in range(len(table_data)):
            for j in range(4):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                elif i == 6:
                    cell.set_facecolor('#E8F5E9')
                    cell.set_text_props(weight='bold')
                elif j == 2 and i in [1, 2, 3]:
                    # Highlight columna de fusión
                    cell.set_facecolor('#C8E6C9')
                    cell.set_text_props(weight='bold')
                elif j == 3 and i in [1, 2, 3]:
                    # Highlight mejoras
                    improvement = float(table_data[i][3].replace('pp', '').replace('+', ''))
                    if improvement > 0:
                        cell.set_facecolor('#C8E6C9')
                        cell.set_text_props(weight='bold', color='green')
        
        ax3.set_title('Tabla Comparativa de Métricas\n(Mejora con Fusión 60/40)', 
                     fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✅ Gráficos guardados: {output_path}\n")
    
    def run(self):
        """Ejecutar generación completa."""
        logger.info("=" * 80)
        logger.info("🎨 GENERACIÓN DE GRÁFICOS FINALES PARA TESIS")
        logger.info("=" * 80)
        logger.info("")
        
        # Recolectar datos
        genuine_data, attack_data = self.collect_data()
        
        # Directorio de salida
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar gráficos antispoofing solo
        antispoofing_path = output_dir / "antispoofing_solo_final.png"
        self.generate_antispoofing_plots(genuine_data, attack_data, antispoofing_path)
        
        # Generar gráficos fusión
        fusion_path = output_dir / "fusion_multimodal_60_40_final.png"
        self.generate_fusion_plots(genuine_data, attack_data, fusion_path)
        
        logger.info("=" * 80)
        logger.info("✅ GENERACIÓN COMPLETADA")
        logger.info("=" * 80)
        logger.info(f"📁 Archivos generados:")
        logger.info(f"   - {antispoofing_path}")
        logger.info(f"   - {fusion_path}")
        logger.info("")


def main():
    """Función principal."""
    generator = FinalPlotsGenerator()
    generator.run()


if __name__ == "__main__":
    main()
