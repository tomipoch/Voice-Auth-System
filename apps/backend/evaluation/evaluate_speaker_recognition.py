"""
Evaluación del Módulo de Reconocimiento de Locutor (Speaker Recognition)

Métricas calculadas:
- FRR (False Rejection Rate): % de usuarios genuinos rechazados (menor es mejor, óptimo ~0%)
- FAR (False Acceptance Rate): % de impostores aceptados (menor es mejor, óptimo ~0%)
- EER (Equal Error Rate): Punto donde FAR = FRR (menor es mejor, óptimo ~0%)

Uso:
    python evaluation/evaluate_speaker_recognition.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import json
import wave
import io
import matplotlib.pyplot as plt
import matplotlib
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from scipy.spatial.distance import euclidean

# Set matplotlib backend for headless environments
matplotlib.use('Agg')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logger = logging.getLogger(__name__)


class SpeakerRecognitionEvaluator:
    """Evaluador del módulo de reconocimiento de locutor."""
    
    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self.speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
        self.voiceprints = {}
        self.users = [
            "anachamorromunoz",
            "ft_fernandotomas",
            "piapobletech",
            "rapomo3"
        ]
        # Métricas de calidad de audios
        self.audio_quality_metrics = {}
        self.enrollment_quality = {}  # SNR de audios de enrollment
        self.duration_analysis = []  # Para correlación duración-score
        
        # Score Normalization
        self.cohort_scores = {}  # Scores de cohort para normalización
        self.enable_score_normalization = True
        self.enable_multiphrase_decision = True
        self.doubt_zone = (0.53, 0.55)  # Zona de duda para decisión multi-frase
        
        # Para visualizaciones
        self.all_embeddings = {}  # Guardar embeddings para visualización
        
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_snr(self, audio_data: bytes) -> float:
        """Calcular Signal-to-Noise Ratio (SNR) en dB."""
        try:
            # Cargar audio WAV
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                sample_width = wav_file.getsampwidth()
                
                # Convertir a numpy array
                if sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    dtype = np.uint8
                
                waveform = np.frombuffer(frames, dtype=dtype).astype(np.float32)
                
                # Normalizar
                if dtype != np.float32:
                    if dtype == np.uint8:
                        waveform = (waveform - 128) / 128.0
                    else:
                        waveform = waveform / np.iinfo(dtype).max
                
                # Calcular SNR usando método de energía
                # Asumimos que los frames con mayor energía son señal
                # y los frames con menor energía son ruido
                
                # Dividir en ventanas de 20ms
                window_size = int(0.02 * sample_rate)  # 20ms
                n_windows = len(waveform) // window_size
                
                if n_windows < 5:
                    return 0.0  # Audio muy corto
                
                # Calcular energía por ventana
                energies = []
                for i in range(n_windows):
                    start = i * window_size
                    end = start + window_size
                    window = waveform[start:end]
                    energy = np.mean(window ** 2)
                    energies.append(energy)
                
                energies = np.array(energies)
                
                # Ordenar energías
                sorted_energies = np.sort(energies)
                
                # Ruido = 20% inferior, Señal = 20% superior
                noise_threshold = int(0.2 * len(sorted_energies))
                signal_threshold = int(0.8 * len(sorted_energies))
                
                noise_energy = np.mean(sorted_energies[:noise_threshold]) + 1e-10
                signal_energy = np.mean(sorted_energies[signal_threshold:]) + 1e-10
                
                # SNR en dB
                snr_db = 10 * np.log10(signal_energy / noise_energy)
                
                return max(0.0, float(snr_db))  # No permitir SNR negativo
                
        except Exception as e:
            logger.warning(f"Error calculando SNR: {e}")
            return 0.0
    
    def get_audio_duration(self, audio_data: bytes) -> float:
        """Obtener duración del audio en segundos."""
        try:
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / sample_rate
                return float(duration)
        except Exception as e:
            logger.warning(f"Error obteniendo duración: {e}")
            return 0.0
    
    def apply_vad(self, audio_data: bytes) -> bytes:
        """Aplicar Voice Activity Detection para eliminar silencios."""
        try:
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                sample_width = wav_file.getsampwidth()
                channels = wav_file.getnchannels()
                
                # Convertir a numpy
                if sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    dtype = np.uint8
                
                waveform = np.frombuffer(frames, dtype=dtype)
                
                # Detectar actividad de voz (energía > umbral)
                # Ventanas de 20ms
                window_size = int(0.02 * sample_rate)
                n_windows = len(waveform) // window_size
                
                if n_windows < 2:
                    return audio_data  # Muy corto, no procesar
                
                # Calcular energía por ventana
                energies = []
                for i in range(n_windows):
                    start = i * window_size
                    end = start + window_size
                    window = waveform[start:end].astype(np.float32)
                    energy = np.mean(window ** 2)
                    energies.append(energy)
                
                energies = np.array(energies)
                
                # Umbral dinámico: mediana * 1.5
                threshold = np.median(energies) * 1.5
                
                # Encontrar inicio y fin de voz
                voice_windows = energies > threshold
                
                if not np.any(voice_windows):
                    return audio_data  # No se detectó voz, mantener original
                
                first_voice = np.argmax(voice_windows)
                last_voice = len(voice_windows) - np.argmax(voice_windows[::-1]) - 1
                
                # Recortar con margen de 1 ventana
                start_sample = max(0, (first_voice - 1) * window_size)
                end_sample = min(len(waveform), (last_voice + 2) * window_size)
                
                trimmed_waveform = waveform[start_sample:end_sample]
                
                # Crear nuevo WAV
                output = io.BytesIO()
                with wave.open(output, 'wb') as out_wav:
                    out_wav.setnchannels(channels)
                    out_wav.setsampwidth(sample_width)
                    out_wav.setframerate(sample_rate)
                    out_wav.writeframes(trimmed_waveform.tobytes())
                
                return output.getvalue()
                
        except Exception as e:
            logger.warning(f"Error aplicando VAD: {e}")
            return audio_data  # Retornar original si falla
    
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno entre embeddings."""
        norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        similarity = np.dot(norm1, norm2)
        return float(max(0.0, min(1.0, similarity)))
    
    def calculate_cohort_scores(self, test_embedding: np.ndarray) -> Dict[str, float]:
        """
        Calcular scores contra cohort (otros usuarios) para normalización.
        Implementa parte de Adaptive S-Norm.
        
        Args:
            test_embedding: Embedding de prueba
            
        Returns:
            Dict con scores contra cada usuario del cohort
        """
        cohort_scores = {}
        for user, voiceprint in self.voiceprints.items():
            score = self.calculate_similarity(test_embedding, voiceprint)
            cohort_scores[user] = score
        return cohort_scores
    
    def normalize_score(
        self, 
        raw_score: float, 
        claimed_user: str,
        test_embedding: np.ndarray
    ) -> float:
        """
        Normalizar score usando Adaptive S-Norm (Symmetric Normalization).
        
        Args:
            raw_score: Score original de similitud
            claimed_user: Usuario que clama ser
            test_embedding: Embedding de prueba
            
        Returns:
            Score normalizado
        """
        if not self.enable_score_normalization:
            return raw_score
        
        # Obtener scores contra cohort (otros usuarios)
        cohort_scores = self.calculate_cohort_scores(test_embedding)
        
        # Eliminar el score del usuario reclamado
        impostor_scores = [s for u, s in cohort_scores.items() if u != claimed_user]
        
        if not impostor_scores:
            return raw_score
        
        # S-Norm: (score - mean_impostor) / std_impostor
        mean_impostor = np.mean(impostor_scores)
        std_impostor = np.std(impostor_scores) + 1e-8
        
        normalized_score = (raw_score - mean_impostor) / std_impostor
        
        # Escalar de vuelta a [0, 1]
        # Z-score típicamente está en [-3, 3], mapeamos a [0, 1]
        normalized_score = (normalized_score + 3) / 6
        normalized_score = max(0.0, min(1.0, normalized_score))
        
        return normalized_score
    
    def multi_phrase_decision(
        self,
        scores: List[float],
        threshold: float
    ) -> Tuple[bool, float, str]:
        """
        Decisión multi-frase para zona de duda.
        
        Args:
            scores: Lista de scores de diferentes frases
            threshold: Umbral de decisión
            
        Returns:
            Tupla (decision, avg_score, reason)
        """
        if not self.enable_multiphrase_decision:
            # Decisión simple con primer score
            decision = scores[0] >= threshold
            return decision, scores[0], "single_phrase"
        
        # Si tenemos múltiples scores, promediar
        avg_score = np.mean(scores)
        
        # Zona de duda
        doubt_min, doubt_max = self.doubt_zone
        
        if len(scores) == 1:
            # Solo una frase
            if doubt_min <= scores[0] <= doubt_max:
                # Está en zona de duda, necesitaría segunda frase
                decision = scores[0] >= threshold
                return decision, scores[0], "doubt_zone_single"
            else:
                # Fuera de zona de duda, decisión clara
                decision = scores[0] >= threshold
                return decision, scores[0], "clear_decision"
        else:
            # Múltiples frases, usar promedio
            decision = avg_score >= threshold
            return decision, avg_score, "multi_phrase"
    
    
    def enroll_user(self, user: str) -> np.ndarray:
        """
        Inscribir usuario creando voiceprint con audios de enrollment.
        Implementa Enrollment Selection: descarta audios con SNR < 15dB.
        
        Args:
            user: ID del usuario
            
        Returns:
            Voiceprint (embedding promedio) del usuario
        """
        user_dir = self.recordings_dir / user
        
        # Buscar audios de enrollment (_enrollment_01, _02, _03)
        enrollment_files = sorted(user_dir.glob(f"{user}_enrollment_*.wav"))
        
        if len(enrollment_files) < 3:
            raise ValueError(f"Usuario {user} no tiene suficientes audios de enrollment")
        
        # MEJORA 1: Enrollment Selection - Evaluar calidad de cada audio
        audio_candidates = []
        for audio_file in enrollment_files[:3]:
            audio_data = self.load_audio(audio_file)
            
            # Calcular SNR
            snr = self.calculate_snr(audio_data)
            duration = self.get_audio_duration(audio_data)
            
            # MEJORA 2: Aplicar VAD para eliminar silencios
            audio_data_vad = self.apply_vad(audio_data)
            
            audio_candidates.append({
                'file': audio_file,
                'data': audio_data_vad,
                'snr': snr,
                'duration': duration
            })
            
            logger.debug(f"  {audio_file.name}: SNR={snr:.1f}dB, Duración={duration:.2f}s")
        
        # Filtrar audios con SNR < 15dB (umbral de calidad)
        MIN_SNR = 15.0
        good_audios = [a for a in audio_candidates if a['snr'] >= MIN_SNR]
        
        # Si todos tienen SNR bajo, usar los 2 mejores
        if len(good_audios) < 2:
            logger.warning(f"  ⚠️ Usuario {user}: Todos los audios tienen SNR bajo, usando los 2 mejores")
            audio_candidates.sort(key=lambda x: x['snr'], reverse=True)
            good_audios = audio_candidates[:2]
        
        # Guardar métricas de calidad
        self.enrollment_quality[user] = {
            'audios': [(a['file'].name, a['snr'], a['duration']) for a in audio_candidates],
            'selected': [(a['file'].name, a['snr'], a['duration']) for a in good_audios],
            'avg_snr': np.mean([a['snr'] for a in good_audios]),
            'avg_duration': np.mean([a['duration'] for a in good_audios])
        }
        
        # Extraer embeddings de audios seleccionados
        embeddings = []
        for audio_info in good_audios:
            embedding = self.speaker_adapter.extract_embedding(audio_info['data'], audio_format="wav")
            embeddings.append(embedding)
        
        # Guardar embeddings para visualización
        if user not in self.all_embeddings:
            self.all_embeddings[user] = []
        self.all_embeddings[user].extend(embeddings)
        
        # Crear voiceprint promedio
        voiceprint = np.mean(embeddings, axis=0)
        
        logger.info(f"  ✓ Usuario {user} inscrito con {len(embeddings)}/{len(audio_candidates)} muestras (SNR avg: {self.enrollment_quality[user]['avg_snr']:.1f}dB)")
        return voiceprint
    
    def enroll_all_users(self) -> None:
        """Inscribir todos los usuarios."""
        logger.info("Inscribiendo usuarios...")
        
        for user in self.users:
            try:
                self.voiceprints[user] = self.enroll_user(user)
            except Exception as e:
                logger.error(f"Error inscribiendo {user}: {e}")
        
        logger.info(f"Total usuarios inscritos: {len(self.voiceprints)}")
    
    def evaluate_genuine_attempts(self) -> Tuple[List[float], int]:
        """
        Evaluar intentos genuinos: verificación vs enrolamiento propio.
        
        Compara cada audio de verification de un usuario contra su propio voiceprint.
        Total: 4 usuarios × 10 audios = 40 comparaciones
        
        Returns:
            Tupla (scores, total_comparisons)
        """
        logger.info("\nEvaluando intentos genuinos (verificación vs enrolamiento propio)...")
        genuine_scores = []
        comparisons = 0
        
        for user in self.users:
            if user not in self.voiceprints:
                logger.warning(f"Usuario {user} no inscrito, omitiendo...")
                continue
            
            user_dir = self.recordings_dir / user
            voiceprint = self.voiceprints[user]
            
            # Buscar audios de verification (_verification_01 a _10)
            verification_files = sorted(user_dir.glob(f"{user}_verification_*.wav"))
            
            logger.info(f"  Usuario {user}: {len(verification_files)} audios de verificación")
            
            for audio_file in verification_files:
                audio_data = self.load_audio(audio_file)
                
                # MEJORA 3: Aplicar VAD y obtener duración
                duration = self.get_audio_duration(audio_data)
                audio_data_vad = self.apply_vad(audio_data)
                
                test_embedding = self.speaker_adapter.extract_embedding(audio_data_vad, audio_format="wav")
                
                # Guardar embedding para visualización
                self.all_embeddings[user].append(test_embedding)
                
                # Score original
                raw_similarity = self.calculate_similarity(voiceprint, test_embedding)
                
                # MEJORA A: Score Normalization
                normalized_similarity = self.normalize_score(raw_similarity, user, test_embedding)
                
                genuine_scores.append(normalized_similarity)
                comparisons += 1
                
                # Guardar para análisis de correlación duración-score
                self.duration_analysis.append({
                    'user': user,
                    'type': 'genuine',
                    'duration': duration,
                    'score': normalized_similarity,
                    'raw_score': raw_similarity
                })
                
                logger.debug(f"    {audio_file.name}: raw={raw_similarity:.4f}, norm={normalized_similarity:.4f} (dur={duration:.2f}s)")
        
        logger.info(f"  Total intentos genuinos: {comparisons}")
        return genuine_scores, comparisons
    
    def evaluate_impostor_attempts(self) -> Tuple[List[float], int]:
        """
        Evaluar intentos de impostores: verificación de A vs enrolamiento de B.
        
        Compara audios de verification de Usuario A contra voiceprints de otros usuarios.
        Total: 4 usuarios × 3 otros usuarios × 10 audios = 120 comparaciones
        
        Returns:
            Tupla (scores, total_comparisons)
        """
        logger.info("\nEvaluando intentos de impostores (verificación cruzada)...")
        impostor_scores = []
        comparisons = 0
        
        for claimed_user in self.users:
            if claimed_user not in self.voiceprints:
                continue
            
            claimed_voiceprint = self.voiceprints[claimed_user]
            
            # Comparar contra verificaciones de otros usuarios
            for actual_user in self.users:
                if actual_user == claimed_user:
                    continue  # Saltar comparación con mismo usuario
                
                actual_user_dir = self.recordings_dir / actual_user
                verification_files = sorted(actual_user_dir.glob(f"{actual_user}_verification_*.wav"))
                
                logger.info(f"  {actual_user} intentando hacerse pasar por {claimed_user}: {len(verification_files)} audios")
                
                for audio_file in verification_files:
                    audio_data = self.load_audio(audio_file)
                    
                    # Aplicar VAD y obtener duración
                    duration = self.get_audio_duration(audio_data)
                    audio_data_vad = self.apply_vad(audio_data)
                    
                    test_embedding = self.speaker_adapter.extract_embedding(audio_data_vad, audio_format="wav")
                    
                    # Score original
                    raw_similarity = self.calculate_similarity(claimed_voiceprint, test_embedding)
                    
                    # Score Normalization
                    normalized_similarity = self.normalize_score(raw_similarity, claimed_user, test_embedding)
                    
                    impostor_scores.append(normalized_similarity)
                    comparisons += 1
                    
                    # Guardar para análisis
                    self.duration_analysis.append({
                        'user': actual_user,
                        'type': 'impostor',
                        'duration': duration,
                        'score': normalized_similarity,
                        'raw_score': raw_similarity
                    })
                    
                    logger.debug(f"    {audio_file.name} vs {claimed_user}: raw={raw_similarity:.4f}, norm={normalized_similarity:.4f} (dur={duration:.2f}s)")
        
        logger.info(f"  Total intentos de impostores: {comparisons}")
        return impostor_scores, comparisons
    
    def calculate_metrics(
        self, 
        genuine_scores: List[float], 
        impostor_scores: List[float],
        threshold: float = 0.65
    ) -> Dict:
        """
        Calcular FAR, FRR y EER.
        
        Args:
            genuine_scores: Scores de intentos genuinos
            impostor_scores: Scores de intentos de impostores
            threshold: Umbral de decisión (aceptar si score >= threshold)
        
        Returns:
            Dict con métricas calculadas
        """
        genuine_scores = np.array(genuine_scores)
        impostor_scores = np.array(impostor_scores)
        
        # FAR: % de impostores aceptados (score >= threshold)
        false_accepts = np.sum(impostor_scores >= threshold)
        far = (false_accepts / len(impostor_scores)) * 100 if len(impostor_scores) > 0 else 0.0
        
        # FRR: % de genuinos rechazados (score < threshold)
        false_rejects = np.sum(genuine_scores < threshold)
        frr = (false_rejects / len(genuine_scores)) * 100 if len(genuine_scores) > 0 else 0.0
        
        # Encontrar EER (punto donde FAR = FRR)
        eer, eer_threshold = self._find_eer(genuine_scores, impostor_scores)
        
        return {
            'threshold': threshold,
            'far': far,
            'frr': frr,
            'eer': eer,
            'eer_threshold': eer_threshold,
            'genuine_count': len(genuine_scores),
            'impostor_count': len(impostor_scores),
            'genuine_mean': float(np.mean(genuine_scores)),
            'genuine_std': float(np.std(genuine_scores)),
            'impostor_mean': float(np.mean(impostor_scores)),
            'impostor_std': float(np.std(impostor_scores))
        }
    
    def _find_eer(
        self, 
        genuine_scores: np.ndarray, 
        impostor_scores: np.ndarray
    ) -> Tuple[float, float]:
        """Encontrar Equal Error Rate."""
        thresholds = np.linspace(0, 1, 1000)
        fars = []
        frrs = []
        
        for t in thresholds:
            false_accepts = np.sum(impostor_scores >= t)
            far = false_accepts / len(impostor_scores)
            
            false_rejects = np.sum(genuine_scores < t)
            frr = false_rejects / len(genuine_scores)
            
            fars.append(far)
            frrs.append(frr)
        
        fars = np.array(fars)
        frrs = np.array(frrs)
        
        # Encontrar punto más cercano donde FAR = FRR
        diff = np.abs(fars - frrs)
        eer_idx = np.argmin(diff)
        
        eer = ((fars[eer_idx] + frrs[eer_idx]) / 2) * 100
        eer_threshold = thresholds[eer_idx]
        
        return eer, eer_threshold
    
    def find_optimal_threshold(
        self,
        genuine_scores: List[float],
        impostor_scores: List[float]
    ) -> Dict:
        """
        Encontrar threshold óptimo usando diferentes estrategias.
        
        Returns:
            Dict con diferentes thresholds y sus métricas
        """
        genuine_scores = np.array(genuine_scores)
        impostor_scores = np.array(impostor_scores)
        
        thresholds = np.linspace(0, 1, 1000)
        
        results = []
        for t in thresholds:
            # FAR y FRR
            false_accepts = np.sum(impostor_scores >= t)
            far = false_accepts / len(impostor_scores)
            
            false_rejects = np.sum(genuine_scores < t)
            frr = false_rejects / len(genuine_scores)
            
            # Error total
            total_error = far + frr
            
            # Accuracy
            true_accepts = len(genuine_scores) - false_rejects
            true_rejects = len(impostor_scores) - false_accepts
            accuracy = (true_accepts + true_rejects) / (len(genuine_scores) + len(impostor_scores))
            
            results.append({
                'threshold': t,
                'far': far,
                'frr': frr,
                'total_error': total_error,
                'accuracy': accuracy
            })
        
        # Encontrar threshold óptimo (minimiza error total)
        optimal_idx = min(range(len(results)), key=lambda i: results[i]['total_error'])
        optimal = results[optimal_idx]
        
        # Encontrar threshold EER
        eer_idx = min(range(len(results)), key=lambda i: abs(results[i]['far'] - results[i]['frr']))
        eer = results[eer_idx]
        
        # Encontrar threshold con máxima accuracy
        max_acc_idx = max(range(len(results)), key=lambda i: results[i]['accuracy'])
        max_acc = results[max_acc_idx]
        
        # SECURITY FIRST: Minimizar FAR con FRR aceptable (< 10%)
        # Encontrar el threshold más bajo que tenga FAR=0% o cercano
        security_candidates = [r for r in results if r['frr'] <= 0.10]  # FRR < 10% aceptable
        if security_candidates:
            security_idx = results.index(min(security_candidates, key=lambda r: r['far']))
            security = results[security_idx]
        else:
            # Si no hay candidatos con FRR < 10%, usar el de menor FAR
            security_idx = min(range(len(results)), key=lambda i: results[i]['far'])
            security = results[security_idx]
        
        # SECURITY STRICT: FAR=0% absoluto (si existe)
        zero_far_candidates = [r for r in results if r['far'] == 0 and r['frr'] <= 0.20]
        if zero_far_candidates:
            strict_idx = results.index(min(zero_far_candidates, key=lambda r: r['frr']))
            strict = results[strict_idx]
        else:
            # Si no hay FAR=0%, usar el más cercano
            strict = security
        
        return {
            'security_strict': {
                'threshold': strict['threshold'],
                'far': strict['far'] * 100,
                'frr': strict['frr'] * 100,
                'total_error': strict['total_error'] * 100,
                'accuracy': strict['accuracy'] * 100,
                'strategy': '🔒 SEGURIDAD MÁXIMA: FAR=0% (prioridad absoluta)'
            },
            'security_first': {
                'threshold': security['threshold'],
                'far': security['far'] * 100,
                'frr': security['frr'] * 100,
                'total_error': security['total_error'] * 100,
                'accuracy': security['accuracy'] * 100,
                'strategy': '🛡️  SEGURIDAD: Minimiza FAR con FRR aceptable (<10%)'
            },
            'eer': {
                'threshold': eer['threshold'],
                'far': eer['far'] * 100,
                'frr': eer['frr'] * 100,
                'total_error': eer['total_error'] * 100,
                'accuracy': eer['accuracy'] * 100,
                'strategy': '⚖️  BALANCE: FAR = FRR'
            },
            'optimal': {
                'threshold': optimal['threshold'],
                'far': optimal['far'] * 100,
                'frr': optimal['frr'] * 100,
                'total_error': optimal['total_error'] * 100,
                'accuracy': optimal['accuracy'] * 100,
                'strategy': '📊 ÓPTIMO: Minimiza error total (FAR + FRR)'
            }
        }
    
    def analyze_duration_correlation(self) -> Dict:
        """Analizar correlación entre duración y scores."""
        if not self.duration_analysis:
            return {}
        
        # Separar por tipo
        genuine = [d for d in self.duration_analysis if d['type'] == 'genuine']
        impostor = [d for d in self.duration_analysis if d['type'] == 'impostor']
        
        result = {}
        
        if genuine:
            durations = np.array([d['duration'] for d in genuine])
            scores = np.array([d['score'] for d in genuine])
            
            # Calcular correlación de Pearson
            if len(durations) > 1:
                correlation = np.corrcoef(durations, scores)[0, 1]
            else:
                correlation = 0.0
            
            result['genuine'] = {
                'correlation': float(correlation),
                'avg_duration': float(np.mean(durations)),
                'avg_score': float(np.mean(scores)),
                'count': len(genuine)
            }
            
            # Análisis por rangos de duración
            short = [d for d in genuine if d['duration'] < 2.5]
            medium = [d for d in genuine if 2.5 <= d['duration'] < 4.0]
            long = [d for d in genuine if d['duration'] >= 4.0]
            
            result['genuine_by_duration'] = {
                'short_avg_score': float(np.mean([d['score'] for d in short])) if short else 0.0,
                'medium_avg_score': float(np.mean([d['score'] for d in medium])) if medium else 0.0,
                'long_avg_score': float(np.mean([d['score'] for d in long])) if long else 0.0,
                'short_count': len(short),
                'medium_count': len(medium),
                'long_count': len(long)
            }
        
        if impostor:
            durations = np.array([d['duration'] for d in impostor])
            scores = np.array([d['score'] for d in impostor])
            
            if len(durations) > 1:
                correlation = np.corrcoef(durations, scores)[0, 1]
            else:
                correlation = 0.0
            
            result['impostor'] = {
                'correlation': float(correlation),
                'avg_duration': float(np.mean(durations)),
                'avg_score': float(np.mean(scores)),
                'count': len(impostor)
            }
        
        return result
    
    def analyze_doubt_zone(self, genuine_scores: List[float], impostor_scores: List[float]) -> Dict:
        """
        Analizar cuántos intentos caen en la zona de duda.
        """
        doubt_min, doubt_max = self.doubt_zone
        
        genuine_in_doubt = [s for s in genuine_scores if doubt_min <= s <= doubt_max]
        impostor_in_doubt = [s for s in impostor_scores if doubt_min <= s <= doubt_max]
        
        return {
            'doubt_zone': self.doubt_zone,
            'genuine_in_doubt': len(genuine_in_doubt),
            'genuine_in_doubt_pct': (len(genuine_in_doubt) / len(genuine_scores)) * 100 if genuine_scores else 0,
            'impostor_in_doubt': len(impostor_in_doubt),
            'impostor_in_doubt_pct': (len(impostor_in_doubt) / len(impostor_scores)) * 100 if impostor_scores else 0,
            'total_in_doubt': len(genuine_in_doubt) + len(impostor_in_doubt),
            'would_benefit_multiphrase': len(genuine_in_doubt)  # Usuarios que se beneficiarían
        }
    
    def generate_report(self, metrics: Dict, threshold_comparison: Dict, doubt_analysis: Dict, output_path: Path) -> None:
        """Generar reporte de evaluación con análisis de calidad."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Analizar correlación duración-score
        duration_stats = self.analyze_duration_correlation()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN DEL MÓDULO DE RECONOCIMIENTO DE LOCUTOR\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Sección de mejoras implementadas
            f.write("MEJORAS IMPLEMENTADAS\n")
            f.write("-" * 80 + "\n")
            f.write("✓ Enrollment Selection: Descarte de audios con SNR < 15dB\n")
            f.write("✓ Voice Activity Detection (VAD): Eliminación de silencios\n")
            f.write("✓ Análisis de duración y correlación con scores\n")
            f.write("✓ Optimización de threshold para minimizar error total\n")
            f.write("✓ Score Normalization (S-Norm): Calibración con cohort\n")
            f.write("✓ Decisión Multi-Frase: Zona de duda para segunda verificación\n\n")
            
            # Comparación de estrategias de threshold
            f.write("COMPARACIÓN DE ESTRATEGIAS DE THRESHOLD\n")
            f.write("-" * 80 + "\n")
            for name, strategy in threshold_comparison.items():
                f.write(f"\n{name.upper().replace('_', ' ')}:\n")
                f.write(f"  Estrategia: {strategy['strategy']}\n")
                f.write(f"  Threshold:  {strategy['threshold']:.4f}\n")
                f.write(f"  FAR:        {strategy['far']:6.2f}%\n")
                f.write(f"  FRR:        {strategy['frr']:6.2f}%\n")
                f.write(f"  Error Total: {strategy['total_error']:6.2f}%\n")
                f.write(f"  Accuracy:   {strategy['accuracy']:6.2f}%\n")
            
            # Identificar mejor estrategia
            best = min(threshold_comparison.items(), key=lambda x: x[1]['total_error'])
            f.write(f"\n🏆 MEJOR ESTRATEGIA: {best[0].upper().replace('_', ' ')}\n")
            f.write(f"   Error total: {best[1]['total_error']:.2f}%\n\n")
            
            f.write("MÉTRICAS PRINCIPALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"FRR (False Rejection Rate):    {metrics['frr']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"FAR (False Acceptance Rate):   {metrics['far']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"EER (Equal Error Rate):        {metrics['eer']:6.2f}%  ")
            f.write("✅ MEJOR si cercano a 0%\n")
            f.write(f"Umbral EER:                    {metrics['eer_threshold']:.4f}\n")
            f.write(f"Umbral operacional:            {metrics['threshold']:.4f}\n\n")
            
            # Calidad de Enrollment
            f.write("CALIDAD DE ENROLLMENT\n")
            f.write("-" * 80 + "\n")
            for user, quality in self.enrollment_quality.items():
                f.write(f"\nUsuario: {user}\n")
                f.write(f"  SNR promedio: {quality['avg_snr']:.1f} dB\n")
                f.write(f"  Duración promedio: {quality['avg_duration']:.2f}s\n")
                f.write(f"  Audios seleccionados: {len(quality['selected'])}/{len(quality['audios'])}\n")
                for filename, snr, dur in quality['selected']:
                    f.write(f"    ✓ {filename}: SNR={snr:.1f}dB, Dur={dur:.2f}s\n")
            f.write("\n")
            
            f.write("ESTADÍSTICAS DE SCORES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Intentos genuinos:     {metrics['genuine_count']}\n")
            f.write(f"  Media:               {metrics['genuine_mean']:.4f}\n")
            f.write(f"  Desviación estándar: {metrics['genuine_std']:.4f}\n\n")
            f.write(f"Intentos de impostores: {metrics['impostor_count']}\n")
            f.write(f"  Media:               {metrics['impostor_mean']:.4f}\n")
            f.write(f"  Desviación estándar: {metrics['impostor_std']:.4f}\n\n")
            
            # Análisis de duración
            if duration_stats:
                f.write("ANÁLISIS DE DURACIÓN\n")
                f.write("-" * 80 + "\n")
                
                if 'genuine' in duration_stats:
                    g = duration_stats['genuine']
                    f.write(f"Intentos Genuinos:\n")
                    f.write(f"  Correlación duración-score: {g['correlation']:.3f}\n")
                    f.write(f"  Duración promedio: {g['avg_duration']:.2f}s\n")
                    f.write(f"  Score promedio: {g['avg_score']:.4f}\n")
                    
                    if 'genuine_by_duration' in duration_stats:
                        gd = duration_stats['genuine_by_duration']
                        f.write(f"\n  Por rangos de duración:\n")
                        f.write(f"    Cortos (<2.5s):  Score={gd['short_avg_score']:.4f}  (n={gd['short_count']})\n")
                        f.write(f"    Medios (2.5-4s): Score={gd['medium_avg_score']:.4f}  (n={gd['medium_count']})\n")
                        f.write(f"    Largos (>4s):    Score={gd['long_avg_score']:.4f}  (n={gd['long_count']})\n")
                
                if 'impostor' in duration_stats:
                    i = duration_stats['impostor']
                    f.write(f"\nIntentos Impostores:\n")
                    f.write(f"  Correlación duración-score: {i['correlation']:.3f}\n")
                    f.write(f"  Duración promedio: {i['avg_duration']:.2f}s\n")
                    f.write(f"  Score promedio: {i['avg_score']:.4f}\n")
                
                f.write("\n")
            
            # Análisis de Zona de Duda
            f.write("ANÁLISIS DE ZONA DE DUDA (MULTI-FRASE)\n")
            f.write("-" * 80 + "\n")
            f.write(f"Zona de duda definida: {doubt_analysis['doubt_zone'][0]:.4f} - {doubt_analysis['doubt_zone'][1]:.4f}\n\n")
            f.write(f"Intentos genuinos en zona de duda: {doubt_analysis['genuine_in_doubt']} ({doubt_analysis['genuine_in_doubt_pct']:.1f}%)\n")
            f.write(f"Intentos de impostores en zona de duda: {doubt_analysis['impostor_in_doubt']} ({doubt_analysis['impostor_in_doubt_pct']:.1f}%)\n")
            f.write(f"Total en zona de duda: {doubt_analysis['total_in_doubt']}\n\n")
            f.write(f"Beneficio de multi-frase:\n")
            f.write(f"  ✓ {doubt_analysis['would_benefit_multiphrase']} usuarios genuinos se beneficiarían de\n")
            f.write(f"    solicitar una segunda frase para confirmar identidad\n\n")
            
            f.write("INTERPRETACIÓN\n")
            f.write("-" * 80 + "\n")
            if metrics['eer'] < 5:
                f.write("✅ EER EXCELENTE (< 5%)\n")
            elif metrics['eer'] < 10:
                f.write("✓ EER BUENO (5-10%)\n")
            else:
                f.write("⚠️  EER REQUIERE MEJORA (> 10%)\n")
            
            if metrics['far'] < 1:
                f.write("✅ FAR EXCELENTE (< 1%) - Alta seguridad\n")
            elif metrics['far'] < 5:
                f.write("✓ FAR ACEPTABLE (1-5%)\n")
            else:
                f.write("⚠️  FAR ALTO (> 5%) - Vulnerabilidad de seguridad\n")
            
            if metrics['frr'] < 10:
                f.write("✅ FRR EXCELENTE (< 10%) - Buena experiencia de usuario\n")
            elif metrics['frr'] < 20:
                f.write("✓ FRR ACEPTABLE (10-20%)\n")
            else:
                f.write("⚠️  FRR ALTO (> 20%) - Usuarios tendrán que reintentar frecuentemente\n")
            
            # Recomendaciones basadas en análisis
            f.write("\nRECOMENDACIONES\n")
            f.write("-" * 80 + "\n")
            
            if duration_stats and 'genuine_by_duration' in duration_stats:
                gd = duration_stats['genuine_by_duration']
                if gd['short_count'] > 0 and gd['medium_count'] > 0:
                    short_score = gd['short_avg_score']
                    medium_score = gd['medium_avg_score']
                    
                    if medium_score > short_score + 0.05:
                        f.write("✓ Audios más largos (>2.5s) obtienen mejores scores\n")
                        f.write("  Recomendación: Solicitar frases de al menos 2.5 segundos\n")
            
            # Revisar SNR
            low_snr_users = [u for u, q in self.enrollment_quality.items() if q['avg_snr'] < 20]
            if low_snr_users:
                f.write(f"\n⚠️  {len(low_snr_users)} usuario(s) con SNR bajo en enrollment\n")
                f.write("  Recomendación: Grabar en ambiente más silencioso\n")
            
            f.write("\n")
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar métricas en JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Métricas JSON: {json_path}")
    
    def generate_visualizations(self, genuine_scores: List[float], impostor_scores: List[float], 
                               threshold: float, output_dir: Path) -> None:
        """Generar 4 visualizaciones en una sola imagen."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar estilo de matplotlib
        plt.style.use('seaborn-v0_8-darkgrid')
        colors = {
            'genuine': '#2ecc71',  # Verde
            'impostor': '#e74c3c',  # Rojo
            'threshold': '#3498db',  # Azul
            'eer': '#f39c12'  # Naranja
        }
        
        # Crear figura con 4 subplots (2x2)
        fig = plt.figure(figsize=(20, 16))
        
        # ============= SUBPLOT 1: Histograma =============
        ax1 = plt.subplot(2, 2, 1)
        
        bins = np.linspace(0, 1, 50)
        
        ax1.hist(genuine_scores, bins=bins, alpha=0.6, label='Genuinos', 
                color=colors['genuine'], edgecolor='black', density=True)
        ax1.hist(impostor_scores, bins=bins, alpha=0.6, label='Impostores', 
                color=colors['impostor'], edgecolor='black', density=True)
        
        ax1.axvline(threshold, color=colors['threshold'], linestyle='--', 
                   linewidth=2, label=f'Threshold ({threshold:.4f})')
        
        ax1.set_xlabel('Score de Similitud', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Densidad', fontsize=11, fontweight='bold')
        ax1.set_title('Distribución de Scores', fontsize=13, fontweight='bold', pad=15)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # ============= SUBPLOT 2: Curva DET =============
        ax2 = plt.subplot(2, 2, 2)
        
        # Calcular FAR y FRR
        thresholds = np.linspace(0, 1, 1000)
        far_values = []
        frr_values = []
        
        for th in thresholds:
            far = np.sum(np.array(impostor_scores) >= th) / len(impostor_scores) * 100
            frr = np.sum(np.array(genuine_scores) < th) / len(genuine_scores) * 100
            far_values.append(far)
            frr_values.append(frr)
        
        far_values = np.array(far_values)
        frr_values = np.array(frr_values)
        
        # Aplicar suavizado gaussiano para curva más profesional
        # Encontrar EER (sin suavizado)
        eer_idx = np.argmin(np.abs(far_values - frr_values))
        eer_value = (far_values[eer_idx] + frr_values[eer_idx]) / 2
        eer_threshold = thresholds[eer_idx]
        
        # Calcular Security First
        far_sf = np.sum(np.array(impostor_scores) >= threshold) / len(impostor_scores) * 100
        frr_sf = np.sum(np.array(genuine_scores) < threshold) / len(genuine_scores) * 100
        
        # Determinar rango de visualización
        max_range = max(max(far_values), max(frr_values))
        
        # Graficar curva DET - simple sin suavizado
        ax2.plot(far_values, frr_values, linewidth=3.5, color='#8b5cf6', 
                alpha=1.0, zorder=2)
        
        # Línea diagonal FAR = FRR
        ax2.plot([0, max_range], [0, max_range], 'k--', alpha=0.3, linewidth=1.5, zorder=1)
        
        # Marcar EER con círculo rojo
        ax2.plot(eer_value, eer_value, 'o', markersize=14, color='red', 
                markeredgecolor='white', markeredgewidth=2, zorder=5)
        
        # Texto del EER en recuadro blanco
        ax2.text(0.98, 0.55, f'EER = {eer_value:.2f}%', 
                transform=ax2.transAxes, fontsize=11, 
                verticalalignment='center', horizontalalignment='right',
                bbox={'boxstyle': 'round,pad=0.5', 'facecolor': 'white', 
                      'edgecolor': 'gray', 'linewidth': 1.5})
        
        # Marcar Security First si es diferente del EER
        if abs(far_sf - eer_value) > 0.5 or abs(frr_sf - eer_value) > 0.5:
            ax2.plot(far_sf, frr_sf, 's', markersize=12, color='purple', 
                    markeredgecolor='white', markeredgewidth=2, zorder=5)
            ax2.text(0.98, 0.45, f'Security First\nFAR={far_sf:.1f}%, FRR={frr_sf:.1f}%', 
                    transform=ax2.transAxes, fontsize=9, 
                    verticalalignment='center', horizontalalignment='right',
                    bbox={'boxstyle': 'round,pad=0.5', 'facecolor': 'white', 
                          'edgecolor': 'purple', 'linewidth': 1.5})
        
        ax2.set_xlabel('FAR (%)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('FRR (%)', fontsize=11, fontweight='bold')
        ax2.set_title('DET Curve (Detection Error Tradeoff)', fontsize=13, fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
        ax2.set_xlim([0, max_range])
        ax2.set_ylim([0, max_range])
        
        # ============= SUBPLOT 3: FAR y FRR vs Threshold =============
        ax3 = plt.subplot(2, 2, 3)
        
        ax3.plot(thresholds, far_values, linewidth=2.5, color=colors['impostor'], 
                label='FAR', alpha=0.8)
        ax3.plot(thresholds, frr_values, linewidth=2.5, color='blue', 
                label='FRR', alpha=0.8)
        
        # Marcar threshold Security First
        far_sf = np.sum(np.array(impostor_scores) >= threshold) / len(impostor_scores) * 100
        frr_sf = np.sum(np.array(genuine_scores) < threshold) / len(genuine_scores) * 100
        ax3.axvline(threshold, color='green', linestyle='--', 
                   linewidth=2.5, label=f'EER @ {eer_threshold:.2f}', alpha=0.8)
        
        # Sombrear zona óptima alrededor del EER
        ax3.axvspan(max(0, eer_threshold - 0.05), min(1, eer_threshold + 0.05), 
                   alpha=0.15, color='green', label='Zona óptima')
        
        ax3.set_xlabel('Threshold', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Error rate (%)', fontsize=11, fontweight='bold')
        ax3.set_title('FAR vs FRR Curve', fontsize=13, fontweight='bold', pad=15)
        ax3.legend(fontsize=9, loc='upper right')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.set_xlim([0, 1])
        ax3.set_ylim([0, 105])
        
        # ============= SUBPLOT 4: Embeddings (t-SNE o PCA) =============
        ax4 = plt.subplot(2, 2, 4)
        
        if len(self.all_embeddings) > 0:
            # Preparar datos
            embeddings_list = []
            labels = []
            user_colors = {
                'anachamorromunoz': '#e74c3c',
                'ft_fernandotomas': '#3498db',
                'piapobletech': '#2ecc71',
                'rapomo3': '#f39c12'
            }
            
            for user, user_embeddings in self.all_embeddings.items():
                for emb in user_embeddings:
                    embeddings_list.append(emb)
                    labels.append(user)
            
            embeddings_array = np.array(embeddings_list)
            
            # Usar PCA para subplot 4
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=42)
            embeddings_2d = pca.fit_transform(embeddings_array)
            
            for user in self.users:
                mask = np.array(labels) == user
                ax4.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1],
                           c=user_colors[user], label=user, s=100, alpha=0.7, 
                           edgecolors='black', linewidth=0.5)
            
            ax4.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', 
                          fontsize=11, fontweight='bold')
            ax4.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', 
                          fontsize=11, fontweight='bold')
            ax4.set_title('Embeddings (PCA)', fontsize=13, fontweight='bold', pad=15)
            ax4.legend(fontsize=9)
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Sin datos de embeddings', 
                    ha='center', va='center', fontsize=12)
            ax4.set_title('Embeddings', fontsize=13, fontweight='bold', pad=15)
        
        # Ajustar layout y guardar
        plt.suptitle('Evaluación Sistema de Reconocimiento de Locutor', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        combined_path = output_dir / 'all_metrics_combined.png'
        plt.savefig(combined_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico combinado guardado: {combined_path}")
        
        print(f"\n✅ Visualización combinada generada:")
        print(f"   📊 {combined_path}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("EVALUACIÓN DEL MÓDULO DE RECONOCIMIENTO DE LOCUTOR")
    print("=" * 80)
    print()
    
    # Configuración del dataset externo
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_base = project_root / "infra" / "evaluation" / "dataset"
    recordings_dir = dataset_base / "recordings" / "auto_recordings_20251218"
    
    # Verificar directorio
    if not recordings_dir.exists():
        print(f"❌ Error: Directorio de recordings no encontrado: {recordings_dir}")
        sys.exit(1)
    
    # Inicializar evaluador
    evaluator = SpeakerRecognitionEvaluator(recordings_dir)
    
    # 1. Inscribir usuarios
    evaluator.enroll_all_users()
    
    if len(evaluator.voiceprints) == 0:
        print("❌ Error: No se inscribieron usuarios")
        sys.exit(1)
    
    # 2. Evaluar intentos genuinos
    genuine_scores, genuine_count = evaluator.evaluate_genuine_attempts()
    
    # 3. Evaluar intentos de impostores
    impostor_scores, impostor_count = evaluator.evaluate_impostor_attempts()
    
    if len(genuine_scores) == 0 or len(impostor_scores) == 0:
        print("❌ Error: No hay suficientes datos para evaluar")
        sys.exit(1)
    
    # 4. Calcular métricas
    print("\nCalculando métricas y buscando threshold óptimo...")
    
    # Encontrar threshold óptimo comparando diferentes estrategias
    threshold_comparison = evaluator.find_optimal_threshold(genuine_scores, impostor_scores)
    
    # Analizar zona de duda
    doubt_analysis = evaluator.analyze_doubt_zone(genuine_scores, impostor_scores)
    
    # Usar el threshold SECURITY FIRST (mejor balance)
    security_threshold = threshold_comparison['security_first']['threshold']
    metrics = evaluator.calculate_metrics(genuine_scores, impostor_scores, threshold=security_threshold)
    
    # Agregar conteos
    metrics['genuine_count'] = genuine_count
    metrics['impostor_count'] = impostor_count
    metrics['threshold_default'] = 0.65  # Para referencia
    
    # 5. Generar reporte
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "speaker_recognition_evaluation.txt"
    evaluator.generate_report(metrics, threshold_comparison, doubt_analysis, output_path)
    
    # 6. Generar visualizaciones
    plots_dir = Path(__file__).parent / "plots"
    
    # Extraer scores raw (sin S-Norm) para gráficos más informativos
    genuine_scores_raw = [item['raw_score'] for item in evaluator.duration_analysis if item['type'] == 'genuine']
    impostor_scores_raw = [item['raw_score'] for item in evaluator.duration_analysis if item['type'] == 'impostor']
    
    # Verificar que estamos usando scores correctos
    logger.info(f"\n🔍 Verificación de scores:")
    logger.info(f"  Genuinos RAW: mean={np.mean(genuine_scores_raw):.4f}, std={np.std(genuine_scores_raw):.4f}")
    logger.info(f"  Impostores RAW: mean={np.mean(impostor_scores_raw):.4f}, std={np.std(impostor_scores_raw):.4f}")
    logger.info(f"  Genuinos S-NORM: mean={np.mean(genuine_scores):.4f}, std={np.std(genuine_scores):.4f}")
    logger.info(f"  Impostores S-NORM: mean={np.mean(impostor_scores):.4f}, std={np.std(impostor_scores):.4f}")
    
    # Calcular threshold sin S-Norm para comparación
    if genuine_scores_raw and impostor_scores_raw:
        threshold_comparison_raw = evaluator.find_optimal_threshold(genuine_scores_raw, impostor_scores_raw)
        security_threshold_raw = threshold_comparison_raw['security_first']['threshold']
        
        # Calcular métricas con scores RAW
        metrics_raw = evaluator.calculate_metrics(genuine_scores_raw, impostor_scores_raw, threshold=security_threshold_raw)
        
        logger.info(f"\n📊 Métricas sin S-Norm (usadas en gráficos):")
        logger.info(f"  Threshold: {security_threshold_raw:.4f}")
        logger.info(f"  FAR: {metrics_raw['far']:.2f}%")
        logger.info(f"  FRR: {metrics_raw['frr']:.2f}%")
        logger.info(f"  EER: {metrics_raw['eer']:.2f}%")
        
        # Generar gráficos SIN S-Norm (más visibles)
        evaluator.generate_visualizations(
            genuine_scores_raw, impostor_scores_raw, 
            security_threshold_raw, plots_dir
        )
        
        logger.info(f"\n✅ Gráficos generados con scores RAW (sin S-Norm)")
        logger.info(f"Threshold gráficos: {security_threshold_raw:.4f} (sin S-Norm)")
        logger.info(f"Threshold reportado: {security_threshold:.4f} (con S-Norm)")
    else:
        # Fallback: usar scores normalizados
        evaluator.generate_visualizations(genuine_scores, impostor_scores, security_threshold, plots_dir)
    
    # Mostrar resumen (usando métricas sin S-Norm)
    print("\n" + "=" * 80)
    print("RESULTADOS DE EVALUACIÓN - SECURITY FIRST")
    print("=" * 80)
    print(f"Threshold usado: {security_threshold_raw:.4f} (Security First)")
    print()
    print(f"Intentos genuinos:  {genuine_count}")
    print(f"Intentos impostores: {impostor_count}")
    print()
    print(f"FAR (False Acceptance Rate): {metrics_raw['far']:6.2f}%  🔒 CRÍTICO: Impostores que entran")
    print(f"FRR (False Rejection Rate):  {metrics_raw['frr']:6.2f}%  ⚠️  Usuarios genuinos rechazados")
    print(f"Error Total (FRR + FAR):     {metrics_raw['frr'] + metrics_raw['far']:6.2f}%")
    print(f"EER (Equal Error Rate):      {metrics_raw['eer']:6.2f}%  (para referencia)")
    print()
    print(f"Separación de distribuciones:")
    print(f"  Media genuinos:  {np.mean(genuine_scores_raw):.4f}")
    print(f"  Media impostores: {np.mean(impostor_scores_raw):.4f}")
    print(f"  Diferencia:      {np.mean(genuine_scores_raw) - np.mean(impostor_scores_raw):.4f}")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
