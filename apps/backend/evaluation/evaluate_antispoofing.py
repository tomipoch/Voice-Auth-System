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
        Obtener scores de spoof para audios.
        
        Args:
            audio_dir: Directorio con archivos de audio
            label: Etiqueta para logging (e.g., 'genuine', 'tts', 'cloning')
        
        Returns:
            Tuple de (lista de scores, total procesados)
        """
        logger.info(f"Procesando audios {label}...")
        
        audio_files = list(audio_dir.glob("*.wav"))
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
            
            f.write("MÉTRICAS PRINCIPALES (Todos los ataques)\n")
            f.write("-" * 80 + "\n")
            f.write(f"APCER (Attack Present. Class. Error):  {metrics['apcer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"BPCER (Bona Fide Present. Class. Error): {metrics['bpcer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"ACER (Average Class. Error Rate):     {metrics['acer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"Umbral operacional:                    {metrics['threshold']:.4f}\n\n")
            
            f.write("UMBRAL ÓPTIMO (Minimiza ACER)\n")
            f.write("-" * 80 + "\n")
            f.write(f"Umbral óptimo:     {metrics['optimal_threshold']:.4f}\n")
            f.write(f"BPCER óptimo:      {metrics['optimal_bpcer']:.2f}%\n")
            f.write(f"APCER óptimo:      {metrics['optimal_apcer']:.2f}%\n")
            f.write(f"ACER óptimo:       {metrics['optimal_acer']:.2f}%\n\n")
            
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
    
    # Configuración del dataset
    base_dir = Path(__file__).parent.parent
    dataset_dir = base_dir / "evaluation" / "dataset" / "antispoofing"
    
    genuine_dir = dataset_dir / "genuine"
    tts_dir = dataset_dir / "tts"
    cloning_dir = dataset_dir / "cloning"
    
    # Verificar directorios
    if not genuine_dir.exists():
        print(f"❌ Error: Directorio de audios genuinos no encontrado: {genuine_dir}")
        print("\nEstructura esperada:")
        print("  evaluation/dataset/antispoofing/")
        print("    genuine/audio1.wav, audio2.wav, ...")
        print("    tts/audio1.wav, audio2.wav, ...")
        print("    cloning/audio1.wav, audio2.wav, ...")
        sys.exit(1)
    
    # Inicializar evaluador
    evaluator = AntiSpoofingEvaluator()
    
    # 1. Procesar audios genuinos
    genuine_scores, genuine_count = evaluator.score_audios(genuine_dir, "genuine")
    
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
    
    # 4. Calcular métricas generales
    print("\nCalculando métricas...")
    all_attacks = tts_scores + cloning_scores
    metrics = evaluator.calculate_metrics(genuine_scores, all_attacks)
    
    # 5. Calcular métricas por tipo de ataque
    metrics_by_type = evaluator.calculate_metrics_by_attack_type(
        genuine_scores, tts_scores, cloning_scores
    )
    
    # 6. Generar reporte
    output_path = base_dir / "evaluation" / "results" / "antispoofing_evaluation.txt"
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
