"""
Optimización de Umbral para Anti-Spoofing

Analiza diferentes umbrales para encontrar el balance óptimo entre
BPCER (rechazo de genuinos) y APCER (aceptación de ataques).

Uso:
    python evaluation/threshold_optimization.py
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ThresholdOptimizer:
    """Optimizador de umbral para anti-spoofing."""
    
    def __init__(self):
        self.spoof_detector = SpoofDetectorAdapter(
            model_name="ensemble_antispoofing",
            use_gpu=True
        )
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def score_audios(self, audio_dir: Path, label: str) -> List[float]:
        """
        Obtener scores de spoof para audios.
        
        Args:
            audio_dir: Directorio con archivos de audio
            label: Etiqueta para logging
        
        Returns:
            Lista de scores
        """
        logger.info(f"📊 Procesando audios {label}...")
        
        audio_files = list(audio_dir.rglob("*.wav"))
        scores = []
        
        for i, audio_path in enumerate(audio_files, 1):
            try:
                audio_data = self.load_audio(audio_path)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                scores.append(spoof_score)
                
                if i % 20 == 0:
                    logger.info(f"  Procesados {i}/{len(audio_files)}")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando {audio_path.name}: {e}")
        
        logger.info(f"✅ Total {label}: {len(scores)} audios, score promedio: {np.mean(scores):.3f}\n")
        return scores
    
    def calculate_metrics_at_threshold(
        self, 
        genuine_scores: List[float], 
        attack_scores: List[float],
        threshold: float
    ) -> Dict[str, float]:
        """
        Calcular métricas para un umbral específico.
        
        Args:
            genuine_scores: Scores de genuinos
            attack_scores: Scores de ataques
            threshold: Umbral de decisión
        
        Returns:
            Diccionario con APCER, BPCER, ACER
        """
        genuine_scores = np.array(genuine_scores)
        attack_scores = np.array(attack_scores)
        
        # BPCER: % de genuinos rechazados (score >= threshold)
        bpcer = np.sum(genuine_scores >= threshold) / len(genuine_scores) * 100
        
        # APCER: % de ataques aceptados (score < threshold)
        apcer = np.sum(attack_scores < threshold) / len(attack_scores) * 100
        
        # ACER: Promedio
        acer = (apcer + bpcer) / 2
        
        return {
            'apcer': apcer,
            'bpcer': bpcer,
            'acer': acer
        }
    
    def find_optimal_thresholds(
        self, 
        genuine_scores: List[float], 
        attack_scores: List[float],
        tts_scores: List[float],
        cloning_scores: List[float]
    ) -> Dict:
        """
        Realizar barrida de umbrales desde 0.70 hasta 0.99.
        
        Returns:
            Diccionario con análisis completo
        """
        logger.info("🔍 Iniciando barrida de umbrales (0.70 - 0.99)...\n")
        
        thresholds = np.arange(0.70, 1.00, 0.01)
        results = []
        
        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(
                genuine_scores, 
                attack_scores, 
                threshold
            )
            
            # Métricas específicas por tipo de ataque
            tts_apcer = np.sum(np.array(tts_scores) < threshold) / len(tts_scores) * 100
            cloning_apcer = np.sum(np.array(cloning_scores) < threshold) / len(cloning_scores) * 100
            
            results.append({
                'threshold': threshold,
                'apcer': metrics['apcer'],
                'bpcer': metrics['bpcer'],
                'acer': metrics['acer'],
                'tts_apcer': tts_apcer,
                'cloning_apcer': cloning_apcer
            })
        
        return results
    
    def find_recommendations(self, results: List[Dict]) -> Dict:
        """
        Encontrar umbrales recomendados para diferentes escenarios.
        
        Returns:
            Diccionario con recomendaciones
        """
        results_arr = np.array([(r['threshold'], r['apcer'], r['bpcer'], r['acer']) 
                                for r in results])
        
        # 1. EER (Equal Error Rate): donde APCER ≈ BPCER
        eer_idx = np.argmin(np.abs(results_arr[:, 1] - results_arr[:, 2]))
        eer_result = results[eer_idx]
        
        # 2. Usabilidad: BPCER < 15%, minimizar APCER
        usability_candidates = [r for r in results if r['bpcer'] <= 15.0]
        if usability_candidates:
            usability_result = min(usability_candidates, key=lambda x: x['apcer'])
        else:
            usability_result = min(results, key=lambda x: x['bpcer'])
        
        # 3. Seguridad: APCER < 10%, minimizar BPCER
        security_candidates = [r for r in results if r['apcer'] <= 10.0]
        if security_candidates:
            security_result = min(security_candidates, key=lambda x: x['bpcer'])
        else:
            security_result = min(results, key=lambda x: x['apcer'])
        
        # 4. Equilibrio: ACER mínimo
        balanced_result = min(results, key=lambda x: x['acer'])
        
        return {
            'eer': eer_result,
            'usability': usability_result,
            'security': security_result,
            'balanced': balanced_result
        }
    
    def generate_visualizations(
        self, 
        results: List[Dict],
        recommendations: Dict,
        genuine_scores: List[float],
        attack_scores: List[float],
        output_path: Path
    ):
        """
        Generar visualizaciones del análisis de umbrales.
        """
        logger.info("📊 Generando visualizaciones...")
        
        fig = plt.figure(figsize=(16, 10))
        
        # Convertir a arrays
        thresholds = np.array([r['threshold'] for r in results])
        apcers = np.array([r['apcer'] for r in results])
        bpcers = np.array([r['bpcer'] for r in results])
        acers = np.array([r['acer'] for r in results])
        tts_apcers = np.array([r['tts_apcer'] for r in results])
        cloning_apcers = np.array([r['cloning_apcer'] for r in results])
        
        # 1. Trade-off APCER vs BPCER
        ax1 = plt.subplot(2, 2, 1)
        ax1.plot(thresholds, apcers, 'r-', linewidth=2, label='APCER (Ataques Aceptados)')
        ax1.plot(thresholds, bpcers, 'b-', linewidth=2, label='BPCER (Genuinos Rechazados)')
        ax1.plot(thresholds, acers, 'g--', linewidth=2, label='ACER (Promedio)')
        
        # Marcar puntos clave
        ax1.axvline(recommendations['eer']['threshold'], color='purple', 
                   linestyle=':', alpha=0.7, label=f"EER ({recommendations['eer']['threshold']:.3f})")
        ax1.axvline(recommendations['usability']['threshold'], color='orange',
                   linestyle=':', alpha=0.7, label=f"Usabilidad ({recommendations['usability']['threshold']:.3f})")
        ax1.axvline(recommendations['security']['threshold'], color='red',
                   linestyle=':', alpha=0.7, label=f"Seguridad ({recommendations['security']['threshold']:.3f})")
        
        ax1.set_xlabel('Umbral', fontsize=12)
        ax1.set_ylabel('Tasa de Error (%)', fontsize=12)
        ax1.set_title('Trade-off: APCER vs BPCER', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0.70, 0.99)
        ax1.set_ylim(0, 100)
        
        # 2. APCER por tipo de ataque
        ax2 = plt.subplot(2, 2, 2)
        ax2.plot(thresholds, tts_apcers, 'r-', linewidth=2, label='TTS')
        ax2.plot(thresholds, cloning_apcers, 'orange', linewidth=2, label='Clonación')
        ax2.plot(thresholds, apcers, 'b--', linewidth=2, label='Total')
        
        ax2.axvline(recommendations['usability']['threshold'], color='green',
                   linestyle=':', alpha=0.7, label='Umbral Recomendado')
        
        ax2.set_xlabel('Umbral', fontsize=12)
        ax2.set_ylabel('APCER (%)', fontsize=12)
        ax2.set_title('APCER por Tipo de Ataque', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0.70, 0.99)
        
        # 3. Distribución de scores con umbrales recomendados
        ax3 = plt.subplot(2, 2, 3)
        ax3.hist(genuine_scores, bins=30, alpha=0.6, color='blue', 
                label=f'Genuinos (n={len(genuine_scores)})', density=True)
        ax3.hist(attack_scores, bins=30, alpha=0.6, color='red',
                label=f'Ataques (n={len(attack_scores)})', density=True)
        
        # Líneas de umbrales recomendados
        ax3.axvline(recommendations['usability']['threshold'], color='green',
                   linestyle='--', linewidth=2, label='Usabilidad', alpha=0.8)
        ax3.axvline(recommendations['eer']['threshold'], color='purple',
                   linestyle='--', linewidth=2, label='EER', alpha=0.8)
        ax3.axvline(recommendations['security']['threshold'], color='darkred',
                   linestyle='--', linewidth=2, label='Seguridad', alpha=0.8)
        
        ax3.set_xlabel('Spoof Score', fontsize=12)
        ax3.set_ylabel('Densidad', fontsize=12)
        ax3.set_title('Distribución de Scores con Umbrales Recomendados', 
                     fontsize=14, fontweight='bold')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Tabla de recomendaciones
        ax4 = plt.subplot(2, 2, 4)
        ax4.axis('off')
        
        table_data = [
            ['Escenario', 'Umbral', 'APCER', 'BPCER', 'ACER'],
            ['EER (Equilibrio)', 
             f"{recommendations['eer']['threshold']:.3f}",
             f"{recommendations['eer']['apcer']:.2f}%",
             f"{recommendations['eer']['bpcer']:.2f}%",
             f"{recommendations['eer']['acer']:.2f}%"],
            ['Usabilidad', 
             f"{recommendations['usability']['threshold']:.3f}",
             f"{recommendations['usability']['apcer']:.2f}%",
             f"{recommendations['usability']['bpcer']:.2f}%",
             f"{recommendations['usability']['acer']:.2f}%"],
            ['Seguridad', 
             f"{recommendations['security']['threshold']:.3f}",
             f"{recommendations['security']['apcer']:.2f}%",
             f"{recommendations['security']['bpcer']:.2f}%",
             f"{recommendations['security']['acer']:.2f}%"],
            ['ACER Mínimo', 
             f"{recommendations['balanced']['threshold']:.3f}",
             f"{recommendations['balanced']['apcer']:.2f}%",
             f"{recommendations['balanced']['bpcer']:.2f}%",
             f"{recommendations['balanced']['acer']:.2f}%"],
        ]
        
        table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.25, 0.15, 0.15, 0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Estilo de tabla
        for i in range(len(table_data)):
            for j in range(len(table_data[0])):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                elif i == 2:  # Highlight usability
                    cell.set_facecolor('#E8F5E9')
        
        ax4.set_title('Umbrales Recomendados por Escenario', 
                     fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✅ Visualizaciones guardadas en: {output_path}\n")
    
    def generate_report(
        self, 
        results: List[Dict],
        recommendations: Dict,
        genuine_scores: List[float],
        attack_scores: List[float],
        tts_scores: List[float],
        cloning_scores: List[float],
        output_dir: Path
    ):
        """
        Generar reporte completo de optimización de umbrales.
        """
        logger.info("📝 Generando reporte...\n")
        
        report_lines = [
            "=" * 80,
            "OPTIMIZACIÓN DE UMBRAL - MÓDULO ANTI-SPOOFING",
            "=" * 80,
            "",
            "Dataset:",
            f"  - Audios Genuinos: {len(genuine_scores)}",
            f"  - Ataques TTS: {len(tts_scores)}",
            f"  - Ataques Clonación: {len(cloning_scores)}",
            f"  - Total Ataques: {len(attack_scores)}",
            "",
            "Estadísticas de Scores:",
            f"  - Genuinos:   mean={np.mean(genuine_scores):.3f}, std={np.std(genuine_scores):.3f}, "
            f"range=[{np.min(genuine_scores):.4f}-{np.max(genuine_scores):.4f}]",
            f"  - TTS:        mean={np.mean(tts_scores):.3f}, std={np.std(tts_scores):.3f}, "
            f"range=[{np.min(tts_scores):.4f}-{np.max(tts_scores):.4f}]",
            f"  - Clonación:  mean={np.mean(cloning_scores):.3f}, std={np.std(cloning_scores):.3f}, "
            f"range=[{np.min(cloning_scores):.4f}-{np.max(cloning_scores):.4f}]",
            "",
            "=" * 80,
            "UMBRALES RECOMENDADOS",
            "=" * 80,
            "",
            f"1. 🎯 EQUILIBRIO (EER - Equal Error Rate)",
            f"   Umbral: {recommendations['eer']['threshold']:.3f}",
            f"   - APCER: {recommendations['eer']['apcer']:.2f}%",
            f"   - BPCER: {recommendations['eer']['bpcer']:.2f}%",
            f"   - ACER:  {recommendations['eer']['acer']:.2f}%",
            f"   - TTS APCER: {recommendations['eer']['tts_apcer']:.2f}%",
            f"   - Cloning APCER: {recommendations['eer']['cloning_apcer']:.2f}%",
            f"   Recomendado para: Investigación, benchmarking",
            "",
            f"2. 👥 USABILIDAD (BPCER < 15%)",
            f"   Umbral: {recommendations['usability']['threshold']:.3f}",
            f"   - APCER: {recommendations['usability']['apcer']:.2f}%",
            f"   - BPCER: {recommendations['usability']['bpcer']:.2f}%",
            f"   - ACER:  {recommendations['usability']['acer']:.2f}%",
            f"   - TTS APCER: {recommendations['usability']['tts_apcer']:.2f}%",
            f"   - Cloning APCER: {recommendations['usability']['cloning_apcer']:.2f}%",
            f"   Recomendado para: Aplicaciones comerciales, banca digital ⭐",
            "",
            f"3. 🔒 SEGURIDAD (APCER < 10%)",
            f"   Umbral: {recommendations['security']['threshold']:.3f}",
            f"   - APCER: {recommendations['security']['apcer']:.2f}%",
            f"   - BPCER: {recommendations['security']['bpcer']:.2f}%",
            f"   - ACER:  {recommendations['security']['acer']:.2f}%",
            f"   - TTS APCER: {recommendations['security']['tts_apcer']:.2f}%",
            f"   - Cloning APCER: {recommendations['security']['cloning_apcer']:.2f}%",
            f"   Recomendado para: Alta seguridad, defensa gubernamental",
            "",
            f"4. ⚖️ ACER MÍNIMO",
            f"   Umbral: {recommendations['balanced']['threshold']:.3f}",
            f"   - APCER: {recommendations['balanced']['apcer']:.2f}%",
            f"   - BPCER: {recommendations['balanced']['bpcer']:.2f}%",
            f"   - ACER:  {recommendations['balanced']['acer']:.2f}%",
            f"   - TTS APCER: {recommendations['balanced']['tts_apcer']:.2f}%",
            f"   - Cloning APCER: {recommendations['balanced']['cloning_apcer']:.2f}%",
            f"   Recomendado para: Error promedio mínimo",
            "",
            "=" * 80,
            "ANÁLISIS Y RECOMENDACIONES",
            "=" * 80,
            "",
            "Interpretación:",
            "",
        ]
        
        # Análisis específico
        usability_rec = recommendations['usability']
        
        if usability_rec['bpcer'] <= 10:
            report_lines.append(f"✅ Excelente usabilidad: Solo {usability_rec['bpcer']:.1f}% de usuarios genuinos rechazados")
        elif usability_rec['bpcer'] <= 20:
            report_lines.append(f"✅ Buena usabilidad: {usability_rec['bpcer']:.1f}% de usuarios genuinos rechazados")
        else:
            report_lines.append(f"⚠️  Usabilidad moderada: {usability_rec['bpcer']:.1f}% de usuarios genuinos rechazados")
        
        if usability_rec['tts_apcer'] <= 1:
            report_lines.append(f"✅ Excelente protección contra TTS: {usability_rec['tts_apcer']:.2f}% de ataques TTS pasan")
        elif usability_rec['tts_apcer'] <= 5:
            report_lines.append(f"✅ Buena protección contra TTS: {usability_rec['tts_apcer']:.2f}% de ataques TTS pasan")
        else:
            report_lines.append(f"⚠️  Protección moderada contra TTS: {usability_rec['tts_apcer']:.2f}% de ataques TTS pasan")
        
        if usability_rec['cloning_apcer'] <= 10:
            report_lines.append(f"✅ Excelente protección contra clonación: {usability_rec['cloning_apcer']:.2f}% de ataques de clonación pasan")
        elif usability_rec['cloning_apcer'] <= 30:
            report_lines.append(f"⚠️  Protección moderada contra clonación: {usability_rec['cloning_apcer']:.2f}% de ataques de clonación pasan")
        else:
            report_lines.append(f"❌ Protección baja contra clonación: {usability_rec['cloning_apcer']:.2f}% de ataques de clonación pasan")
        
        report_lines.extend([
            "",
            "Notas:",
            "  - TTS (Text-to-Speech) es el ataque más común y mejor detectado",
            "  - Clonación de voz es más sofisticada y difícil de detectar",
            "  - El sistema antispoofing trabaja en conjunto con verificación de identidad (ECAPA-TDNN)",
            "  - Se recomienda usar el umbral de 'Usabilidad' para aplicaciones reales",
            "",
            "Próximos pasos:",
            "  1. Actualizar threshold en código de producción",
            "  2. Validar con datos adicionales",
            "  3. Monitorear métricas en producción",
            "  4. Ajustar según feedback de usuarios",
            "",
            "=" * 80,
        ])
        
        # Guardar reporte
        report_path = output_dir / "threshold_optimization.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"✅ Reporte guardado en: {report_path}")
        
        # Guardar datos JSON
        json_data = {
            'dataset': {
                'genuine_count': len(genuine_scores),
                'tts_count': len(tts_scores),
                'cloning_count': len(cloning_scores),
                'total_attacks': len(attack_scores)
            },
            'score_statistics': {
                'genuine': {
                    'mean': float(np.mean(genuine_scores)),
                    'std': float(np.std(genuine_scores)),
                    'min': float(np.min(genuine_scores)),
                    'max': float(np.max(genuine_scores))
                },
                'tts': {
                    'mean': float(np.mean(tts_scores)),
                    'std': float(np.std(tts_scores)),
                    'min': float(np.min(tts_scores)),
                    'max': float(np.max(tts_scores))
                },
                'cloning': {
                    'mean': float(np.mean(cloning_scores)),
                    'std': float(np.std(cloning_scores)),
                    'min': float(np.min(cloning_scores)),
                    'max': float(np.max(cloning_scores))
                }
            },
            'recommendations': recommendations,
            'all_thresholds': results
        }
        
        json_path = output_dir / "threshold_optimization.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"✅ Datos JSON guardados en: {json_path}\n")
    
    def print_summary_table(self, recommendations: Dict):
        """Imprimir tabla resumen en consola."""
        logger.info("=" * 100)
        logger.info("📊 RESUMEN DE UMBRALES RECOMENDADOS")
        logger.info("=" * 100)
        logger.info(f"{'Escenario':<20} {'Umbral':<10} {'APCER':<10} {'BPCER':<10} {'ACER':<10} {'Uso Recomendado':<30}")
        logger.info("-" * 100)
        
        scenarios = [
            ('EER (Equilibrio)', 'eer', 'Investigación/Benchmark'),
            ('Usabilidad ⭐', 'usability', 'Apps comerciales/Banca'),
            ('Seguridad', 'security', 'Alta seguridad'),
            ('ACER Mínimo', 'balanced', 'Error mínimo'),
        ]
        
        for name, key, usage in scenarios:
            rec = recommendations[key]
            logger.info(
                f"{name:<20} "
                f"{rec['threshold']:<10.3f} "
                f"{rec['apcer']:<10.2f} "
                f"{rec['bpcer']:<10.2f} "
                f"{rec['acer']:<10.2f} "
                f"{usage:<30}"
            )
        
        logger.info("=" * 100)
        logger.info("")
    
    def run(self):
        """Ejecutar optimización completa."""
        logger.info("=" * 80)
        logger.info("🎯 OPTIMIZACIÓN DE UMBRAL ANTISPOOFING")
        logger.info("=" * 80)
        logger.info("")
        
        # Paths - backend/evaluation/threshold_optimization.py
        # Necesitamos subir 2 niveles (backend -> apps) y luego a infra
        evaluation_dir = Path(__file__).parent  # evaluation/
        backend_dir = evaluation_dir.parent  # apps/backend/
        apps_dir = backend_dir.parent  # apps/
        project_root = apps_dir.parent  # proyecto/
        dataset_dir = project_root / "infra" / "evaluation" / "dataset"
        
        genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
        attacks_dir = dataset_dir / "attacks"
        cloning_dir = dataset_dir / "cloning"
        
        logger.info(f"📁 Rutas de datos:")
        logger.info(f"   Dataset base: {dataset_dir}")
        logger.info(f"   Genuinos: {genuine_dir}")
        logger.info(f"   TTS: {attacks_dir}")
        logger.info(f"   Clonación: {cloning_dir}")
        logger.info("")
        
        # Verificar que existan los directorios
        if not genuine_dir.exists():
            logger.error(f"❌ No existe: {genuine_dir}")
            return
        if not attacks_dir.exists():
            logger.error(f"❌ No existe: {attacks_dir}")
            return
        if not cloning_dir.exists():
            logger.error(f"❌ No existe: {cloning_dir}")
            return
        
        # Obtener scores
        genuine_scores = self.score_audios(genuine_dir, "Genuinos")
        tts_scores = self.score_audios(attacks_dir, "TTS")
        cloning_scores = self.score_audios(cloning_dir, "Clonación")
        
        attack_scores = tts_scores + cloning_scores
        
        # Optimizar umbrales
        results = self.find_optimal_thresholds(
            genuine_scores,
            attack_scores,
            tts_scores,
            cloning_scores
        )
        
        # Encontrar recomendaciones
        recommendations = self.find_recommendations(results)
        
        # Imprimir tabla resumen
        self.print_summary_table(recommendations)
        
        # Generar visualizaciones
        output_dir = backend_dir / "evaluation" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        viz_path = output_dir / "threshold_optimization_visualizations.png"
        self.generate_visualizations(
            results,
            recommendations,
            genuine_scores,
            attack_scores,
            viz_path
        )
        
        # Generar reporte
        self.generate_report(
            results,
            recommendations,
            genuine_scores,
            attack_scores,
            tts_scores,
            cloning_scores,
            output_dir
        )
        
        logger.info("=" * 80)
        logger.info("✅ OPTIMIZACIÓN COMPLETADA")
        logger.info("=" * 80)
        logger.info(f"📁 Resultados guardados en: {output_dir}")
        logger.info("")
        logger.info("⭐ RECOMENDACIÓN PRINCIPAL:")
        logger.info(f"   Para aplicaciones comerciales usa: threshold = {recommendations['usability']['threshold']:.3f}")
        logger.info(f"   Esto da: BPCER={recommendations['usability']['bpcer']:.2f}%, APCER={recommendations['usability']['apcer']:.2f}%")
        logger.info("")


def main():
    """Función principal."""
    optimizer = ThresholdOptimizer()
    optimizer.run()


if __name__ == "__main__":
    main()
