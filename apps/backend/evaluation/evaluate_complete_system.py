"""
Evaluación del Sistema Completo (Métricas de Integración)

Métricas calculadas:

1. EFICIENCIA:
   - RTF (Real-Time Factor): Tiempo de procesamiento / Duración del audio (menor es mejor, óptimo ~0)
   - TTP (Total Processing Time): Tiempo total de procesamiento en segundos (~2 segundos es bueno)

2. ROBUSTEZ:
   - SNR vs Error: Sensibilidad al ruido (error debe ser bajo incluso con SNR bajo)
   - Sensibilidad a Duración: EER vs Duración del audio (cuánto afecta audio corto al rendimiento)

3. CALIBRACIÓN:
   - t-DCF (tandem Detection Cost Function): Costo de detección (menor es mejor, óptimo ~0%)

Uso:
    python evaluation/evaluate_complete_system.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import json
import time
import librosa

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
from src.infrastructure.biometrics.ASRAdapter import ASRAdapter

logger = logging.getLogger(__name__)


class CompleteSystemEvaluator:
    """Evaluador del sistema completo."""
    
    def __init__(self):
        self.speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
        self.spoof_detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
        self.asr_adapter = ASRAdapter(use_gpu=True)
    
    def load_audio(self, audio_path: Path) -> Tuple[bytes, float]:
        """
        Cargar archivo de audio.
        
        Returns:
            Tuple de (audio_data, duration_seconds)
        """
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Obtener duración usando librosa
        y, sr = librosa.load(audio_path, sr=None)
        duration = len(y) / sr
        
        return audio_data, duration
    
    def calculate_snr(self, audio_path: Path) -> float:
        """
        Calcular Signal-to-Noise Ratio (SNR) del audio.
        
        Returns:
            SNR en dB
        """
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Detección de actividad de voz simple basada en energía
        energy = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        threshold = np.median(energy) * 1.5
        
        # Frames de voz vs ruido
        voice_frames = energy > threshold
        noise_frames = ~voice_frames
        
        if not np.any(noise_frames):
            return 40.0  # SNR muy alto si no hay ruido detectable
        
        # Calcular potencia de señal y ruido
        signal_power = np.mean(energy[voice_frames] ** 2)
        noise_power = np.mean(energy[noise_frames] ** 2)
        
        if noise_power < 1e-10:
            return 40.0
        
        snr_db = 10 * np.log10(signal_power / noise_power)
        return float(snr_db)
    
    def evaluate_efficiency(self, test_audios_dir: Path) -> Dict:
        """
        Evaluar eficiencia del sistema (RTF y TTP).
        
        Args:
            test_audios_dir: Directorio con audios de prueba
        
        Returns:
            Dict con métricas de eficiencia
        """
        logger.info("Evaluando eficiencia del sistema...")
        
        audio_files = list(test_audios_dir.glob("*.wav"))[:50]  # Limitar a 50 audios
        
        rtf_values = []
        ttp_values = []
        
        for audio_path in audio_files:
            try:
                audio_data, duration = self.load_audio(audio_path)
                
                # Medir tiempo de procesamiento total
                start_time = time.time()
                
                # Procesar con los 3 módulos
                embedding = self.speaker_adapter.extract_embedding(audio_data)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                transcription = self.asr_adapter.transcribe(audio_data)
                
                processing_time = time.time() - start_time
                
                # Calcular RTF
                rtf = processing_time / duration if duration > 0 else 0
                rtf_values.append(rtf)
                ttp_values.append(processing_time)
                
            except Exception as e:
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        return {
            'rtf_mean': float(np.mean(rtf_values)),
            'rtf_std': float(np.std(rtf_values)),
            'rtf_min': float(np.min(rtf_values)),
            'rtf_max': float(np.max(rtf_values)),
            'ttp_mean': float(np.mean(ttp_values)),
            'ttp_std': float(np.std(ttp_values)),
            'ttp_min': float(np.min(ttp_values)),
            'ttp_max': float(np.max(ttp_values)),
            'samples_tested': len(rtf_values)
        }
    
    def evaluate_snr_robustness(
        self,
        genuine_dir: Path,
        voiceprint: np.ndarray,
        threshold: float = 0.65
    ) -> Dict:
        """
        Evaluar robustez del sistema ante diferentes niveles de SNR.
        
        Mide cómo el error de verificación aumenta con ruido.
        
        Returns:
            Dict con métricas de robustez a SNR
        """
        logger.info("Evaluando robustez a SNR...")
        
        audio_files = list(genuine_dir.glob("*.wav"))
        
        # Agrupar por rangos de SNR
        snr_groups = {
            'high': {'range': (20, 100), 'errors': 0, 'total': 0, 'snr_values': []},
            'medium': {'range': (10, 20), 'errors': 0, 'total': 0, 'snr_values': []},
            'low': {'range': (0, 10), 'errors': 0, 'total': 0, 'snr_values': []}
        }
        
        for audio_path in audio_files:
            try:
                # Calcular SNR
                snr = self.calculate_snr(audio_path)
                
                # Verificar
                audio_data, _ = self.load_audio(audio_path)
                embedding = self.speaker_adapter.extract_embedding(audio_data)
                similarity = self._calculate_similarity(voiceprint, embedding)
                
                # Determinar error (si es genuino pero rechazado)
                is_error = similarity < threshold
                
                # Clasificar en grupo de SNR
                for group_name, group_data in snr_groups.items():
                    snr_min, snr_max = group_data['range']
                    if snr_min <= snr < snr_max:
                        group_data['total'] += 1
                        group_data['snr_values'].append(snr)
                        if is_error:
                            group_data['errors'] += 1
                        break
                
            except Exception as e:
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        # Calcular tasas de error por grupo
        results = {}
        for group_name, group_data in snr_groups.items():
            error_rate = (group_data['errors'] / group_data['total'] * 100) if group_data['total'] > 0 else 0.0
            avg_snr = np.mean(group_data['snr_values']) if group_data['snr_values'] else 0.0
            
            results[group_name] = {
                'error_rate': error_rate,
                'total_samples': group_data['total'],
                'avg_snr': float(avg_snr),
                'snr_range': group_data['range']
            }
        
        return results
    
    def evaluate_duration_sensitivity(
        self,
        test_audios_dir: Path,
        genuine_voiceprint: np.ndarray
    ) -> Dict:
        """
        Evaluar sensibilidad del anti-spoofing a la duración del audio.
        
        Pregunta: ¿Qué tan corto puede ser el audio antes de perder precisión?
        
        Returns:
            Dict con métricas de sensibilidad a duración
        """
        logger.info("Evaluando sensibilidad a duración del audio...")
        
        audio_files = list(test_audios_dir.glob("*.wav"))
        
        # Agrupar por duración
        duration_groups = {
            'very_short': {'range': (0, 2), 'genuine_scores': [], 'spoof_scores': []},
            'short': {'range': (2, 4), 'genuine_scores': [], 'spoof_scores': []},
            'medium': {'range': (4, 6), 'genuine_scores': [], 'spoof_scores': []},
            'long': {'range': (6, 100), 'genuine_scores': [], 'spoof_scores': []}
        }
        
        for audio_path in audio_files:
            try:
                audio_data, duration = self.load_audio(audio_path)
                
                # Determinar si es genuino o spoof por nombre de archivo
                is_genuine = 'genuine' in str(audio_path).lower()
                
                # Obtener score de anti-spoofing
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                
                # Clasificar en grupo de duración
                for group_name, group_data in duration_groups.items():
                    dur_min, dur_max = group_data['range']
                    if dur_min <= duration < dur_max:
                        if is_genuine:
                            group_data['genuine_scores'].append(spoof_score)
                        else:
                            group_data['spoof_scores'].append(spoof_score)
                        break
                
            except Exception as e:
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        # Calcular EER por grupo de duración
        results = {}
        for group_name, group_data in duration_groups.items():
            genuine_scores = np.array(group_data['genuine_scores'])
            spoof_scores = np.array(group_data['spoof_scores'])
            
            if len(genuine_scores) > 0 and len(spoof_scores) > 0:
                eer = self._calculate_eer(genuine_scores, spoof_scores)
                results[group_name] = {
                    'eer': eer,
                    'genuine_count': len(genuine_scores),
                    'spoof_count': len(spoof_scores),
                    'duration_range': group_data['range']
                }
            else:
                results[group_name] = {
                    'eer': None,
                    'genuine_count': len(genuine_scores),
                    'spoof_count': len(spoof_scores),
                    'duration_range': group_data['range']
                }
        
        return results
    
    def calculate_t_dcf(
        self,
        genuine_scores: List[float],
        spoof_scores: List[float],
        threshold: float = 0.5,
        c_miss: float = 1.0,
        c_fa: float = 10.0,
        p_target: float = 0.05
    ) -> float:
        """
        Calcular t-DCF (tandem Detection Cost Function).
        
        Métrica estándar de ASVspoof que considera costos de errores.
        
        Args:
            genuine_scores: Scores de spoof para genuinos (menor = genuino)
            spoof_scores: Scores de spoof para ataques (mayor = ataque)
            threshold: Umbral de decisión
            c_miss: Costo de perder un ataque (default: 1)
            c_fa: Costo de falsa alarma (default: 10)
            p_target: Prior de ataques (default: 0.05)
        
        Returns:
            t-DCF normalizado (0-1, menor es mejor)
        """
        genuine_scores = np.array(genuine_scores)
        spoof_scores = np.array(spoof_scores)
        
        # BPCER: genuinos rechazados (score >= threshold)
        bpcer = np.sum(genuine_scores >= threshold) / len(genuine_scores) if len(genuine_scores) > 0 else 0
        
        # APCER: ataques aceptados (score < threshold)
        apcer = np.sum(spoof_scores < threshold) / len(spoof_scores) if len(spoof_scores) > 0 else 0
        
        # Calcular t-DCF
        t_dcf = c_miss * bpcer * p_target + c_fa * apcer * (1 - p_target)
        
        # Normalizar por el peor caso
        t_dcf_norm = t_dcf / min(c_miss * p_target, c_fa * (1 - p_target))
        
        return float(t_dcf_norm)
    
    def _calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno."""
        norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        similarity = np.dot(norm1, norm2)
        return float(max(0.0, min(1.0, similarity)))
    
    def _calculate_eer(self, genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
        """Calcular Equal Error Rate."""
        thresholds = np.linspace(0, 1, 500)
        fars = []
        frrs = []
        
        for t in thresholds:
            far = np.sum(impostor_scores >= t) / len(impostor_scores)
            frr = np.sum(genuine_scores < t) / len(genuine_scores)
            fars.append(far)
            frrs.append(frr)
        
        fars = np.array(fars)
        frrs = np.array(frrs)
        diff = np.abs(fars - frrs)
        eer_idx = np.argmin(diff)
        eer = ((fars[eer_idx] + frrs[eer_idx]) / 2) * 100
        
        return float(eer)
    
    def generate_report(
        self,
        efficiency_metrics: Dict,
        snr_robustness: Dict,
        duration_sensitivity: Dict,
        t_dcf_value: float,
        output_path: Path
    ) -> None:
        """Generar reporte de evaluación del sistema completo."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN DEL SISTEMA COMPLETO\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 1. EFICIENCIA
            f.write("1. EFICIENCIA\n")
            f.write("-" * 80 + "\n")
            f.write(f"RTF (Real-Time Factor):\n")
            f.write(f"  Promedio:        {efficiency_metrics['rtf_mean']:.4f}  ")
            f.write("✅ MEJOR si cercano a 0\n")
            f.write(f"  Desv. estándar:  {efficiency_metrics['rtf_std']:.4f}\n")
            f.write(f"  Rango:           [{efficiency_metrics['rtf_min']:.4f} - {efficiency_metrics['rtf_max']:.4f}]\n\n")
            
            f.write(f"TTP (Total Processing Time):\n")
            f.write(f"  Promedio:        {efficiency_metrics['ttp_mean']:.2f} seg  ")
            f.write("✅ ~2 segundos es BUENO\n")
            f.write(f"  Desv. estándar:  {efficiency_metrics['ttp_std']:.2f} seg\n")
            f.write(f"  Rango:           [{efficiency_metrics['ttp_min']:.2f} - {efficiency_metrics['ttp_max']:.2f}] seg\n")
            f.write(f"  Muestras:        {efficiency_metrics['samples_tested']}\n\n")
            
            # 2. ROBUSTEZ
            f.write("2. ROBUSTEZ\n")
            f.write("-" * 80 + "\n")
            f.write("SNR vs Error Rate:\n")
            for group_name, data in snr_robustness.items():
                f.write(f"  {group_name.upper()} SNR ({data['snr_range'][0]}-{data['snr_range'][1]} dB):\n")
                f.write(f"    SNR promedio:    {data['avg_snr']:.1f} dB\n")
                f.write(f"    Tasa de error:   {data['error_rate']:.2f}%\n")
                f.write(f"    Muestras:        {data['total_samples']}\n")
            f.write("\n")
            
            f.write("Sensibilidad a Duración (EER vs Duración de Audio):\n")
            for group_name, data in duration_sensitivity.items():
                dur_min, dur_max = data['duration_range']
                f.write(f"  {group_name.upper()} ({dur_min}-{dur_max} seg):\n")
                if data['eer'] is not None:
                    f.write(f"    EER:             {data['eer']:.2f}%\n")
                else:
                    f.write(f"    EER:             N/A (datos insuficientes)\n")
                f.write(f"    Genuinos:        {data['genuine_count']}\n")
                f.write(f"    Ataques:         {data['spoof_count']}\n")
            f.write("\n")
            
            # 3. CALIBRACIÓN
            f.write("3. CALIBRACIÓN\n")
            f.write("-" * 80 + "\n")
            f.write(f"t-DCF (tandem Detection Cost Function): {t_dcf_value:.4f}  ")
            f.write("✅ MEJOR si cercano a 0\n\n")
            
            # INTERPRETACIÓN
            f.write("INTERPRETACIÓN\n")
            f.write("-" * 80 + "\n")
            
            # RTF
            if efficiency_metrics['rtf_mean'] < 0.5:
                f.write("✅ RTF EXCELENTE (< 0.5) - Más rápido que tiempo real\n")
            elif efficiency_metrics['rtf_mean'] < 1.0:
                f.write("✓ RTF BUENO (0.5-1.0) - Cercano a tiempo real\n")
            else:
                f.write("⚠️  RTF REQUIERE MEJORA (> 1.0) - Más lento que tiempo real\n")
            
            # TTP
            if 1.5 <= efficiency_metrics['ttp_mean'] <= 3.0:
                f.write("✅ TTP ÓPTIMO (1.5-3.0 seg) - Buena experiencia de usuario\n")
            elif efficiency_metrics['ttp_mean'] < 1.5:
                f.write("✓ TTP EXCELENTE (< 1.5 seg) - Muy rápido\n")
            else:
                f.write("⚠️  TTP ALTO (> 3 seg) - Puede afectar experiencia de usuario\n")
            
            # t-DCF
            if t_dcf_value < 0.05:
                f.write("✅ t-DCF EXCELENTE (< 0.05)\n")
            elif t_dcf_value < 0.10:
                f.write("✓ t-DCF BUENO (0.05-0.10)\n")
            else:
                f.write("⚠️  t-DCF REQUIERE MEJORA (> 0.10)\n")
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar métricas en JSON
        combined_metrics = {
            'efficiency': efficiency_metrics,
            'snr_robustness': snr_robustness,
            'duration_sensitivity': duration_sensitivity,
            't_dcf': t_dcf_value
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
    print("EVALUACIÓN DEL SISTEMA COMPLETO")
    print("=" * 80)
    print()
    
    # Configuración del dataset
    base_dir = Path(__file__).parent.parent
    dataset_dir = base_dir / "evaluation" / "dataset" / "complete_system"
    
    efficiency_dir = dataset_dir / "efficiency_test"
    snr_robustness_dir = dataset_dir / "snr_robustness"
    duration_dir = dataset_dir / "duration_sensitivity"
    antispoofing_genuine = dataset_dir / "antispoofing" / "genuine"
    antispoofing_spoof = dataset_dir / "antispoofing" / "spoof"
    
    # Verificar directorios
    if not efficiency_dir.exists():
        print(f"❌ Error: Directorio de eficiencia no encontrado: {efficiency_dir}")
        print("\nEstructura esperada:")
        print("  evaluation/dataset/complete_system/")
        print("    efficiency_test/audio1.wav, audio2.wav, ...")
        print("    snr_robustness/genuine/audio1.wav, ...")
        print("    duration_sensitivity/genuine/*.wav, spoof/*.wav")
        print("    antispoofing/genuine/*.wav, spoof/*.wav")
        sys.exit(1)
    
    # Inicializar evaluador
    evaluator = CompleteSystemEvaluator()
    
    # 1. Evaluar eficiencia
    print("Evaluando eficiencia...")
    efficiency_metrics = evaluator.evaluate_efficiency(efficiency_dir)
    
    # 2. Evaluar robustez a SNR (necesita voiceprint de referencia)
    print("\nEvaluando robustez a SNR...")
    # Crear un voiceprint dummy para prueba
    dummy_voiceprint = np.random.randn(192).astype(np.float32)
    snr_robustness = evaluator.evaluate_snr_robustness(
        snr_robustness_dir, dummy_voiceprint
    ) if snr_robustness_dir.exists() else {}
    
    # 3. Evaluar sensibilidad a duración
    print("\nEvaluando sensibilidad a duración...")
    duration_sensitivity = evaluator.evaluate_duration_sensitivity(
        duration_dir, dummy_voiceprint
    ) if duration_dir.exists() else {}
    
    # 4. Calcular t-DCF
    print("\nCalculando t-DCF...")
    genuine_scores = []
    spoof_scores = []
    
    if antispoofing_genuine.exists() and antispoofing_spoof.exists():
        # Obtener scores de genuinos
        for audio_file in list(antispoofing_genuine.glob("*.wav"))[:50]:
            audio_data, _ = evaluator.load_audio(audio_file)
            score = evaluator.spoof_detector.detect_spoof(audio_data)
            genuine_scores.append(score)
        
        # Obtener scores de ataques
        for audio_file in list(antispoofing_spoof.glob("*.wav"))[:50]:
            audio_data, _ = evaluator.load_audio(audio_file)
            score = evaluator.spoof_detector.detect_spoof(audio_data)
            spoof_scores.append(score)
        
        t_dcf_value = evaluator.calculate_t_dcf(genuine_scores, spoof_scores)
    else:
        t_dcf_value = 0.0
        print("⚠️  No hay datos para calcular t-DCF")
    
    # 5. Generar reporte
    output_path = base_dir / "evaluation" / "results" / "complete_system_evaluation.txt"
    evaluator.generate_report(
        efficiency_metrics,
        snr_robustness,
        duration_sensitivity,
        t_dcf_value,
        output_path
    )
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"RTF (Real-Time Factor):      {efficiency_metrics['rtf_mean']:.4f}  ✅ Menor es mejor")
    print(f"TTP (Total Processing Time): {efficiency_metrics['ttp_mean']:.2f} seg  ✅ ~2 seg es bueno")
    print(f"t-DCF:                       {t_dcf_value:.4f}  ✅ Menor es mejor")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
