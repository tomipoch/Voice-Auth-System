"""
Evaluación del Módulo de Verificación de Texto (ASR - Text Verification)

Métricas calculadas:
- WER (Word Error Rate): % de errores en palabras (menor es mejor, óptimo ~0%)
- Phrase Matching Accuracy: % de frases correctamente identificadas (mayor es mejor, óptimo ~100%)
- Transcription Accuracy: % de transcripciones correctas (mayor es mejor, óptimo ~100%)

Uso:
    python evaluation/evaluate_text_verification.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List
import numpy as np
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.ASRAdapter import ASRAdapter

logger = logging.getLogger(__name__)


class TextVerificationEvaluator:
    """Evaluador del módulo de verificación de texto (ASR)."""
    
    def __init__(self):
        self.asr_adapter = ASRAdapter(use_gpu=True)
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        Calcular Word Error Rate (WER).
        
        WER = (Substitutions + Deletions + Insertions) / Total words
        
        Args:
            reference: Texto de referencia (ground truth)
            hypothesis: Texto transcrito por el ASR
        
        Returns:
            WER como porcentaje (0-100%)
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Usar programación dinámica para calcular distancia de edición
        d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1), dtype=np.int32)
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        if len(ref_words) == 0:
            return 100.0 if len(hyp_words) > 0 else 0.0
        
        wer = (float(d[len(ref_words)][len(hyp_words)]) / len(ref_words)) * 100
        return wer
    
    def calculate_phrase_similarity(self, phrase1: str, phrase2: str) -> float:
        """
        Calcular similitud entre dos frases (normalizada).
        
        Returns:
            Similitud como porcentaje (0-100%)
        """
        phrase1 = phrase1.lower().strip()
        phrase2 = phrase2.lower().strip()
        
        if phrase1 == phrase2:
            return 100.0
        
        # Calcular similitud basada en palabras comunes
        words1 = set(phrase1.split())
        words2 = set(phrase2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = (intersection / union) * 100 if union > 0 else 0.0
        return similarity
    
    def evaluate_transcription(self, test_cases_file: Path) -> Dict:
        """
        Evaluar precisión de transcripción con WER.
        
        Args:
            test_cases_file: Archivo JSON con casos de prueba
                Format: [{"audio": "path/to/audio.wav", "text": "texto esperado"}, ...]
        
        Returns:
            Dict con métricas de transcripción
        """
        logger.info("Evaluando precisión de transcripción...")
        
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        
        wer_scores = []
        perfect_transcriptions = 0
        total = len(test_cases)
        
        dataset_dir = test_cases_file.parent
        
        for i, case in enumerate(test_cases, 1):
            audio_path = dataset_dir / case['audio']
            reference_text = case['text']
            
            if not audio_path.exists():
                logger.warning(f"Audio no encontrado: {audio_path}")
                continue
            
            try:
                # Transcribir
                audio_data = self.load_audio(audio_path)
                transcribed = self.asr_adapter.transcribe(audio_data)
                
                # Calcular WER
                wer = self.calculate_wer(reference_text, transcribed)
                wer_scores.append(wer)
                
                if wer == 0.0:
                    perfect_transcriptions += 1
                
                if i % 10 == 0:
                    logger.info(f"  Procesados {i}/{total}")
                
            except Exception as e:
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        # Calcular métricas
        avg_wer = np.mean(wer_scores) if wer_scores else 100.0
        transcription_accuracy = 100.0 - avg_wer  # Invertir WER para obtener accuracy
        perfect_rate = (perfect_transcriptions / len(wer_scores)) * 100 if wer_scores else 0.0
        
        return {
            'wer': avg_wer,
            'transcription_accuracy': transcription_accuracy,
            'perfect_transcriptions': perfect_transcriptions,
            'perfect_rate': perfect_rate,
            'total_samples': len(wer_scores),
            'wer_std': float(np.std(wer_scores)) if wer_scores else 0.0
        }
    
    def evaluate_phrase_matching(self, phrase_matching_file: Path) -> Dict:
        """
        Evaluar capacidad de coincidencia de frases.
        
        Args:
            phrase_matching_file: Archivo JSON con casos de prueba
                Format: [
                    {
                        "audio": "path/to/audio.wav",
                        "expected_phrase": "la frase correcta",
                        "test_phrases": ["la frase correcta", "otra frase", "frase incorrecta"]
                    },
                    ...
                ]
        
        Returns:
            Dict con métricas de phrase matching
        """
        logger.info("Evaluando coincidencia de frases...")
        
        with open(phrase_matching_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        
        correct_matches = 0
        incorrect_rejections = 0
        correct_rejections = 0
        false_matches = 0
        total_tests = 0
        
        dataset_dir = phrase_matching_file.parent
        
        for i, case in enumerate(test_cases, 1):
            audio_path = dataset_dir / case['audio']
            expected_phrase = case['expected_phrase']
            test_phrases = case['test_phrases']
            
            if not audio_path.exists():
                logger.warning(f"Audio no encontrado: {audio_path}")
                continue
            
            try:
                # Transcribir audio
                audio_data = self.load_audio(audio_path)
                transcribed = self.asr_adapter.transcribe(audio_data)
                
                # Probar coincidencia con cada frase
                for test_phrase in test_phrases:
                    is_expected = (test_phrase == expected_phrase)
                    similarity = self.calculate_phrase_similarity(transcribed, test_phrase)
                    
                    # Umbral de aceptación: 70%
                    is_match = similarity >= 70.0
                    
                    total_tests += 1
                    
                    if is_expected and is_match:
                        correct_matches += 1
                    elif is_expected and not is_match:
                        incorrect_rejections += 1
                    elif not is_expected and is_match:
                        false_matches += 1
                    elif not is_expected and not is_match:
                        correct_rejections += 1
                
                if i % 10 == 0:
                    logger.info(f"  Procesados {i}/{len(test_cases)}")
                
            except Exception as e:
                logger.error(f"Error procesando {audio_path.name}: {e}")
        
        # Calcular métricas
        phrase_matching_accuracy = ((correct_matches + correct_rejections) / total_tests * 100) if total_tests > 0 else 0.0
        correct_phrase_accuracy = (correct_matches / (correct_matches + incorrect_rejections) * 100) if (correct_matches + incorrect_rejections) > 0 else 0.0
        incorrect_phrase_rejection = (correct_rejections / (correct_rejections + false_matches) * 100) if (correct_rejections + false_matches) > 0 else 0.0
        
        return {
            'phrase_matching_accuracy': phrase_matching_accuracy,
            'correct_phrase_accuracy': correct_phrase_accuracy,
            'incorrect_phrase_rejection': incorrect_phrase_rejection,
            'correct_matches': correct_matches,
            'incorrect_rejections': incorrect_rejections,
            'correct_rejections': correct_rejections,
            'false_matches': false_matches,
            'total_tests': total_tests
        }
    
    def generate_report(
        self,
        transcription_metrics: Dict,
        phrase_matching_metrics: Dict,
        output_path: Path
    ) -> None:
        """Generar reporte de evaluación."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN DEL MÓDULO DE VERIFICACIÓN DE TEXTO (ASR)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("MÉTRICAS PRINCIPALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"WER (Word Error Rate):           {transcription_metrics['wer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"Transcription Accuracy:          {transcription_metrics['transcription_accuracy']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 100%\n")
            f.write(f"Phrase Matching Accuracy:        {phrase_matching_metrics['phrase_matching_accuracy']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 100%\n\n")
            
            f.write("DETALLES DE TRANSCRIPCIÓN\n")
            f.write("-" * 80 + "\n")
            f.write(f"Muestras evaluadas:              {transcription_metrics['total_samples']}\n")
            f.write(f"Transcripciones perfectas:       {transcription_metrics['perfect_transcriptions']} ")
            f.write(f"({transcription_metrics['perfect_rate']:.1f}%)\n")
            f.write(f"WER promedio:                    {transcription_metrics['wer']:.2f}%\n")
            f.write(f"WER desviación estándar:         {transcription_metrics['wer_std']:.2f}%\n\n")
            
            f.write("DETALLES DE COINCIDENCIA DE FRASES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total de pruebas:                {phrase_matching_metrics['total_tests']}\n")
            f.write(f"Coincidencias correctas:         {phrase_matching_metrics['correct_matches']}\n")
            f.write(f"Rechazos correctos:              {phrase_matching_metrics['correct_rejections']}\n")
            f.write(f"Rechazos incorrectos:            {phrase_matching_metrics['incorrect_rejections']}\n")
            f.write(f"Coincidencias falsas:            {phrase_matching_metrics['false_matches']}\n")
            f.write(f"Accuracy de frase correcta:      {phrase_matching_metrics['correct_phrase_accuracy']:.2f}%\n")
            f.write(f"Rechazo de frase incorrecta:     {phrase_matching_metrics['incorrect_phrase_rejection']:.2f}%\n\n")
            
            f.write("INTERPRETACIÓN\n")
            f.write("-" * 80 + "\n")
            if transcription_metrics['wer'] < 5:
                f.write("✅ WER EXCELENTE (< 5%)\n")
            elif transcription_metrics['wer'] < 15:
                f.write("✓ WER BUENO (5-15%)\n")
            else:
                f.write("⚠️  WER REQUIERE MEJORA (> 15%)\n")
            
            if transcription_metrics['transcription_accuracy'] > 95:
                f.write("✅ TRANSCRIPTION ACCURACY EXCELENTE (> 95%)\n")
            elif transcription_metrics['transcription_accuracy'] > 85:
                f.write("✓ TRANSCRIPTION ACCURACY BUENO (85-95%)\n")
            else:
                f.write("⚠️  TRANSCRIPTION ACCURACY BAJO (< 85%)\n")
            
            if phrase_matching_metrics['phrase_matching_accuracy'] > 95:
                f.write("✅ PHRASE MATCHING ACCURACY EXCELENTE (> 95%)\n")
            elif phrase_matching_metrics['phrase_matching_accuracy'] > 85:
                f.write("✓ PHRASE MATCHING ACCURACY BUENO (85-95%)\n")
            else:
                f.write("⚠️  PHRASE MATCHING ACCURACY BAJO (< 85%)\n")
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar métricas en JSON
        combined_metrics = {
            'transcription': transcription_metrics,
            'phrase_matching': phrase_matching_metrics
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
    print("EVALUACIÓN DEL MÓDULO DE VERIFICACIÓN DE TEXTO (ASR)")
    print("=" * 80)
    print()
    
    # Configuración del dataset
    base_dir = Path(__file__).parent.parent
    dataset_dir = base_dir / "evaluation" / "dataset" / "text_verification"
    
    transcription_file = dataset_dir / "transcription_tests.json"
    phrase_matching_file = dataset_dir / "phrase_matching_tests.json"
    
    # Verificar archivos
    if not transcription_file.exists():
        print(f"❌ Error: Archivo de pruebas de transcripción no encontrado: {transcription_file}")
        print("\nFormato esperado de transcription_tests.json:")
        print('[{"audio": "audio1.wav", "text": "texto esperado"}, ...]')
        sys.exit(1)
    
    if not phrase_matching_file.exists():
        print(f"❌ Error: Archivo de pruebas de phrase matching no encontrado: {phrase_matching_file}")
        print("\nFormato esperado de phrase_matching_tests.json:")
        print('[{"audio": "audio1.wav", "expected_phrase": "frase correcta", "test_phrases": ["frase correcta", "otra frase"]}, ...]')
        sys.exit(1)
    
    # Inicializar evaluador
    evaluator = TextVerificationEvaluator()
    
    # 1. Evaluar transcripción
    transcription_metrics = evaluator.evaluate_transcription(transcription_file)
    
    # 2. Evaluar phrase matching
    phrase_matching_metrics = evaluator.evaluate_phrase_matching(phrase_matching_file)
    
    # 3. Generar reporte
    output_path = base_dir / "evaluation" / "results" / "text_verification_evaluation.txt"
    evaluator.generate_report(transcription_metrics, phrase_matching_metrics, output_path)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"WER (Word Error Rate):        {transcription_metrics['wer']:6.2f}%  ✅ Menor es mejor")
    print(f"Transcription Accuracy:       {transcription_metrics['transcription_accuracy']:6.2f}%  ✅ Mayor es mejor")
    print(f"Phrase Matching Accuracy:     {phrase_matching_metrics['phrase_matching_accuracy']:6.2f}%  ✅ Mayor es mejor")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
