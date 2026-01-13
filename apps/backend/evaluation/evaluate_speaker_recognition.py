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
        
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno entre embeddings."""
        norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        similarity = np.dot(norm1, norm2)
        return float(max(0.0, min(1.0, similarity)))
    
    def enroll_user(self, user: str) -> np.ndarray:
        """
        Inscribir usuario creando voiceprint con audios de enrollment.
        
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
        
        # Extraer embeddings de los 3 audios de enrollment
        embeddings = []
        for audio_file in enrollment_files[:3]:
            audio_data = self.load_audio(audio_file)
            embedding = self.speaker_adapter.extract_embedding(audio_data, audio_format="wav")
            embeddings.append(embedding)
            logger.debug(f"  Enrollment: {audio_file.name}")
        
        # Crear voiceprint promedio
        voiceprint = np.mean(embeddings, axis=0)
        
        logger.info(f"  ✓ Usuario {user} inscrito con {len(embeddings)} muestras")
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
                test_embedding = self.speaker_adapter.extract_embedding(audio_data, audio_format="wav")
                similarity = self.calculate_similarity(voiceprint, test_embedding)
                genuine_scores.append(similarity)
                comparisons += 1
                logger.debug(f"    {audio_file.name}: {similarity:.4f}")
        
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
                    test_embedding = self.speaker_adapter.extract_embedding(audio_data, audio_format="wav")
                    similarity = self.calculate_similarity(claimed_voiceprint, test_embedding)
                    impostor_scores.append(similarity)
                    comparisons += 1
                    logger.debug(f"    {audio_file.name} vs {claimed_user}: {similarity:.4f}")
        
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
    
    def generate_report(self, metrics: Dict, output_path: Path) -> None:
        """Generar reporte de evaluación."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUACIÓN DEL MÓDULO DE RECONOCIMIENTO DE LOCUTOR\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
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
            
            f.write("ESTADÍSTICAS DE SCORES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Intentos genuinos:     {metrics['genuine_count']}\n")
            f.write(f"  Media:               {metrics['genuine_mean']:.4f}\n")
            f.write(f"  Desviación estándar: {metrics['genuine_std']:.4f}\n\n")
            f.write(f"Intentos de impostores: {metrics['impostor_count']}\n")
            f.write(f"  Media:               {metrics['impostor_mean']:.4f}\n")
            f.write(f"  Desviación estándar: {metrics['impostor_std']:.4f}\n\n")
            
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
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar métricas en JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Métricas JSON: {json_path}")


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
    print("\nCalculando métricas...")
    metrics = evaluator.calculate_metrics(genuine_scores, impostor_scores)
    metrics['genuine_count'] = genuine_count
    metrics['impostor_count'] = impostor_count
    
    # 5. Generar reporte
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "speaker_recognition_evaluation.txt"
    evaluator.generate_report(metrics, output_path)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"Intentos genuinos:  {genuine_count}")
    print(f"Intentos impostores: {impostor_count}")
    print()
    print(f"FRR (False Rejection Rate):  {metrics['frr']:6.2f}%  ✅ Menor es mejor")
    print(f"FAR (False Acceptance Rate): {metrics['far']:6.2f}%  ✅ Menor es mejor")
    print(f"EER (Equal Error Rate):      {metrics['eer']:6.2f}%  ✅ Menor es mejor")
    print()
    print(f"Reporte completo: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
