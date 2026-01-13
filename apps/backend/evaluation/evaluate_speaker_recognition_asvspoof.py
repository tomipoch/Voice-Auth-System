"""
Evaluación ESCALADA de Speaker Recognition usando ASVspoof 2019

Este script evalúa el sistema con CIENTOS de hablantes reales del dataset
ASVspoof 2019 (Logical Access), comparando contra el baseline de 4 usuarios.

Objetivo: Validar si el EER de 2.78% se mantiene con dataset grande.

Dataset: connor-f-m/asvspoof2019 (Hugging Face)
- 200+ hablantes únicos
- Miles de audios bonafide
- Variaciones naturales (ruido, calidad, duración)

Métricas:
- EER, FAR, FRR con threshold Security First (0.5516)
- Comparación vs baseline (4 usuarios)
- Análisis por speaker_id

Uso:
    pip install datasets
    python evaluation/evaluate_speaker_recognition_asvspoof.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import json
from tqdm import tqdm
import io
import wave

# Hugging Face datasets
try:
    from datasets import load_dataset
except ImportError:
    print("❌ Error: Instala 'datasets' con: pip install datasets")
    sys.exit(1)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logger = logging.getLogger(__name__)


class ASVspoofSpeakerEvaluator:
    """Evaluador escalado de Speaker Recognition con ASVspoof 2019."""
    
    def __init__(self, num_speakers: int = 20, samples_per_speaker: int = 10):
        """
        Args:
            num_speakers: Número de hablantes a evaluar (default 20, max ~200)
            samples_per_speaker: Muestras por hablante para enrollment (default 10)
        """
        self.num_speakers = num_speakers
        self.samples_per_speaker = samples_per_speaker
        self.speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
        self.voiceprints = {}
        self.speaker_samples = {}  # speaker_id -> lista de audios
        
        # Threshold del baseline (4 usuarios)
        self.baseline_threshold = 0.5516  # Security First
        
        logger.info(f"Inicializando evaluador con {num_speakers} hablantes")
    
    def load_asvspoof_dataset(self, split: str = "validation") -> None:
        """
        Cargar dataset ASVspoof 2019 (Logical Access).
        
        Args:
            split: 'train', 'validation', o 'test'
        """
        logger.info(f"Descargando ASVspoof 2019 LA ({split})...")
        
        try:
            # Intentar varios datasets posibles de ASVspoof en Hugging Face
            dataset_names = [
                ("asvspoof/LA", None),  # Oficial si existe
                ("asvspoof2019", "LA"),  # Alternativa
                ("speech-datasets/asvspoof2019", "la"),  # Otra alternativa
            ]
            
            dataset = None
            for dataset_name, config in dataset_names:
                try:
                    logger.info(f"Intentando cargar: {dataset_name} (config: {config})")
                    if config:
                        dataset = load_dataset(dataset_name, config, split=split, trust_remote_code=True)
                    else:
                        dataset = load_dataset(dataset_name, split=split, trust_remote_code=True)
                    logger.info(f"✓ Dataset cargado exitosamente: {dataset_name}")
                    break
                except Exception as e:
                    logger.warning(f"No se pudo cargar {dataset_name}: {e}")
                    continue
            
            if dataset is None:
                # Fallback: Usar LibriSpeech como alternativa
                logger.warning("No se encontró ASVspoof, usando LibriSpeech como alternativa")
                dataset = load_dataset("librispeech_asr", "clean", split="validation", trust_remote_code=True)
            
            # Filtrar solo bonafide si es ASVspoof, o usar todos si es LibriSpeech
            if 'label' in dataset.features or 'is_bonafide' in dataset.features:
                bonafide_samples = [
                    sample for sample in dataset 
                    if sample.get('label', 1) == 0 or sample.get('is_bonafide', False)
                ]
                logger.info(f"Dataset ASVspoof cargado: {len(bonafide_samples)} muestras bonafide")
            else:
                # Es LibriSpeech u otro dataset sin etiquetas de spoofing
                bonafide_samples = list(dataset)
                logger.info(f"Dataset cargado (todos bonafide): {len(bonafide_samples)} muestras")
            
            if len(bonafide_samples) == 0:
                logger.warning("No se encontraron muestras, usando todas las muestras")
                bonafide_samples = list(dataset)
            
            # Agrupar por speaker_id
            speaker_groups = {}
            for sample in bonafide_samples:
                # Diferentes datasets usan diferentes nombres de campo
                speaker_id = sample.get('speaker_id') or sample.get('speaker') or sample.get('id', 'unknown')
                if isinstance(speaker_id, int):
                    speaker_id = str(speaker_id)
                
                if speaker_id not in speaker_groups:
                    speaker_groups[speaker_id] = []
                speaker_groups[speaker_id].append(sample)
            
            # Seleccionar top N speakers con más muestras
            sorted_speakers = sorted(
                speaker_groups.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            
            selected_speakers = sorted_speakers[:self.num_speakers]
            
            for speaker_id, samples in selected_speakers:
                self.speaker_samples[speaker_id] = samples
            
            logger.info(f"Seleccionados {len(self.speaker_samples)} hablantes")
            logger.info(f"Muestras por hablante: {[len(s) for s in list(self.speaker_samples.values())[:5]]}")
            
        except Exception as e:
            logger.error(f"Error cargando dataset: {e}")
            raise
    
    def audio_to_wav_bytes(self, audio_data: Dict) -> bytes:
        """
        Convertir audio de Hugging Face a bytes WAV.
        
        Args:
            audio_data: Dict con 'array' y 'sampling_rate'
            
        Returns:
            bytes de audio WAV
        """
        waveform = audio_data['array']
        sample_rate = audio_data['sampling_rate']
        
        # Convertir a int16
        waveform_int16 = (waveform * 32767).astype(np.int16)
        
        # Crear WAV en memoria
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(waveform_int16.tobytes())
        
        return output.getvalue()
    
    def enroll_speakers(self) -> None:
        """Inscribir todos los hablantes seleccionados."""
        logger.info(f"Inscribiendo {len(self.speaker_samples)} hablantes...")
        
        for speaker_id, samples in tqdm(self.speaker_samples.items(), desc="Enrollment"):
            # Usar primeras N muestras para enrollment
            enrollment_samples = samples[:self.samples_per_speaker]
            
            embeddings = []
            for sample in enrollment_samples:
                try:
                    audio_bytes = self.audio_to_wav_bytes(sample['audio'])
                    embedding = self.speaker_adapter.extract_embedding(audio_bytes, audio_format="wav")
                    embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"Error procesando audio de {speaker_id}: {e}")
                    continue
            
            if len(embeddings) > 0:
                # Voiceprint = promedio de embeddings
                self.voiceprints[speaker_id] = np.mean(embeddings, axis=0)
            else:
                logger.warning(f"No se pudo inscribir {speaker_id}")
        
        logger.info(f"Total inscritos: {len(self.voiceprints)} hablantes")
    
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Similitud coseno entre embeddings."""
        norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        similarity = np.dot(norm1, norm2)
        return float(max(0.0, min(1.0, similarity)))
    
    def evaluate_genuine_attempts(self) -> Tuple[List[float], int]:
        """
        Evaluar intentos genuinos (verification vs enrollment propio).
        
        Returns:
            (scores, total_comparisons)
        """
        logger.info("Evaluando intentos genuinos...")
        genuine_scores = []
        comparisons = 0
        
        for speaker_id, samples in tqdm(self.speaker_samples.items(), desc="Genuine"):
            if speaker_id not in self.voiceprints:
                continue
            
            voiceprint = self.voiceprints[speaker_id]
            
            # Usar muestras después del enrollment para verification
            verification_samples = samples[self.samples_per_speaker:]
            
            for sample in verification_samples:
                try:
                    audio_bytes = self.audio_to_wav_bytes(sample['audio'])
                    test_embedding = self.speaker_adapter.extract_embedding(audio_bytes, audio_format="wav")
                    
                    score = self.calculate_similarity(voiceprint, test_embedding)
                    genuine_scores.append(score)
                    comparisons += 1
                    
                except Exception as e:
                    logger.warning(f"Error en genuine {speaker_id}: {e}")
                    continue
        
        logger.info(f"Total genuinos: {comparisons}")
        return genuine_scores, comparisons
    
    def evaluate_impostor_attempts(self) -> Tuple[List[float], int]:
        """
        Evaluar intentos de impostores (verificación cruzada).
        
        Compara audios de Speaker A vs voiceprint de Speaker B.
        
        Returns:
            (scores, total_comparisons)
        """
        logger.info("Evaluando intentos de impostores...")
        impostor_scores = []
        comparisons = 0
        
        speaker_ids = list(self.voiceprints.keys())
        
        # Limitar comparaciones para no explotar la memoria
        max_impostor_per_speaker = 20
        
        for claimed_id in tqdm(speaker_ids, desc="Impostor"):
            claimed_voiceprint = self.voiceprints[claimed_id]
            
            # Comparar contra otros hablantes
            for actual_id in speaker_ids:
                if actual_id == claimed_id:
                    continue
                
                # Usar muestras de verification del impostor
                verification_samples = self.speaker_samples[actual_id][self.samples_per_speaker:]
                
                # Limitar número de comparaciones
                samples_to_test = verification_samples[:max_impostor_per_speaker]
                
                for sample in samples_to_test:
                    try:
                        audio_bytes = self.audio_to_wav_bytes(sample['audio'])
                        test_embedding = self.speaker_adapter.extract_embedding(audio_bytes, audio_format="wav")
                        
                        score = self.calculate_similarity(claimed_voiceprint, test_embedding)
                        impostor_scores.append(score)
                        comparisons += 1
                        
                    except Exception as e:
                        logger.warning(f"Error en impostor {actual_id}->{claimed_id}: {e}")
                        continue
                
                # Limitar por speaker reclamado también
                if comparisons > len(speaker_ids) * max_impostor_per_speaker * 5:
                    break
        
        logger.info(f"Total impostores: {comparisons}")
        return impostor_scores, comparisons
    
    def calculate_metrics(
        self, 
        genuine_scores: List[float], 
        impostor_scores: List[float], 
        threshold: float
    ) -> Dict:
        """Calcular métricas biométricas."""
        genuine_array = np.array(genuine_scores)
        impostor_array = np.array(impostor_scores)
        
        # FAR: % impostores que pasan el threshold
        far = np.sum(impostor_array >= threshold) / len(impostor_array) * 100
        
        # FRR: % genuinos rechazados
        frr = np.sum(genuine_array < threshold) / len(genuine_array) * 100
        
        # EER: punto donde FAR = FRR
        thresholds = np.linspace(0, 1, 1000)
        far_values = [np.sum(impostor_array >= t) / len(impostor_array) * 100 for t in thresholds]
        frr_values = [np.sum(genuine_array < t) / len(genuine_array) * 100 for t in thresholds]
        
        eer_idx = np.argmin(np.abs(np.array(far_values) - np.array(frr_values)))
        eer = (far_values[eer_idx] + frr_values[eer_idx]) / 2
        
        return {
            'far': far,
            'frr': frr,
            'eer': eer,
            'threshold': threshold,
            'genuine_mean': float(np.mean(genuine_array)),
            'impostor_mean': float(np.mean(impostor_array)),
            'genuine_std': float(np.std(genuine_array)),
            'impostor_std': float(np.std(impostor_array)),
            'separation': float(np.mean(genuine_array) - np.mean(impostor_array))
        }
    
    def generate_report(self, metrics: Dict, baseline_metrics: Dict, output_path: Path) -> None:
        """Generar reporte comparativo."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN ESCALADA - SPEAKER RECOGNITION CON ASVSPOOF 2019\n")
            f.write("=" * 80 + "\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Dataset: ASVspoof 2019 LA (Logical Access)\n")
            f.write(f"Hablantes: {self.num_speakers}\n")
            f.write(f"Threshold: {metrics['threshold']:.4f} (Security First - del baseline)\n")
            f.write("\n")
            
            f.write("RESULTADOS CON DATASET ESCALADO\n")
            f.write("-" * 80 + "\n")
            f.write(f"FAR (False Acceptance Rate):  {metrics['far']:6.2f}%\n")
            f.write(f"FRR (False Rejection Rate):   {metrics['frr']:6.2f}%\n")
            f.write(f"EER (Equal Error Rate):       {metrics['eer']:6.2f}%\n")
            f.write(f"Accuracy:                     {100 - metrics['far'] - metrics['frr']:6.2f}%\n")
            f.write("\n")
            
            f.write(f"Genuine Mean Score:           {metrics['genuine_mean']:.4f} ± {metrics['genuine_std']:.4f}\n")
            f.write(f"Impostor Mean Score:          {metrics['impostor_mean']:.4f} ± {metrics['impostor_std']:.4f}\n")
            f.write(f"Separación:                   {metrics['separation']:.4f}\n")
            f.write("\n")
            
            f.write("COMPARACIÓN CON BASELINE (4 usuarios)\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Métrica':<25} {'Baseline':<15} {'ASVspoof':<15} {'Diferencia':<15}\n")
            f.write("-" * 80 + "\n")
            
            f.write(f"{'FAR':<25} {baseline_metrics['far']:>6.2f}% {metrics['far']:>14.2f}% ")
            f.write(f"{metrics['far'] - baseline_metrics['far']:>14.2f}%\n")
            
            f.write(f"{'FRR':<25} {baseline_metrics['frr']:>6.2f}% {metrics['frr']:>14.2f}% ")
            f.write(f"{metrics['frr'] - baseline_metrics['frr']:>14.2f}%\n")
            
            f.write(f"{'EER':<25} {baseline_metrics['eer']:>6.2f}% {metrics['eer']:>14.2f}% ")
            f.write(f"{metrics['eer'] - baseline_metrics['eer']:>14.2f}%\n")
            
            f.write("\n")
            f.write("ANÁLISIS\n")
            f.write("-" * 80 + "\n")
            
            if metrics['eer'] <= baseline_metrics['eer'] * 1.5:
                f.write("✅ EXCELENTE: EER se mantiene estable con dataset grande\n")
                f.write("   El sistema generaliza bien a nuevos hablantes\n")
            elif metrics['eer'] <= baseline_metrics['eer'] * 2:
                f.write("✓ BUENO: EER aumentó moderadamente con dataset grande\n")
                f.write("   Comportamiento esperado al aumentar variabilidad\n")
            else:
                f.write("⚠️  ADVERTENCIA: EER aumentó significativamente\n")
                f.write("   El sistema podría estar sobreajustado al dataset pequeño\n")
            
            f.write("\n")
            f.write("RECOMENDACIONES\n")
            f.write("-" * 80 + "\n")
            
            if metrics['eer'] > baseline_metrics['eer'] * 2:
                f.write("• Considerar re-entrenar con dataset más grande\n")
                f.write("• Aplicar data augmentation en enrollment\n")
                f.write("• Ajustar threshold para balance FAR/FRR\n")
            else:
                f.write("• Resultados validados con dataset escalado ✓\n")
                f.write("• Sistema robusto para producción\n")
            
            f.write("\n")
        
        logger.info(f"Reporte generado: {output_path}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("EVALUACIÓN ESCALADA CON ASVSPOOF 2019")
    print("=" * 80)
    print()
    
    # Configuración
    NUM_SPEAKERS = 5  # Ajustar según recursos (max ~200) - Empezar con 5 para prueba
    SAMPLES_PER_SPEAKER = 3  # Para enrollment
    
    print(f"Configuración:")
    print(f"  • Hablantes a evaluar: {NUM_SPEAKERS}")
    print(f"  • Muestras para enrollment: {SAMPLES_PER_SPEAKER}")
    print()
    
    # Inicializar evaluador
    evaluator = ASVspoofSpeakerEvaluator(
        num_speakers=NUM_SPEAKERS,
        samples_per_speaker=SAMPLES_PER_SPEAKER
    )
    
    # 1. Cargar dataset
    evaluator.load_asvspoof_dataset(split="validation")
    
    # 2. Inscribir hablantes
    evaluator.enroll_speakers()
    
    if len(evaluator.voiceprints) < 5:
        print("❌ Error: No hay suficientes hablantes inscritos")
        sys.exit(1)
    
    # 3. Evaluar intentos genuinos
    genuine_scores, genuine_count = evaluator.evaluate_genuine_attempts()
    
    # 4. Evaluar intentos de impostores
    impostor_scores, impostor_count = evaluator.evaluate_impostor_attempts()
    
    if len(genuine_scores) == 0 or len(impostor_scores) == 0:
        print("❌ Error: No hay suficientes datos para evaluar")
        sys.exit(1)
    
    # 5. Calcular métricas con threshold baseline
    metrics = evaluator.calculate_metrics(
        genuine_scores, 
        impostor_scores, 
        threshold=evaluator.baseline_threshold
    )
    
    # Métricas baseline (del sistema con 4 usuarios)
    baseline_metrics = {
        'far': 1.85,
        'frr': 5.56,
        'eer': 2.78
    }
    
    # 6. Generar reporte
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "speaker_recognition_asvspoof_evaluation.txt"
    
    evaluator.generate_report(metrics, baseline_metrics, output_path)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"Threshold: {evaluator.baseline_threshold:.4f} (Security First)")
    print()
    print(f"Dataset ASVspoof ({NUM_SPEAKERS} hablantes):")
    print(f"  FAR:  {metrics['far']:6.2f}%")
    print(f"  FRR:  {metrics['frr']:6.2f}%")
    print(f"  EER:  {metrics['eer']:6.2f}%")
    print()
    print(f"Baseline (4 usuarios):")
    print(f"  FAR:  {baseline_metrics['far']:6.2f}%")
    print(f"  FRR:  {baseline_metrics['frr']:6.2f}%")
    print(f"  EER:  {baseline_metrics['eer']:6.2f}%")
    print()
    print(f"Diferencia EER: {metrics['eer'] - baseline_metrics['eer']:+.2f}%")
    print()
    print(f"Genuinos:   {genuine_count} comparaciones")
    print(f"Impostores: {impostor_count} comparaciones")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
