"""
Anti-Spoofing Evaluation Script

Evaluates the anti-spoofing module (AASIST, RawNet2, ResNet ensemble).
Tests with genuine audios vs. spoofed/synthetic audios.

Usage:
    python evaluate_antispoofing.py --dataset asvspoof --model ensemble
    python evaluate_antispoofing.py --dataset asvspoof --model aasist
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from evaluation.metrics_calculator import BiometricScores, BiometricMetrics
from evaluation.results_manager import (
    ResultsManager, ExperimentMetadata, TestResult, generate_experiment_id
)

# Import biometric components
try:
    from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
except ImportError as e:
    print(f"Error importing biometric components: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)


class AntiSpoofingEvaluator:
    """
    Evaluator for anti-spoofing module.
    
    Tests genuine vs. spoofed audios using direct injection into SpoofDetectorAdapter.
    """
    
    def __init__(self, model_name: str = "ensemble_antispoofing"):
        """
        Initialize evaluator.
        
        Args:
            model_name: Name of anti-spoofing model to use
        """
        self.model_name = model_name
        self.results_manager = ResultsManager()
        
        # Initialize spoof detector
        logger.info(f"Initializing SpoofDetectorAdapter with model: {model_name}")
        self.spoof_detector = SpoofDetectorAdapter(model_name=model_name, use_gpu=True)
        
    def load_audio_file(self, audio_path: Path) -> bytes:
        """Load audio file as bytes."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def evaluate_genuine_audios(
        self,
        genuine_paths: List[str],
        dataset_dir: Path
    ) -> Tuple[List[float], List[TestResult]]:
        """
        Evaluate genuine (bonafide) audios.
        
        These should have LOW spoof probability.
        
        Args:
            genuine_paths: List of paths to genuine audio files
            dataset_dir: Base dataset directory
            
        Returns:
            Tuple of (spoof_probabilities, test_results)
        """
        logger.info(f"Evaluating {len(genuine_paths)} genuine audios...")
        
        scores = []
        results = []
        
        for i, audio_path_str in enumerate(genuine_paths, 1):
            test_id = f"genuine_{i:04d}"
            audio_path = dataset_dir / audio_path_str
            
            if not audio_path.exists():
                logger.warning(f"  Audio not found: {audio_path}")
                continue
            
            try:
                # Load audio
                audio_data = self.load_audio_file(audio_path)
                
                # Detect spoofing
                spoof_prob = self.spoof_detector.detect_spoof(audio_data)
                scores.append(spoof_prob)
                
                # Create test result
                result = TestResult(
                    test_id=test_id,
                    test_type="genuine",
                    spoof_probability=spoof_prob,
                    label="genuine",
                    timestamp=datetime.now().isoformat(),
                    notes=f"Audio: {audio_path.name}"
                )
                results.append(result)
                
                if i % 50 == 0:
                    logger.info(f"  Processed {i}/{len(genuine_paths)} genuine audios")
                
            except Exception as e:
                logger.error(f"  Failed test {test_id}: {e}")
        
        logger.info(f"Genuine audios complete: {len(scores)} tests, mean spoof prob: {np.mean(scores):.3f}")
        return scores, results
    
    def evaluate_spoofed_audios(
        self,
        spoofed_paths: List[str],
        dataset_dir: Path,
        attack_types: Dict[str, str] = None
    ) -> Tuple[List[float], List[TestResult]]:
        """
        Evaluate spoofed/synthetic audios.
        
        These should have HIGH spoof probability.
        
        Args:
            spoofed_paths: List of paths to spoofed audio files
            dataset_dir: Base dataset directory
            attack_types: Optional dict mapping audio path to attack type
            
        Returns:
            Tuple of (spoof_probabilities, test_results)
        """
        logger.info(f"Evaluating {len(spoofed_paths)} spoofed audios...")
        
        scores = []
        results = []
        
        for i, audio_path_str in enumerate(spoofed_paths, 1):
            test_id = f"spoofed_{i:04d}"
            audio_path = dataset_dir / audio_path_str
            
            if not audio_path.exists():
                logger.warning(f"  Audio not found: {audio_path}")
                continue
            
            try:
                # Load audio
                audio_data = self.load_audio_file(audio_path)
                
                # Detect spoofing
                spoof_prob = self.spoof_detector.detect_spoof(audio_data)
                scores.append(spoof_prob)
                
                # Get attack type if available
                attack_type = None
                if attack_types:
                    attack_type = attack_types.get(audio_path_str, "unknown")
                
                # Create test result
                result = TestResult(
                    test_id=test_id,
                    test_type="spoof",
                    spoof_probability=spoof_prob,
                    label="spoof",
                    timestamp=datetime.now().isoformat(),
                    notes=f"Attack: {attack_type}, Audio: {audio_path.name}" if attack_type else f"Audio: {audio_path.name}"
                )
                results.append(result)
                
                if i % 50 == 0:
                    logger.info(f"  Processed {i}/{len(spoofed_paths)} spoofed audios")
                
            except Exception as e:
                logger.error(f"  Failed test {test_id}: {e}")
        
        logger.info(f"Spoofed audios complete: {len(scores)} tests, mean spoof prob: {np.mean(scores):.3f}")
        return scores, results
    
    def run_evaluation(
        self,
        genuine_paths: List[str],
        spoofed_paths: List[str],
        dataset_dir: Path,
        experiment_name: str = "antispoofing",
        attack_types: Dict[str, str] = None
    ) -> Path:
        """
        Run complete anti-spoofing evaluation.
        
        Args:
            genuine_paths: List of genuine audio paths
            spoofed_paths: List of spoofed audio paths
            dataset_dir: Dataset directory
            experiment_name: Experiment name
            attack_types: Optional attack type mapping
            
        Returns:
            Path to results file
        """
        # Step 1: Evaluate genuine audios (should have LOW spoof prob)
        genuine_scores, genuine_results = self.evaluate_genuine_audios(
            genuine_paths, dataset_dir
        )
        
        # Step 2: Evaluate spoofed audios (should have HIGH spoof prob)
        spoofed_scores, spoofed_results = self.evaluate_spoofed_audios(
            spoofed_paths, dataset_dir, attack_types
        )
        
        # Step 3: Calculate metrics
        # For anti-spoofing: genuine = bonafide (low scores), impostor = spoof (high scores)
        # We invert the interpretation: treat genuine as "should be accepted" (low spoof prob)
        if len(genuine_scores) > 0 and len(spoofed_scores) > 0:
            # Convert to similarity-like scores (1 - spoof_prob) for genuine
            # Keep spoof_prob as-is for spoofed (higher is more spoofed)
            genuine_as_similarity = 1 - np.array(genuine_scores)  # High = good (not spoofed)
            spoofed_as_similarity = 1 - np.array(spoofed_scores)  # Low = good (detected as spoof)
            
            biometric_scores = BiometricScores(
                genuine_scores=genuine_as_similarity,
                impostor_scores=spoofed_as_similarity
            )
            
            metrics_calc = BiometricMetrics(biometric_scores)
            eer_result = metrics_calc.find_eer()
            statistics = metrics_calc.get_statistics()
            
            metrics = {
                "eer_spoof": eer_result.eer,
                "eer_threshold": eer_result.eer_threshold,
                "far_spoof_at_eer": eer_result.far,  # Spoof accepted as genuine
                "frr_spoof_at_eer": eer_result.frr,  # Genuine rejected as spoof
                "model_name": self.model_name,
                "genuine_spoof_prob_mean": float(np.mean(genuine_scores)),
                "genuine_spoof_prob_std": float(np.std(genuine_scores)),
                "spoofed_spoof_prob_mean": float(np.mean(spoofed_scores)),
                "spoofed_spoof_prob_std": float(np.std(spoofed_scores)),
            }
            
            logger.info(f"\n{'='*60}")
            logger.info(f"ANTI-SPOOFING RESULTS: {experiment_name}")
            logger.info(f"Model: {self.model_name}")
            logger.info(f"{'='*60}")
            logger.info(f"EER: {eer_result.eer:.3%} at threshold {eer_result.eer_threshold:.3f}")
            logger.info(f"Genuine (bonafide): {len(genuine_scores)} tests, spoof_prob μ={np.mean(genuine_scores):.3f}")
            logger.info(f"Spoofed (attacks): {len(spoofed_scores)} tests, spoof_prob μ={np.mean(spoofed_scores):.3f}")
            logger.info(f"{'='*60}\n")
        else:
            metrics = {}
            logger.warning("Insufficient data to calculate metrics")
        
        # Step 4: Save results
        experiment_id = generate_experiment_id("antispoofing", f"{experiment_name}_{self.model_name}")
        metadata = ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_type="anti_spoofing",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            dataset=experiment_name,
            description=f"Anti-spoofing evaluation ({self.model_name}): {len(genuine_scores)} genuine, {len(spoofed_scores)} spoofed"
        )
        
        all_results = genuine_results + spoofed_results
        filepath = self.results_manager.save_experiment(metadata, all_results, metrics)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath


def load_example_config():
    """
    Return example configuration.
    
    In production, load from dataset/asvspoof_config.json
    """
    return {
        "genuine": [
            "bonafide/audio_001.wav",
            "bonafide/audio_002.wav",
        ],
        "spoofed": [
            "spoof/A01_001.wav",  # TTS attack
            "spoof/A02_001.wav",  # VC attack
        ],
        "attack_types": {
            "spoof/A01_001.wav": "TTS",
            "spoof/A02_001.wav": "VC",
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate anti-spoofing module")
    parser.add_argument("--dataset", type=str, default="dataset",
                        help="Dataset directory path")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to configuration JSON file")
    parser.add_argument("--model", type=str, default="ensemble_antispoofing",
                        choices=["ensemble_antispoofing", "aasist_antispoofing", 
                                 "rawnet2_antispoofing", "resnet_antispoofing"],
                        help="Anti-spoofing model to evaluate")
    parser.add_argument("--name", type=str, default="antispoofing_eval",
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
        print("In production, provide config with: --config dataset/asvspoof_config.json")
        config = load_example_config()
    
    # Run evaluation
    evaluator = AntiSpoofingEvaluator(model_name=args.model)
    
    try:
        result_path = evaluator.run_evaluation(
            genuine_paths=config["genuine"],
            spoofed_paths=config["spoofed"],
            dataset_dir=Path(args.dataset),
            experiment_name=args.name,
            attack_types=config.get("attack_types")
        )
        print(f"\n✓ Evaluation complete! Results: {result_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
