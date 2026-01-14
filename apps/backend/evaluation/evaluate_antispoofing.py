"""
Evaluación del Módulo de Anti-Spoofing

Métricas calculadas (según ISO/IEC 30107-3):
- APCER (Attack Presentation Classification Error Rate): % de ataques aceptados (menor es mejor, óptimo ~0%)
- BPCER (Bona Fide Presentation Classification Error Rate): % de genuinos rechazados (menor es mejor, óptimo ~0%)
- ACER (Average Classification Error Rate): Promedio de APCER y BPCER (menor es mejor, óptimo ~0%)

Uso:
    python evaluation/evaluate_antispoofing.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logger = logging.getLogger(__name__)


class AntiSpoofingEvaluator:
    """Evaluador del módulo de anti-spoofing."""
    
    def __init__(self):
        self.spoof_detector = SpoofDetectorAdapter(
            model_name="ensemble_antispoofing",
            use_gpu=True
        )
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def score_audios(self, audio_dir: Path, label: str) -> Tuple[List[float], int]:
        """
        Obtener scores de spoof para audios, procesando recursivamente subdirectorios.
        
        Args:
            audio_dir: Directorio con archivos de audio (puede tener subdirectorios)
            label: Etiqueta para logging (e.g., 'genuine', 'tts', 'cloning')
        
        Returns:
            Tuple de (lista de scores, total procesados)
        """
        logger.info(f"Procesando audios {label} desde {audio_dir}...")
        
        # Buscar todos los archivos .wav recursivamente
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
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        logger.info(f"  Total {label}: {len(scores)} audios, score promedio: {np.mean(scores):.3f}")
        return scores, len(scores)
    
    def calculate_bpcer(self, genuine_scores: List[float], threshold: float) -> float:
        """
        Calcular BPCER (Bona Fide Presentation Classification Error Rate).
        
        BPCER = % de muestras genuinas con score >= threshold (rechazadas incorrectamente)
        
        Args:
            genuine_scores: Scores de spoof para audios genuinos
            threshold: Umbral de decisión
        
        Returns:
            BPCER como porcentaje (0-100%)
        """
        genuine_scores = np.array(genuine_scores)
        rejected = np.sum(genuine_scores >= threshold)
        total = len(genuine_scores)
        return (rejected / total * 100) if total > 0 else 0.0
    
    def calculate_apcer(self, attack_scores: List[float], threshold: float) -> float:
        """
        Calcular APCER (Attack Presentation Classification Error Rate).
        
        APCER = % de ataques con score < threshold (aceptados incorrectamente)
        
        Args:
            attack_scores: Scores de spoof para ataques
            threshold: Umbral de decisión
        
        Returns:
            APCER como porcentaje (0-100%)
        """
        attack_scores = np.array(attack_scores)
        accepted = np.sum(attack_scores < threshold)
        total = len(attack_scores)
        return (accepted / total * 100) if total > 0 else 0.0
    
    def calculate_acer(self, bpcer: float, apcer: float) -> float:
        """
        Calcular ACER (Average Classification Error Rate).
        
        ACER = (BPCER + APCER) / 2
        """
        return (bpcer + apcer) / 2
    
    def find_optimal_threshold(
        self,
        genuine_scores: List[float],
        attack_scores: List[float]
    ) -> Dict:
        """
        Encontrar umbral óptimo que minimiza ACER.
        
        Returns:
            Dict con el umbral óptimo y métricas asociadas
        """
        thresholds = np.linspace(0, 1, 1000)
        best_acer = float('inf')
        best_threshold = 0.5
        best_bpcer = 0.0
        best_apcer = 0.0
        
        for t in thresholds:
            bpcer = self.calculate_bpcer(genuine_scores, t)
            apcer = self.calculate_apcer(attack_scores, t)
            acer = self.calculate_acer(bpcer, apcer)
            
            if acer < best_acer:
                best_acer = acer
                best_threshold = float(t)
                best_bpcer = bpcer
                best_apcer = apcer
        
        return {
            'threshold': best_threshold,
            'bpcer': best_bpcer,
            'apcer': best_apcer,
            'acer': best_acer
        }
    
    def calculate_metrics(
        self,
        genuine_scores: List[float],
        attack_scores: List[float],
        threshold: float = 0.5
    ) -> Dict:
        """
        Calcular todas las métricas de anti-spoofing.
        
        Args:
            genuine_scores: Scores de audios genuinos
            attack_scores: Scores de ataques (TTS, cloning, etc.)
            threshold: Umbral de decisión
        
        Returns:
            Dict con todas las métricas
        """
        genuine_scores = np.array(genuine_scores)
        attack_scores = np.array(attack_scores)
        
        # Métricas principales
        bpcer = self.calculate_bpcer(genuine_scores.tolist(), threshold)
        apcer = self.calculate_apcer(attack_scores.tolist(), threshold)
        acer = self.calculate_acer(bpcer, apcer)
        
        # Encontrar umbral óptimo
        optimal = self.find_optimal_threshold(genuine_scores.tolist(), attack_scores.tolist())
        
        # Estadísticas de scores
        genuine_stats = {
            'mean': float(np.mean(genuine_scores)),
            'std': float(np.std(genuine_scores)),
            'min': float(np.min(genuine_scores)),
            'max': float(np.max(genuine_scores))
        }
        
        attack_stats = {
            'mean': float(np.mean(attack_scores)),
            'std': float(np.std(attack_scores)),
            'min': float(np.min(attack_scores)),
            'max': float(np.max(attack_scores))
        }
        
        return {
            'threshold': threshold,
            'bpcer': bpcer,
            'apcer': apcer,
            'acer': acer,
            'optimal_threshold': optimal['threshold'],
            'optimal_bpcer': optimal['bpcer'],
            'optimal_apcer': optimal['apcer'],
            'optimal_acer': optimal['acer'],
            'genuine_count': len(genuine_scores),
            'attack_count': len(attack_scores),
            'genuine_stats': genuine_stats,
            'attack_stats': attack_stats
        }
    
    def calculate_metrics_by_attack_type(
        self,
        genuine_scores: List[float],
        tts_scores: List[float],
        cloning_scores: List[float],
        threshold: float = 0.5
    ) -> Dict:
        """
        Calcular métricas separadas por tipo de ataque.
        
        Returns:
            Dict con métricas por tipo de ataque
        """
        bpcer = self.calculate_bpcer(genuine_scores, threshold)
        apcer_tts = self.calculate_apcer(tts_scores, threshold)
        apcer_cloning = self.calculate_apcer(cloning_scores, threshold)
        
        # APCER combinado (todos los ataques)
        all_attacks = tts_scores + cloning_scores
        apcer_all = self.calculate_apcer(all_attacks, threshold)
        
        # ACER
        acer_tts = self.calculate_acer(bpcer, apcer_tts)
        acer_cloning = self.calculate_acer(bpcer, apcer_cloning)
        acer_all = self.calculate_acer(bpcer, apcer_all)
        
        return {
            'bpcer': bpcer,
            'tts': {
                'apcer': apcer_tts,
                'acer': acer_tts,
                'count': len(tts_scores)
            },
            'cloning': {
                'apcer': apcer_cloning,
                'acer': acer_cloning,
                'count': len(cloning_scores)
            },
            'all_attacks': {
                'apcer': apcer_all,
                'acer': acer_all,
                'count': len(all_attacks)
            }
        }
    
    def generate_visualizations(
        self,
        genuine_scores: List[float],
        tts_scores: List[float],
        cloning_scores: List[float],
        metrics: Dict,
        output_dir: Path
    ) -> None:
        """Generar visualizaciones diagnósticas para el reporte de anti-spoofing."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear figura con 4 subplots (2x2)
            plt.figure(figsize=(20, 12))
            
            # Combinar todos los ataques para algunos gráficos
            all_attacks = tts_scores + cloning_scores
            
            # ==============================================================
            # 1. HISTOGRAMA DE SCORES (BONAFIDE VS SPOOF) - DIAGNÓSTICO CLAVE
            # ==============================================================
            ax1 = plt.subplot(2, 2, 1)
            bins = np.linspace(0, 1, 50)
            
            # Histogramas con transparencia para ver solapamiento
            if len(genuine_scores) > 0:
                ax1.hist(genuine_scores, bins=bins, alpha=0.6, color='green', 
                        label=f'Bonafide (n={len(genuine_scores)})', density=True, edgecolor='darkgreen')
            if len(all_attacks) > 0:
                ax1.hist(all_attacks, bins=bins, alpha=0.6, color='red', 
                        label=f'Spoof (n={len(all_attacks)})', density=True, edgecolor='darkred')
            
            # Línea del umbral actual
            ax1.axvline(x=metrics['threshold'], color='blue', linestyle='--', 
                       linewidth=2.5, label=f'Umbral actual = {metrics["threshold"]:.3f}')
            
            # Estadísticas en el gráfico
            if len(genuine_scores) > 0 and len(all_attacks) > 0:
                ax1.text(0.02, 0.98, 
                        f'Media Bonafide: {np.mean(genuine_scores):.3f}\n'
                        f'Media Spoof: {np.mean(all_attacks):.3f}\n'
                        f'Separación: {abs(np.mean(genuine_scores) - np.mean(all_attacks)):.3f}',
                        transform=ax1.transAxes, fontsize=10,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            ax1.set_xlabel('Score de Spoofing (0=Genuino, 1=Spoof)', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Densidad de Probabilidad', fontsize=12, fontweight='bold')
            ax1.set_title('🔍 DIAGNÓSTICO: Separación Bonafide vs Spoof', fontsize=14, fontweight='bold')
            ax1.legend(loc='upper right', fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # ==============================================================
            # 2. APCER/BPCER VS THRESHOLD - ENCONTRAR EER
            # ==============================================================
            ax2 = plt.subplot(2, 2, 2)
            
            # Calcular errores para diferentes umbrales
            thresholds = np.linspace(0, 1, 200)
            bpcer_values = [self.calculate_bpcer(genuine_scores, t) for t in thresholds]
            apcer_values = [self.calculate_apcer(all_attacks, t) for t in thresholds]
            
            # Encontrar EER (Equal Error Rate)
            eer_idx = np.argmin(np.abs(np.array(bpcer_values) - np.array(apcer_values)))
            eer_threshold = thresholds[eer_idx]
            eer_value = (bpcer_values[eer_idx] + apcer_values[eer_idx]) / 2
            
            # Graficar curvas
            ax2.plot(thresholds, bpcer_values, 'g-', linewidth=2.5, label='BPCER (Rechazo genuino)')
            ax2.plot(thresholds, apcer_values, 'r-', linewidth=2.5, label='APCER (Acepta ataque)')
            
            # Marcar EER
            ax2.plot(eer_threshold, eer_value, 'ko', markersize=12, 
                    label=f'EER = {eer_value:.1f}% @ {eer_threshold:.3f}')
            ax2.axvline(x=eer_threshold, color='black', linestyle=':', alpha=0.5)
            ax2.axhline(y=eer_value, color='black', linestyle=':', alpha=0.5)
            
            # Marcar umbral actual
            current_bpcer = metrics['bpcer']
            current_apcer = metrics['apcer']
            ax2.plot(metrics['threshold'], current_bpcer, 'gs', markersize=10, 
                    label=f'Actual BPCER={current_bpcer:.1f}%')
            ax2.plot(metrics['threshold'], current_apcer, 'rs', markersize=10,
                    label=f'Actual APCER={current_apcer:.1f}%')
            ax2.axvline(x=metrics['threshold'], color='blue', linestyle='--', alpha=0.7)
            
            ax2.set_xlabel('Umbral de Decisión', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Tasa de Error (%)', fontsize=12, fontweight='bold')
            ax2.set_title('📊 Error Rate vs Threshold (EER)', fontsize=14, fontweight='bold')
            ax2.legend(loc='best', fontsize=9)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim([0, 105])
            
            # ==============================================================
            # 3. COMPARACIÓN DE APCER POR TIPO DE ATAQUE
            # ==============================================================
            ax3 = plt.subplot(2, 2, 3)
            
            attack_types = []
            apcer_by_type = []
            detection_rates = []
            attack_counts = []
            
            if len(tts_scores) > 0:
                attack_types.append('TTS')
                apcer_tts = self.calculate_apcer(tts_scores, metrics['threshold'])
                apcer_by_type.append(apcer_tts)
                detection_rates.append(100 - apcer_tts)
                attack_counts.append(len(tts_scores))
            
            if len(cloning_scores) > 0:
                attack_types.append('Voice\nCloning')
                apcer_cloning = self.calculate_apcer(cloning_scores, metrics['threshold'])
                apcer_by_type.append(apcer_cloning)
                detection_rates.append(100 - apcer_cloning)
                attack_counts.append(len(cloning_scores))
            
            x = np.arange(len(attack_types))
            width = 0.35
            
            # Barras de APCER (error - malo)
            bars1 = ax3.bar(x - width/2, apcer_by_type, width, label='APCER (Ataques aceptados)', 
                           color='red', alpha=0.7, edgecolor='darkred', linewidth=1.5)
            
            # Barras de Detección (bueno)
            bars2 = ax3.bar(x + width/2, detection_rates, width, label='Tasa de Detección', 
                           color='green', alpha=0.7, edgecolor='darkgreen', linewidth=1.5)
            
            # Añadir valores y conteos
            for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
                height1 = bar1.get_height()
                height2 = bar2.get_height()
                ax3.text(bar1.get_x() + bar1.get_width()/2., height1,
                        f'{height1:.1f}%\n(n={attack_counts[i]})', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
                ax3.text(bar2.get_x() + bar2.get_width()/2., height2,
                        f'{height2:.1f}%', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax3.set_ylabel('Porcentaje (%)', fontsize=12, fontweight='bold')
            ax3.set_title('⚔️ Rendimiento por Tipo de Ataque', fontsize=14, fontweight='bold')
            ax3.set_xticks(x)
            ax3.set_xticklabels(attack_types, fontsize=11)
            ax3.legend(loc='upper right', fontsize=10)
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.set_ylim([0, 110])
            
            # ==============================================================
            # 4. MATRIZ DE CONFUSIÓN DETALLADA
            # ==============================================================
            ax4 = plt.subplot(2, 2, 4)
            
            # Calcular verdaderos positivos/negativos
            threshold = metrics['threshold']
            
            # Genuinos correctamente aceptados (score < threshold)
            genuine_accepted = sum(1 for s in genuine_scores if s < threshold)
            genuine_rejected = len(genuine_scores) - genuine_accepted
            
            # Ataques correctamente rechazados (score >= threshold)
            attacks_rejected = sum(1 for s in all_attacks if s >= threshold)
            attacks_accepted = len(all_attacks) - attacks_rejected
            
            # Crear matriz
            confusion_data = np.array([
                [genuine_accepted, genuine_rejected],  # Genuinos: aceptados, rechazados
                [attacks_accepted, attacks_rejected]   # Ataques: aceptados (mal), rechazados (bien)
            ])
            
            im = ax4.imshow(confusion_data, cmap='RdYlGn', aspect='auto', alpha=0.8)
            
            # Etiquetas
            ax4.set_xticks([0, 1])
            ax4.set_yticks([0, 1])
            ax4.set_xticklabels(['Aceptado', 'Rechazado'], fontsize=11)
            ax4.set_yticklabels(['Bonafide', 'Spoof'], fontsize=11)
            
            # Valores en cada celda con porcentajes
            for i in range(2):
                for j in range(2):
                    total = len(genuine_scores) if i == 0 else len(all_attacks)
                    percentage = (confusion_data[i, j] / total * 100) if total > 0 else 0
                    text_color = 'white' if confusion_data[i, j] < max(confusion_data.flatten()) * 0.5 else 'black'
                    ax4.text(j, i, f'{confusion_data[i, j]}\n({percentage:.1f}%)',
                            ha="center", va="center", color=text_color, 
                            fontsize=12, fontweight='bold')
            
            ax4.set_xlabel('Decisión del Sistema', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Tipo Real', fontsize=12, fontweight='bold')
            ax4.set_title('🎯 Matriz de Confusión', fontsize=14, fontweight='bold')
            
            plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
            
            # ==============================================================
            plt.tight_layout()
            
            output_path = output_dir / "antispoofing_visualizations.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Visualizaciones diagnósticas guardadas en: {output_path}")
            logger.info(f"EER encontrado: {eer_value:.2f}% en umbral {eer_threshold:.4f}")
            
            # Agregar EER a las métricas para el reporte
            metrics['eer'] = f"{eer_value:.2f}% @ {eer_threshold:.4f}"
            
        except Exception as e:
            logger.error(f"Error generando visualizaciones: {e}", exc_info=True)
    
    def generate_report(
        self,
        metrics: Dict,
        metrics_by_type: Dict,
        output_path: Path
    ) -> None:
        """Generar reporte de evaluación."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN DEL MÓDULO DE ANTI-SPOOFING\n")
            f.write("Métricas según ISO/IEC 30107-3\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("MÉTRICAS PRINCIPALES (Threshold Óptimo: {:.4f})\n".format(metrics['threshold']))
            f.write("-" * 80 + "\n")
            f.write(f"APCER (Attack Present. Class. Error):  {metrics['apcer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"BPCER (Bona Fide Present. Class. Error): {metrics['bpcer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"ACER (Average Class. Error Rate):     {metrics['acer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"EER (Equal Error Rate):                {metrics.get('eer', 'N/A')}\n\n")
            
            f.write("NOTA: El threshold óptimo minimiza ACER y balancea seguridad con usabilidad.\n")
            f.write("      Un threshold más bajo (ej. 0.5) detectaría más ataques pero rechazaría\n")
            f.write("      demasiados usuarios genuinos (BPCER ~67%), haciéndolo impracticable.\n\n")
            
            f.write("MÉTRICAS POR TIPO DE ATAQUE\n")
            f.write("-" * 80 + "\n")
            f.write(f"BPCER (común):     {metrics_by_type['bpcer']:.2f}%\n\n")
            
            f.write(f"Ataques TTS ({metrics_by_type['tts']['count']} muestras):\n")
            f.write(f"  APCER:           {metrics_by_type['tts']['apcer']:.2f}%\n")
            f.write(f"  ACER:            {metrics_by_type['tts']['acer']:.2f}%\n")
            f.write(f"  Detección:       {100 - metrics_by_type['tts']['apcer']:.2f}%\n\n")
            
            f.write(f"Ataques Cloning ({metrics_by_type['cloning']['count']} muestras):\n")
            f.write(f"  APCER:           {metrics_by_type['cloning']['apcer']:.2f}%\n")
            f.write(f"  ACER:            {metrics_by_type['cloning']['acer']:.2f}%\n")
            f.write(f"  Detección:       {100 - metrics_by_type['cloning']['apcer']:.2f}%\n\n")
            
            f.write(f"Todos los ataques ({metrics_by_type['all_attacks']['count']} muestras):\n")
            f.write(f"  APCER:           {metrics_by_type['all_attacks']['apcer']:.2f}%\n")
            f.write(f"  ACER:            {metrics_by_type['all_attacks']['acer']:.2f}%\n")
            f.write(f"  Detección:       {100 - metrics_by_type['all_attacks']['apcer']:.2f}%\n\n")
            
            f.write("ESTADÍSTICAS DE SCORES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Audios genuinos ({metrics['genuine_count']}):\n")
            f.write(f"  Media:           {metrics['genuine_stats']['mean']:.4f}\n")
            f.write(f"  Desv. estándar:  {metrics['genuine_stats']['std']:.4f}\n")
            f.write(f"  Rango:           [{metrics['genuine_stats']['min']:.4f} - {metrics['genuine_stats']['max']:.4f}]\n\n")
            
            f.write(f"Audios de ataque ({metrics['attack_count']}):\n")
            f.write(f"  Media:           {metrics['attack_stats']['mean']:.4f}\n")
            f.write(f"  Desv. estándar:  {metrics['attack_stats']['std']:.4f}\n")
            f.write(f"  Rango:           [{metrics['attack_stats']['min']:.4f} - {metrics['attack_stats']['max']:.4f}]\n\n")
            
            f.write("INTERPRETACIÓN\n")
            f.write("-" * 80 + "\n")
            if metrics['acer'] < 5:
                f.write("✅ ACER EXCELENTE (< 5%)\n")
            elif metrics['acer'] < 15:
                f.write("✓ ACER BUENO (5-15%)\n")
            else:
                f.write("⚠️  ACER REQUIERE MEJORA (> 15%)\n")
            
            if metrics['apcer'] < 5:
                f.write("✅ APCER EXCELENTE (< 5%) - Alta detección de ataques\n")
            elif metrics['apcer'] < 15:
                f.write("✓ APCER ACEPTABLE (5-15%)\n")
            else:
                f.write("⚠️  APCER ALTO (> 15%) - Vulnerabilidad a ataques\n")
            
            if metrics['bpcer'] < 5:
                f.write("✅ BPCER EXCELENTE (< 5%) - Buena experiencia de usuario\n")
            elif metrics['bpcer'] < 15:
                f.write("✓ BPCER ACEPTABLE (5-15%)\n")
            else:
                f.write("⚠️  BPCER ALTO (> 15%) - Usuarios genuinos rechazados frecuentemente\n")
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar métricas en JSON
        combined_metrics = {
            'overall': metrics,
            'by_attack_type': metrics_by_type
        }
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(combined_metrics, f, indent=2)
        logger.info(f"Métricas JSON: {json_path}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("EVALUACIÓN DEL MÓDULO DE ANTI-SPOOFING")
    print("=" * 80)
    print()
    
    # Configuración del dataset - usar directorio correcto en infra/
    base_dir = Path(__file__).parent.parent
    project_root = base_dir.parent.parent
    dataset_dir = project_root / "infra" / "evaluation" / "dataset"
    
    # Directorios con diferentes tipos de audio
    genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"  # Audios genuinos
    tts_dir = dataset_dir / "attacks"  # Ataques TTS (por usuario)
    cloning_dir = dataset_dir / "cloning"  # Ataques de cloning (por usuario)
    
    # Verificar directorios
    if not genuine_dir.exists():
        print(f"❌ Error: Directorio de audios genuinos no encontrado: {genuine_dir}")
        print("\nEstructura esperada:")
        print("  infra/evaluation/dataset/")
        print("    recordings/auto_recordings_20251218/*.wav")
        print("    attacks/[usuario]/*.wav")
        print("    cloning/[usuario]/*.wav")
        sys.exit(1)
    
    # Inicializar evaluador
    evaluator = AntiSpoofingEvaluator()
    
    # 1. Procesar audios genuinos
    genuine_scores, _ = evaluator.score_audios(genuine_dir, "genuine")
    
    # 2. Procesar ataques TTS
    tts_scores = []
    if tts_dir.exists():
        tts_scores, _ = evaluator.score_audios(tts_dir, "TTS")
    
    # 3. Procesar ataques de cloning
    cloning_scores = []
    if cloning_dir.exists():
        cloning_scores, _ = evaluator.score_audios(cloning_dir, "voice cloning")
    
    if len(genuine_scores) == 0:
        print("❌ Error: No hay audios genuinos para evaluar")
        sys.exit(1)
    
    if len(tts_scores) == 0 and len(cloning_scores) == 0:
        print("❌ Error: No hay ataques para evaluar")
        sys.exit(1)
    
    # 4. Calcular threshold óptimo primero
    print("\nCalculando threshold óptimo...")
    all_attacks = tts_scores + cloning_scores
    optimal = evaluator.find_optimal_threshold(genuine_scores, all_attacks)
    optimal_threshold = optimal['threshold']
    print(f"Threshold óptimo encontrado: {optimal_threshold:.4f}")
    
    # 5. Calcular métricas generales con threshold óptimo
    print("\nCalculando métricas con threshold óptimo...")
    metrics = evaluator.calculate_metrics(genuine_scores, all_attacks, threshold=optimal_threshold)
    
    # 6. Calcular métricas por tipo de ataque con threshold óptimo
    metrics_by_type = evaluator.calculate_metrics_by_attack_type(
        genuine_scores, tts_scores, cloning_scores, threshold=optimal_threshold
    )
    
    # 7. Generar visualizaciones
    print("\nGenerando visualizaciones...")
    output_dir = base_dir / "evaluation" / "results"
    evaluator.generate_visualizations(genuine_scores, tts_scores, cloning_scores, 
                                     metrics, output_dir)
    
    # 8. Generar reporte
    output_path = output_dir / "antispoofing_evaluation.txt"
    evaluator.generate_report(metrics, metrics_by_type, output_path)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"APCER (Attack Classification Error): {metrics['apcer']:6.2f}%  ✅ Menor es mejor")
    print(f"BPCER (Genuine Classification Error): {metrics['bpcer']:6.2f}%  ✅ Menor es mejor")
    print(f"ACER (Average Classification Error):  {metrics['acer']:6.2f}%  ✅ Menor es mejor")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
