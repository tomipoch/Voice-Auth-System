"""
Speaker Verification Evaluation Script

Evaluates the speaker verification module using direct injection into biometric layers.
Tests with enrollment, genuine attempts, and impostor attempts.

Usage:
    python evaluate_speaker_verification.py --mode enrollment --dataset voxceleb_mini
    python evaluate_speaker_verification.py --mode test --dataset voxceleb_mini
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from evaluation.metrics_calculator import BiometricScores, BiometricMetrics
from evaluation.results_manager import (
    ResultsManager, ExperimentMetadata, TestResult, generate_experiment_id
)

# Import biometric components
try:
    from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
    from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION
except ImportError as e:
    print(f"Error importing biometric components: {e}")
    print("Make sure you're running from the Backend directory")
    sys.exit(1)

logger = logging.getLogger(__name__)


class SpeakerVerificationEvaluator:
    """
    Evaluator for speaker verification module.
    
    Uses direct injection into SpeakerEmbeddingAdapter to extract embeddings
    and calculate similarity scores without going through API layer.
    """
    
    def __init__(self, dataset_dir: Path):
        """
        Initialize evaluator.
        
        Args:
            dataset_dir: Path to dataset directory
        """
        self.dataset_dir = Path(dataset_dir)
        self.results_manager = ResultsManager()
        
        # Initialize speaker embedding adapter
        logger.info("Initializing SpeakerEmbeddingAdapter...")
        self.speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
        
        # Storage for voiceprints (user_id -> embedding)
        self.voiceprints: Dict[str, np.ndarray] = {}
    
    def load_audio_file(self, audio_path: Path) -> bytes:
        """Load audio file as bytes."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score [0, 1]
        """
        # Normalize
        norm1 = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        norm2 = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        # Cosine similarity
        similarity = np.dot(norm1, norm2)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, similarity)))
    
    def enroll_users(self, enrollment_config: Dict) -> Dict[str, np.ndarray]:
        """
        Enroll users by creating voiceprints from enrollment audios.
        
        Args:
            enrollment_config: Dict with user_id -> list of audio paths
            
        Returns:
            Dict of user_id -> voiceprint embedding
        """
        logger.info(f"Enrolling {len(enrollment_config)} users...")
        
        voiceprints = {}
        
        for user_id, audio_paths in enrollment_config.items():
            logger.info(f"  Enrolling user: {user_id} with {len(audio_paths)} audios")
            
            embeddings = []
            for audio_path_str in audio_paths:
                audio_path = self.dataset_dir / audio_path_str
                
                if not audio_path.exists():
                    logger.warning(f"    Audio not found: {audio_path}")
                    continue
                
                # Load audio
                audio_data = self.load_audio_file(audio_path)
                
                # Extract embedding
                try:
                    embedding = self.speaker_adapter.extract_embedding(
                        audio_data,
                        audio_format=audio_path.suffix[1:]  # Remove leading dot
                    )
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"    Failed to extract embedding from {audio_path}: {e}")
            
            if embeddings:
                # Average embeddings to create voiceprint
                voiceprint = np.mean(embeddings, axis=0).astype(np.float32)
                voiceprints[user_id] = voiceprint
                logger.info(f"    ✓ Created voiceprint from {len(embeddings)} audios")
            else:
                logger.warning(f"    ✗ No valid embeddings for {user_id}")
        
        self.voiceprints = voiceprints
        logger.info(f"Enrollment complete: {len(voiceprints)} users enrolled")
        return voiceprints
    
    def evaluate_genuine_tests(
        self,
        genuine_config: Dict[str, List[str]]
    ) -> Tuple[List[float], List[TestResult]]:
        """
        Test genuine attempts (same user verifying).
        
        Args:
            genuine_config: Dict with user_id -> list of test audio paths
            
        Returns:
            Tuple of (similarity_scores, test_results)
        """
        logger.info("Evaluating genuine tests...")
        
        scores = []
        results = []
        test_count = 0
        
        for user_id, audio_paths in genuine_config.items():
            if user_id not in self.voiceprints:
                logger.warning(f"  Skipping {user_id}: not enrolled")
                continue
            
            voiceprint = self.voiceprints[user_id]
            
            for audio_path_str in audio_paths:
                test_count += 1
                test_id = f"genuine_{test_count:04d}"
                audio_path = self.dataset_dir / audio_path_str
                
                if not audio_path.exists():
                    logger.warning(f"  Audio not found: {audio_path}")
                    continue
                
                try:
                    # Extract embedding
                    audio_data = self.load_audio_file(audio_path)
                    embedding = self.speaker_adapter.extract_embedding(
                        audio_data,
                        audio_format=audio_path.suffix[1:]
                    )
                    
                    # Calculate similarity
                    similarity = self.calculate_similarity(embedding, voiceprint)
                    scores.append(similarity)
                    
                    # Create test result
                    result = TestResult(
                        test_id=test_id,
                        test_type="genuine",
                        user_id=user_id,
                        similarity_score=similarity,
                        label="genuine",
                        timestamp=datetime.now().isoformat(),
                        notes=f"Audio: {audio_path.name}"
                    )
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"  Failed test {test_id}: {e}")
        
        logger.info(f"Genuine tests complete: {len(scores)} tests, mean score: {np.mean(scores):.3f}")
        return scores, results
    
    def evaluate_impostor_tests(
        self,
        impostor_config: Dict[str, Dict[str, List[str]]]
    ) -> Tuple[List[float], List[TestResult]]:
        """
        Test impostor attempts (different user attempting to verify).
        
        Args:
            impostor_config: Dict with claimed_user_id -> { actual_user_id -> audio_paths }
            
        Returns:
            Tuple of (similarity_scores, test_results)
        """
        logger.info("Evaluating impostor tests...")
        
        scores = []
        results = []
        test_count = 0
        
        for claimed_user, impostors in impostor_config.items():
            if claimed_user not in self.voiceprints:
                logger.warning(f"  Skipping {claimed_user}: not enrolled")
                continue
            
            voiceprint = self.voiceprints[claimed_user]
            
            for impostor_user, audio_paths in impostors.items():
                for audio_path_str in audio_paths:
                    test_count += 1
                    test_id = f"impostor_{test_count:04d}"
                    audio_path = self.dataset_dir / audio_path_str
                    
                    if not audio_path.exists():
                        logger.warning(f"  Audio not found: {audio_path}")
                        continue
                    
                    try:
                        # Extract embedding
                        audio_data = self.load_audio_file(audio_path)
                        embedding = self.speaker_adapter.extract_embedding(
                            audio_data,
                            audio_format=audio_path.suffix[1:]
                        )
                        
                        # Calculate similarity
                        similarity = self.calculate_similarity(embedding, voiceprint)
                        scores.append(similarity)
                        
                        # Create test result
                        result = TestResult(
                            test_id=test_id,
                            test_type="impostor",
                            user_id=f"{impostor_user} -> {claimed_user}",
                            similarity_score=similarity,
                            label="impostor",
                            timestamp=datetime.now().isoformat(),
                            notes=f"{impostor_user} attempting as {claimed_user}: {audio_path.name}"
                        )
                        results.append(result)
                        
                    except Exception as e:
                        logger.error(f"  Failed test {test_id}: {e}")
        
        logger.info(f"Impostor tests complete: {len(scores)} tests, mean score: {np.mean(scores):.3f}")
        return scores, results
    
    def run_evaluation(
        self,
        enrollment_config: Dict,
        genuine_config: Dict,
        impostor_config: Dict,
        experiment_name: str = "speaker_verification"
    ) -> Path:
        """
        Run complete speaker verification evaluation.
        
        Args:
            enrollment_config: Enrollment configuration
            genuine_config: Genuine test configuration
            impostor_config: Impostor test configuration
            experiment_name: Name for this experiment
            
        Returns:
            Path to results file
        """
        # Step 1: Enrollment
        self.enroll_users(enrollment_config)
        
        # Step 2: Genuine tests
        genuine_scores, genuine_results = self.evaluate_genuine_tests(genuine_config)
        
        # Step 3: Impostor tests
        impostor_scores, impostor_results = self.evaluate_impostor_tests(impostor_config)
        
        # Step 4: Calculate metrics
        if len(genuine_scores) > 0 and len(impostor_scores) > 0:
            biometric_scores = BiometricScores(
                genuine_scores=np.array(genuine_scores),
                impostor_scores=np.array(impostor_scores)
            )
            
            metrics_calc = BiometricMetrics(biometric_scores)
            eer_result = metrics_calc.find_eer()
            statistics = metrics_calc.get_statistics()
            
            metrics = {
                "eer": eer_result.eer,
                "eer_threshold": eer_result.eer_threshold,
                "far_at_eer": eer_result.far,
                "frr_at_eer": eer_result.frr,
                **statistics
            }
            
            logger.info(f"\n{'='*60}")
            logger.info(f"RESULTS: {experiment_name}")
            logger.info(f"{'='*60}")
            logger.info(f"EER: {eer_result.eer:.3%} at threshold {eer_result.eer_threshold:.3f}")
            logger.info(f"Genuine: {len(genuine_scores)} tests, μ={statistics['genuine_mean']:.3f}")
            logger.info(f"Impostor: {len(impostor_scores)} tests, μ={statistics['impostor_mean']:.3f}")
            logger.info(f"{'='*60}\n")
        else:
            metrics = {}
            logger.warning("Insufficient data to calculate metrics")
        
        # Step 5: Save results
        experiment_id = generate_experiment_id("speaker_verification", experiment_name)
        metadata = ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_type="speaker_verification",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            dataset=experiment_name,
            description=f"Speaker verification evaluation: {len(genuine_scores)} genuine, {len(impostor_scores)} impostor"
        )
        
        all_results = genuine_results + impostor_results
        filepath = self.results_manager.save_experiment(metadata, all_results, metrics)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath


def load_example_config():
    """
    Return example configuration for testing with dummy data.
    
    In production, this would be loaded from dataset/voxceleb_config.json or similar.
    """
    # This is just a template - actual paths should come from dataset
    return {
        "enrollment": {
            "user_001": ["user_001/audio_01.wav", "user_001/audio_02.wav", "user_001/audio_03.wav"],
            "user_002": ["user_002/audio_01.wav", "user_002/audio_02.wav", "user_002/audio_03.wav"],
        },
        "genuine": {
            "user_001": ["user_001/test_01.wav", "user_001/test_02.wav"],
            "user_002": ["user_002/test_01.wav", "user_002/test_02.wav"],
        },
        "impostor": {
            "user_001": {
                "user_002": ["user_002/test_01.wav"],  # user_002 trying to be user_001
            },
            "user_002": {
                "user_001": ["user_001/test_01.wav"],  # user_001 trying to be user_002
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate speaker verification module")
    parser.add_argument("--dataset", type=str, default="dataset",
                        help="Dataset directory path")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to configuration JSON file")
    parser.add_argument("--name", type=str, default="speaker_verification_eval",
                        help="Experiment name")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        print("WARNING: No config file provided, using example configuration")
        print("In production, provide config with: --config dataset/voxceleb_config.json")
        config = load_example_config()
    
    # Run evaluation
    evaluator = SpeakerVerificationEvaluator(dataset_dir=args.dataset)
    
    try:
        result_path = evaluator.run_evaluation(
            enrollment_config=config["enrollment"],
            genuine_config=config["genuine"],
            impostor_config=config["impostor"],
            experiment_name=args.name
        )
        print(f"\n✓ Evaluation complete! Results: {result_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
