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
import torch
import torchaudio
import io

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from speechbrain.inference.ASR import EncoderASR
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class TextVerificationEvaluator:
    """Evaluador del módulo de verificación de texto (ASR) - versión para evaluación sin limitaciones de producción."""
    
    def __init__(self):
        logger.info("Cargando modelo ASR directamente (sin limitaciones de producción)...")
        
        self.device = torch.device("cpu")
        self.target_sample_rate = 16000
        self.asr_model = None
        
        # Cargar modelo ASR directamente con SpeechBrain
        model_path = Path("models/text-verification/lightweight_asr")
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo ASR no encontrado en {model_path}")
        
        try:
            logger.info(f"Cargando modelo desde {model_path}...")
            self.asr_model = EncoderASR.from_hparams(
                source=str(model_path),
                savedir=str(model_path),
                run_opts={"device": str(self.device)}
            )
            logger.info("✅ Modelo ASR cargado exitosamente")
        except Exception as e:
            logger.error(f"Error cargando modelo ASR: {e}")
            raise
    
    def load_audio(self, audio_path: Path) -> torch.Tensor:
        """
        Cargar y preprocesar audio COMPLETO sin limitaciones.
        Sin VAD, sin recortes, sin límites de duración.
        """
        try:
            # Cargar audio
            waveform, sample_rate = torchaudio.load(str(audio_path))
            
            # Resample si es necesario
            if sample_rate != self.target_sample_rate:
                resampler = torchaudio.transforms.Resample(sample_rate, self.target_sample_rate)
                waveform = resampler(waveform)
            
            # Convertir a mono si es stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Normalizar amplitud
            max_val = waveform.abs().max()
            if max_val > 0:
                waveform = waveform / max_val
            
            # Mover a device
            waveform = waveform.to(self.device)
            
            return waveform
            
        except Exception as e:
            logger.error(f"Error cargando audio {audio_path}: {e}")
            raise
    
    def transcribe_audio(self, waveform: torch.Tensor) -> str:
        """
        Transcribir audio completo sin limitaciones de producción.
        """
        try:
            with torch.no_grad():
                wav_lens = torch.tensor([1.0]).to(self.device)
                results = self.asr_model.transcribe_batch(waveform, wav_lens)
                transcription = results[0]
            
            # Extraer texto si es lista
            if isinstance(transcription, list):
                transcription = transcription[0] if transcription else ""
            
            return str(transcription).strip()
            
        except Exception as e:
            logger.error(f"Error transcribiendo: {e}")
            return ""
    
    def normalize_text(self, text: str) -> str:
        """
        Normalizar texto para comparación justa.
        
        - Minúsculas
        - Sin tildes
        - Sin puntuación
        - Sin espacios múltiples
        """
        import unicodedata
        import re
        
        # Minúsculas
        text = text.lower()
        
        # Quitar tildes
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Quitar puntuación y caracteres especiales
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        Calcular Word Error Rate (WER) con normalización mejorada.
        
        WER = (Substitutions + Deletions + Insertions) / Total words
        
        Args:
            reference: Texto de referencia (ground truth)
            hypothesis: Texto transcrito por el ASR
        
        Returns:
            WER como porcentaje (0-100%)
        """
        # Normalizar ambos textos antes de comparar
        ref_normalized = self.normalize_text(reference)
        hyp_normalized = self.normalize_text(hypothesis)
        
        ref_words = ref_normalized.split()
        hyp_words = hyp_normalized.split()
        
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
    
    def calculate_detailed_errors(self, reference: str, hypothesis: str) -> Dict[str, int]:
        """
        Calcular errores detallados: substitución, eliminación, inserción.
        
        Returns:
            Dict con counts de 'substitutions', 'deletions', 'insertions'
        """
        ref_normalized = self.normalize_text(reference)
        hyp_normalized = self.normalize_text(hypothesis)
        
        ref_words = ref_normalized.split()
        hyp_words = hyp_normalized.split()
        
        # Matriz de programación dinámica
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
        
        # Backtrack para contar tipos de errores
        substitutions = 0
        deletions = 0
        insertions = 0
        
        i, j = len(ref_words), len(hyp_words)
        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i-1] == hyp_words[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + 1:
                # Substitución
                substitutions += 1
                i -= 1
                j -= 1
            elif j > 0 and d[i][j] == d[i][j-1] + 1:
                # Inserción
                insertions += 1
                j -= 1
            elif i > 0 and d[i][j] == d[i-1][j] + 1:
                # Eliminación
                deletions += 1
                i -= 1
        
        return {
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions
        }
    
    def generate_visualizations(self, results: Dict, output_dir: Path):
        """
        Generar 3 gráficos de evaluación:
        1. Histograma de Distribución del WER
        2. WER vs. Longitud de Frase
        3. Matriz de Análisis de Errores
        """
        import matplotlib
        matplotlib.use('Agg')  # Backend sin GUI
        import matplotlib.pyplot as plt
        
        logger.info("Generando visualizaciones...")
        
        # Preparar datos
        wer_values = []
        phrase_lengths = []
        error_stats = {'substitutions': 0, 'deletions': 0, 'insertions': 0}
        
        for detail in results['details']:
            wer_values.append(detail['wer'])
            ref_text = self.normalize_text(detail['expected'])
            phrase_lengths.append(len(ref_text.split()))
            
            # Calcular errores detallados
            errors = self.calculate_detailed_errors(detail['expected'], detail['transcribed'])
            error_stats['substitutions'] += errors['substitutions']
            error_stats['deletions'] += errors['deletions']
            error_stats['insertions'] += errors['insertions']
        
        # Crear figura con 3 subplots
        fig = plt.figure(figsize=(16, 5))
        
        # 1. Histograma de Distribución del WER
        ax1 = plt.subplot(1, 3, 1)
        ax1.hist(wer_values, bins=15, color='#3498db', edgecolor='black', alpha=0.7)
        ax1.axvline(np.mean(wer_values), color='red', linestyle='--', linewidth=2, label=f'Media: {np.mean(wer_values):.2f}%')
        ax1.set_xlabel('WER (%)', fontsize=12)
        ax1.set_ylabel('Frecuencia', fontsize=12)
        ax1.set_title('Distribución del Word Error Rate (WER)', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. WER vs. Longitud de Frase
        ax2 = plt.subplot(1, 3, 2)
        ax2.scatter(phrase_lengths, wer_values, color='#e74c3c', alpha=0.6, s=80)
        
        # Línea de tendencia
        z = np.polyfit(phrase_lengths, wer_values, 1)
        p = np.poly1d(z)
        ax2.plot(sorted(phrase_lengths), p(sorted(phrase_lengths)), 
                 "b--", alpha=0.8, linewidth=2, label=f'Tendencia: y={z[0]:.2f}x+{z[1]:.2f}')
        
        ax2.set_xlabel('Longitud de Frase (palabras)', fontsize=12)
        ax2.set_ylabel('WER (%)', fontsize=12)
        ax2.set_title('WER vs. Longitud de Frase', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        # 3. Matriz de Análisis de Errores
        ax3 = plt.subplot(1, 3, 3)
        error_types = ['Sustitución', 'Eliminación', 'Inserción']
        error_counts = [error_stats['substitutions'], error_stats['deletions'], error_stats['insertions']]
        colors = ['#e74c3c', '#f39c12', '#9b59b6']
        
        bars = ax3.bar(error_types, error_counts, color=colors, edgecolor='black', alpha=0.8)
        ax3.set_ylabel('Cantidad de Errores', fontsize=12)
        ax3.set_title('Distribución de Tipos de Errores', fontsize=14, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        # Agregar valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Agregar porcentajes
        total_errors = sum(error_counts)
        for i, (bar, count) in enumerate(zip(bars, error_counts)):
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            ax3.text(bar.get_x() + bar.get_width()/2., height * 0.5,
                    f'{percentage:.1f}%',
                    ha='center', va='center', fontsize=10, color='white', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar
        output_path = output_dir / "text_verification_visualizations.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ Visualizaciones guardadas en: {output_path}")
        
        # Retornar estadísticas de errores
        return error_stats
    
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
                # Transcribir audio completo sin limitaciones
                waveform = self.load_audio(audio_path)
                transcribed = self.transcribe_audio(waveform)
                
                # DEBUG: Imprimir longitud de transcripción
                if i == 1:
                    logger.info(f"DEBUG primer audio - Longitud transcripción: {len(transcribed)} chars")
                    logger.info(f"DEBUG primer audio - Texto: {transcribed[:100]}")
                
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
                # Transcribir audio completo
                waveform = self.load_audio(audio_path)
                transcribed = self.transcribe_audio(waveform)
                
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
    
    # Ground truth extraído del reporte de verificación
    ground_truth = {
        # anachamorromunoz
        "anachamorromunoz_enrollment_01.wav": "Un radio de sol poniente caía sobre el pie de la cama y daba sobre la chimenea, donde el agua hervía por botones.",
        "anachamorromunoz_enrollment_02.wav": "Súbitamente se vio un resplandor de luz y del pozo salió una cantidad de humo verde y luminoso entre bocanadas claramente visibles.",
        "anachamorromunoz_enrollment_03.wav": "El señor Cols tardaba en entender las cosas, pero ahora se daba cuenta de que allí pasaba algo.",
        "anachamorromunoz_verification_01.wav": "Nada de todo cuanto ha sido puesto y repuesto sobre el tapete en el anexo, puede mantenerse joven y fresco.",
        "anachamorromunoz_verification_02.wav": "Aunque ya había luz sobre la Terra, los oculto Atenea con una oscura nube y raudamente, lo sacó de la ciudad.",
        "anachamorromunoz_verification_03.wav": "No es decoroso que decaiga vuestro impetuoso valor, siendo como sois los más valientes del ejército.",
        "anachamorromunoz_verification_04.wav": "El obrero dirigió a lo alto una mirada despavorida y vio con espanto desprenderse pedazos de las paredes.",
        "anachamorromunoz_verification_05.wav": "Y ese, aunque sea poderoso, permanezca tranquilo en la tercia parte que le pertenece.",
        "anachamorromunoz_verification_06.wav": "Mas el fugitivo no había contado con la frialdad del agua ni con los engañosa proximidad de la costa.",
        "anachamorromunoz_verification_07.wav": "Más adelante en camino hacia Weybridge y el otro lado del puente, había un número de reclutas que estaban haciendo un largo Teraplent, estas del camino vivimos más cañones.",
        "anachamorromunoz_verification_08.wav": "En la puerta de la cueva apareció una penosa escena al Opaca Luz del crepúsculo que iluminaba aquel lugar.",
        "anachamorromunoz_verification_09.wav": "Se discutia, se diputaba, se ngociaba la cotización de Chiligoodfood como una de las fondos ingleses.",
        "anachamorromunoz_verification_10.wav": "En el fondo, sentado delante de una mesa, un hombre pequeño, ya entrado en años, hacía anotaciones en un enorme registro.",
        
        # ft_fernandotomas
        "ft_fernandotomas_enrollment_01.wav": "y yo al verlos, no se irrito, porque habían obedecido con pesteza a las órdenes de Juno.",
        "ft_fernandotomas_enrollment_02.wav": "La señora Hall abrió la puerta de Warenmpart para que entrara Mas luz ibara poder ver visitante con Claridad.",
        "ft_fernandotomas_enrollment_03.wav": "La relación del calado encarga con la cabida ha sido mal calculada, y por consiguiente ofrecen al mar muy debil Resistencia.",
        "ft_fernandotomas_verification_01.wav": "La.",
        "ft_fernandotomas_verification_02.wav": "empecé a revolver entre aquella ropa , olvidándome de la agudeza de oído de aquel hombre",
        "ft_fernandotomas_verification_03.wav": "Entonces Tom se ajustó al cinturón, por decirlo así, y se lanzó a la terea de aprender sus vestículos.",
        "ft_fernandotomas_verification_04.wav": "En medio del dédalo pedregoso, que surcaba al fondo del Atlántico, el capitán Nemo avanzaba sin vacilaciones.",
        "ft_fernandotomas_verification_05.wav": "Entretanto, Peter se había mudado para ir a vivir con un compañero mucho mayor que el.",
        "ft_fernandotomas_verification_06.wav": "Entonces escuchó el astuto Odiseo unos pasos afuera, que advirtió que los perros no ladraban.",
        "ft_fernandotomas_verification_07.wav": "La viuda, muy desesperada, lo buscó por todas partes durante cuarenta y ocho horas.",
        "ft_fernandotomas_verification_08.wav": "pues si eres tu , en verdad, quien el asegura ,sabes que has nacido con funesto destino",
        "ft_fernandotomas_verification_09.wav": "A pesar de esta carga que soportamos, muchos de nosotros siguen sobreviviendo: hay que creer que como proscritos los judíos se transformarán en un día en ejemplo.",
        
        # piapobletech
        "piapobletech_enrollment_01.wav": "Ayudadme a todos, pues la obra de muchos siempre resulta mejor, cuatrocientos trece tales fueron sus palabras.",
        "piapobletech_enrollment_02.wav": "Mi vecino opinaba que las tropas podrían capturar o destruir a los marcianos durante el transcurso del día.",
        "piapobletech_enrollment_03.wav": "manifestado, Sirse se me preguntó que me ocurria, ¿Porque estás así mudo odiseo y no quieres probar estos manjares?",
        "piapobletech_verification_01.wav": "el le hizo sufrir mucho hasta que halló un caño de agua corriente que estaba roto y del cual salía líquido como un manantial.",
        "piapobletech_verification_02.wav": "Si lo veía a ella al asomarse la ventana en la mañana alegre y entonces.",
        "piapobletech_verification_03.wav": "Para vengar a sus hijos, los titanes cuidaba y alimentaba desde hacia siglos a tifón el horror absoluto.",
        "piapobletech_verification_04.wav": "A los lejos se elevaban las azuladas colinas de su rey y las torres del cristal Palace relucían como dos baras de plata.",
        "piapobletech_verification_05.wav": "pero como no sabía a que quería el llegar espere nuevas preguntas , reservándome el responder de acuerdo con las circunstancias.",
        "piapobletech_verification_06.wav": "vamos al comedor donde estaba servido al desayuno, señor Aronax, me dijo el capitán , le ruego que comparta desayuno sin cumplidos.",
        "piapobletech_verification_07.wav": "A diez millas del nautilus hacia el sur se alzaba un islote solitario a una altura de doscientos metros.",
        "piapobletech_verification_08.wav": "En ese instante siete tripulantes, mudos e impacibles como siempre, ascendieron a la plataforma.",
        "piapobletech_verification_09.wav": "La haca marina, que se conoce también con el nombre Alicore, recordaba mucho al manati.",
        
        # rapomo3
        "rapomo3_enrollment_01.wav": "Durante este tiempo, yo había reflexionado y una cierta esperanza vaga aún renacía mi corazón.",
        "rapomo3_enrollment_02.wav": "Cada uno de los muchachos persibía una renta prodigiosa, Un dolar cada día laborable del año y medio Dolar los Domingos.",
        "rapomo3_enrollment_03.wav": "Cada uno de estos mounstros tiene hocico de Marsopa, cabeza de lagarto, dientes de cocodrilo y por esto nos ha engañado.",
        "rapomo3_verification_01.wav": "Sus casas eran pequeñas, y en ella solían vivir muchos hermanos, como en el caso de Marta, que eran doce.",
        "rapomo3_verification_02.wav": "En ese momento, el capitán, sin preocuparse por mi presencia abrió el mueble semejante a una caja de caudales que encerraba gran número de lingotes.",
        "rapomo3_verification_03.wav": "Escoge por compañero al que quieras, al mejor de los presentes, pues son muchos los que se ofrecen.",
        "rapomo3_verification_04.wav": "Un Dia se lo mostró, a Él se estaba fuera de sí, pues no fue ninguno de los hombres que estábamos cerca.",
        "rapomo3_verification_05.wav": "en cuanto a mí, distraído hasta entonces por los incidentes del viaje, habíame olvidado algo del porvenir, pero ahora sentí que la zosobra se apodera de mi nuevamente.",
        "rapomo3_verification_06.wav": "No podía hacer otra cosa que esperar en la mayor inactividad durante esas cuarenta y ocho horas.",
        "rapomo3_verification_07.wav": "Tanto en nuestra casa como en la escuela, se hablaba de temas sexuales, a veces con misterio, a veces con verguenza.",
        "rapomo3_verification_08.wav": "La preplejidad y el desagrado del auditorio se manifestó en murmullos y provocó una reprimenda del tribunal.",
        "rapomo3_verification_09.wav": "Entonces uno de ellos avanzó riendo hacia mí, llevando una guirnalda de bella flores que me eran desconocidas por completo y me la puso al cuello."
    }
    
    # Configuración del dataset
    base_dir = Path(__file__).parent.parent.parent.parent
    recordings_dir = base_dir / "infra" / "evaluation" / "dataset" / "recordings" / "auto_recordings_20251218"
    
    if not recordings_dir.exists():
        print(f"❌ Error: Directorio de recordings no encontrado: {recordings_dir}")
        sys.exit(1)
    
    # Inicializar evaluador
    print("Inicializando ASR...")
    evaluator = TextVerificationEvaluator()
    
    # Evaluar transcripción en todos los audios
    print(f"\nTranscribiendo {len(ground_truth)} audios...")
    
    wer_scores = []
    perfect_count = 0
    transcription_details = []
    
    for i, (audio_filename, expected_text) in enumerate(ground_truth.items(), 1):
        user = audio_filename.split('_')[0]
        audio_path = recordings_dir / user / audio_filename
        
        if not audio_path.exists():
            logger.warning(f"Audio no encontrado: {audio_path}")
            continue
        
        try:
            waveform = evaluator.load_audio(audio_path)
            transcribed_text = evaluator.transcribe_audio(waveform)
            wer = evaluator.calculate_wer(expected_text, transcribed_text)
            
            wer_scores.append(wer)
            if wer == 0.0:
                perfect_count += 1
            
            transcription_details.append({
                'audio': audio_filename,
                'expected': expected_text,
                'transcribed': transcribed_text,
                'wer': wer
            })
            
            if i % 5 == 0:
                logger.info(f"  Procesados {i}/{len(ground_truth)}")
                
        except Exception as e:
            logger.error(f"Error procesando {audio_filename}: {e}")
    
    # Calcular métricas
    avg_wer = np.mean(wer_scores) if wer_scores else 0.0
    std_wer = np.std(wer_scores) if wer_scores else 0.0
    transcription_accuracy = 100 - avg_wer
    perfect_rate = (perfect_count / len(wer_scores) * 100) if wer_scores else 0.0
    
    transcription_metrics = {
        'wer': avg_wer,
        'wer_std': std_wer,
        'transcription_accuracy': transcription_accuracy,
        'perfect_transcriptions': perfect_count,
        'perfect_rate': perfect_rate,
        'total_samples': len(wer_scores),
        'details': transcription_details
    }
    
    # Generar reporte
    output_path = base_dir / "evaluation" / "results" / "text_verification_evaluation.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("EVALUACIÓN DEL MÓDULO DE VERIFICACIÓN DE TEXTO (ASR)\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("MÉTRICAS PRINCIPALES\n")
        f.write("-" * 80 + "\n")
        f.write(f"WER (Word Error Rate):           {avg_wer:6.2f}%  ")
        f.write("✅ MEJOR si cercano a 0%\n")
        f.write(f"Transcription Accuracy:          {transcription_accuracy:6.2f}%  ")
        f.write("✅ MEJOR si cercano a 100%\n\n")
        
        f.write("DETALLES DE TRANSCRIPCIÓN\n")
        f.write("-" * 80 + "\n")
        f.write(f"Muestras evaluadas:              {len(wer_scores)}\n")
        f.write(f"Transcripciones perfectas:       {perfect_count} ({perfect_rate:.1f}%)\n")
        f.write(f"WER promedio:                    {avg_wer:.2f}%\n")
        f.write(f"WER desviación estándar:         {std_wer:.2f}%\n\n")
        
        f.write("DETALLE POR AUDIO\n")
        f.write("-" * 80 + "\n")
        for detail in transcription_details:
            f.write(f"\n{detail['audio']}:\n")
            f.write(f"  Esperado:     {detail['expected']}\n")
            f.write(f"  Transcrito:   {detail['transcribed']}\n")
            f.write(f"  WER:          {detail['wer']:.2f}%\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("INTERPRETACIÓN\n")
        f.write("=" * 80 + "\n")
        if avg_wer < 5:
            f.write("✅ WER EXCELENTE (< 5%)\n")
        elif avg_wer < 15:
            f.write("✓ WER BUENO (5-15%)\n")
        else:
            f.write("⚠️  WER REQUIERE MEJORA (> 15%)\n")
        
        if transcription_accuracy > 95:
            f.write("✅ TRANSCRIPTION ACCURACY EXCELENTE (> 95%)\n")
        elif transcription_accuracy > 85:
            f.write("✓ TRANSCRIPTION ACCURACY BUENO (85-95%)\n")
        else:
            f.write("⚠️  TRANSCRIPTION ACCURACY BAJO (< 85%)\n")
    
    logger.info(f"Reporte generado: {output_path}")
    
    # Guardar métricas en JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcription_metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas JSON: {json_path}")
    
    # Generar visualizaciones
    try:
        error_stats = evaluator.generate_visualizations(transcription_metrics, output_path.parent)
        logger.info(f"Estadísticas de errores - Sustituciones: {error_stats['substitutions']}, "
                   f"Eliminaciones: {error_stats['deletions']}, Inserciones: {error_stats['insertions']}")
    except Exception as e:
        logger.error(f"Error generando visualizaciones: {e}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS DE EVALUACIÓN - TEXT VERIFICATION")
    print("=" * 80)
    print(f"Audios evaluados:              {len(wer_scores)}")
    print(f"Transcripciones perfectas:     {perfect_count} ({perfect_rate:.1f}%)")
    print()
    print(f"WER (Word Error Rate):         {avg_wer:6.2f}%  ✅ Menor es mejor")
    print(f"WER std deviation:             {std_wer:6.2f}%")
    print(f"Transcription Accuracy:        {transcription_accuracy:6.2f}%  ✅ Mayor es mejor")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
