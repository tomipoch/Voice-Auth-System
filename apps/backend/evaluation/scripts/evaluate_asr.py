"""
ASR (Automatic Speech Recognition) Evaluation Script

Evaluates the ASR module for phrase matching accuracy and Word Error Rate (WER).

Usage:
    python evaluate_asr.py --dataset phrases_dataset --config asr_config.json
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

from evaluation.metrics_calculator import calculate_wer
from evaluation.results_manager import (
    ResultsManager, ExperimentMetadata, TestResult, generate_experiment_id
)

# Import biometric components
try:
    from src.infrastructure.biometrics.ASRAdapter import ASRAdapter
except ImportError as e:
    print(f"Error importing biometric components: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)


class ASREvaluator:
    """
    Evaluator for ASR module.
    
    Tests transcription accuracy and phrase matching capabilities.
    """
    
    def __init__(self):
        """Initialize evaluator."""
        self.results_manager = ResultsManager()
        
        # Initialize ASR adapter
        logger.info("Initializing ASRAdapter...")
        self.asr_adapter = ASRAdapter(use_gpu=True)
    
    def load_audio_file(self, audio_path: Path) -> bytes:
        """Load audio file as bytes."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def evaluate_transcription_accuracy(
        self,
        test_cases: List[Dict[str, str]],
        dataset_dir: Path
    ) -> Tuple[List[float], List[TestResult]]:
        """
        Evaluate transcription accuracy using WER.
        
        Args:
            test_cases: List of dicts with 'audio_path' and 'reference_text'
            dataset_dir: Dataset directory
            
        Returns:
            Tuple of (wer_scores, test_results)
        """
        logger.info(f"Evaluating transcription accuracy on {len(test_cases)} cases...")
        
        wer_scores = []
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = f"wer_{i:04d}"
            audio_path = dataset_dir / test_case["audio_path"]
            reference_text = test_case["reference_text"]
            
            if not audio_path.exists():
                logger.warning(f"  Audio not found: {audio_path}")
                continue
            
            try:
                # Load audio
                audio_data = self.load_audio_file(audio_path)
                
                # Transcribe
                transcribed_text = self.asr_adapter.transcribe(audio_data)
                
                # Calculate WER
                wer = calculate_wer(reference_text, transcribed_text)
                wer_scores.append(wer)
                
                # Create test result
                result = TestResult(
                    test_id=test_id,
                    test_type="transcription",
                    label=reference_text,
                    notes=f"Transcribed: '{transcribed_text}', WER: {wer:.3f}",
                    timestamp=datetime.now().isoformat()
                )
                results.append(result)
                
                if i % 20 == 0:
                    logger.info(f"  Processed {i}/{len(test_cases)} transcriptions")
                
            except Exception as e:
                logger.error(f"  Failed test {test_id}: {e}")
        
        mean_wer = np.mean(wer_scores) if wer_scores else 0.0
        logger.info(f"Transcription complete: {len(wer_scores)} tests, mean WER: {mean_wer:.3f}")
        return wer_scores, results
    
    def evaluate_phrase_matching(
        self,
        correct_phrase_cases: List[Dict],
        incorrect_phrase_cases: List[Dict],
        dataset_dir: Path
    ) -> Tuple[Dict[str, float], List[TestResult]]:
        """
        Evaluate phrase matching (correct vs incorrect phrase detection).
        
        Args:
            correct_phrase_cases: Cases where user says correct phrase
            incorrect_phrase_cases: Cases where user says wrong phrase
            dataset_dir: Dataset directory
            
        Returns:
            Tuple of (metrics_dict, test_results)
        """
        logger.info("Evaluating phrase matching...")
        
        results = []
        correct_detections = 0
        total_correct = 0
        incorrect_detections = 0
        total_incorrect = 0
        
        # Test correct phrases (should match)
        for i, test_case in enumerate(correct_phrase_cases, 1):
            test_id = f"phrase_correct_{i:04d}"
            audio_path = dataset_dir / test_case["audio_path"]
            expected_phrase = test_case["expected_phrase"]
            
            if not audio_path.exists():
                continue
            
            try:
                audio_data = self.load_audio_file(audio_path)
                verification_result = self.asr_adapter.verify_phrase(audio_data, expected_phrase)
                
                phrase_matches = verification_result.get("phrase_matches", False)
                similarity = verification_result.get("similarity", 0.0)
                
                total_correct += 1
                if phrase_matches:
                    correct_detections += 1
                
                result = TestResult(
                    test_id=test_id,
                    test_type="phrase_correct",
                    phrase_match_score=similarity,
                    label="should_match",
                    system_decision="matched" if phrase_matches else "rejected",
                    notes=f"Expected: '{expected_phrase}', Similarity: {similarity:.3f}",
                    timestamp=datetime.now().isoformat()
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"  Failed test {test_id}: {e}")
        
        # Test incorrect phrases (should NOT match)
        for i, test_case in enumerate(incorrect_phrase_cases, 1):
            test_id = f"phrase_incorrect_{i:04d}"
            audio_path = dataset_dir / test_case["audio_path"]
            expected_phrase = test_case["expected_phrase"]
            actual_phrase = test_case.get("actual_phrase", "different phrase")
            
            if not audio_path.exists():
                continue
            
            try:
                audio_data = self.load_audio_file(audio_path)
                verification_result = self.asr_adapter.verify_phrase(audio_data, expected_phrase)
                
                phrase_matches = verification_result.get("phrase_matches", False)
                similarity = verification_result.get("similarity", 0.0)
                
                total_incorrect += 1
                if not phrase_matches:  # Correctly rejected
                    incorrect_detections += 1
                
                result = TestResult(
                    test_id=test_id,
                    test_type="phrase_incorrect",
                    phrase_match_score=similarity,
                    label="should_not_match",
                    system_decision="matched" if phrase_matches else "rejected",
                    notes=f"Expected: '{expected_phrase}', Actual: '{actual_phrase}', Similarity: {similarity:.3f}",
                    timestamp=datetime.now().isoformat()
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"  Failed test {test_id}: {e}")
        
        # Calculate metrics
        correct_accuracy = correct_detections / total_correct if total_correct > 0 else 0.0
        incorrect_accuracy = incorrect_detections / total_incorrect if total_incorrect > 0 else 0.0
        overall_accuracy = (correct_detections + incorrect_detections) / (total_correct + total_incorrect) if (total_correct + total_incorrect) > 0 else 0.0
        
        metrics = {
            "correct_phrase_accuracy": correct_accuracy,
            "incorrect_phrase_rejection_rate": incorrect_accuracy,
            "overall_phrase_matching_accuracy": overall_accuracy,
            "total_correct_tests": total_correct,
            "total_incorrect_tests": total_incorrect
        }
        
        logger.info(f"Phrase matching complete:")
        logger.info(f"  Correct phrase detection: {correct_accuracy:.1%} ({correct_detections}/{total_correct})")
        logger.info(f"  Incorrect phrase rejection: {incorrect_accuracy:.1%} ({incorrect_detections}/{total_incorrect})")
        logger.info(f"  Overall accuracy: {overall_accuracy:.1%}")
        
        return metrics, results
    
    def run_evaluation(
        self,
        transcription_cases: List[Dict],
        correct_phrase_cases: List[Dict],
        incorrect_phrase_cases: List[Dict],
        dataset_dir: Path,
        experiment_name: str = "asr_evaluation"
    ) -> Path:
        """
        Run complete ASR evaluation.
        
        Args:
            transcription_cases: Cases for WER evaluation
            correct_phrase_cases: Cases with correct phrases
            incorrect_phrase_cases: Cases with incorrect phrases
            dataset_dir: Dataset directory
            experiment_name: Experiment name
            
        Returns:
            Path to results file
        """
        all_results = []
        metrics = {}
        
        # Step 1: Transcription accuracy (WER)
        if transcription_cases:
            wer_scores, wer_results = self.evaluate_transcription_accuracy(
                transcription_cases, dataset_dir
            )
            all_results.extend(wer_results)
            metrics["mean_wer"] = float(np.mean(wer_scores)) if wer_scores else None
            metrics["wer_std"] = float(np.std(wer_scores)) if wer_scores else None
        
        # Step 2: Phrase matching accuracy
        if correct_phrase_cases or incorrect_phrase_cases:
            phrase_metrics, phrase_results = self.evaluate_phrase_matching(
                correct_phrase_cases, incorrect_phrase_cases, dataset_dir
            )
            all_results.extend(phrase_results)
            metrics.update(phrase_metrics)
        
        # Display summary
        logger.info(f"\n{'='*60}")
        logger.info(f"ASR EVALUATION RESULTS: {experiment_name}")
        logger.info(f"{'='*60}")
        if "mean_wer" in metrics and metrics["mean_wer"] is not None:
            logger.info(f"Mean WER: {metrics['mean_wer']:.3f}")
        if "overall_phrase_matching_accuracy" in metrics:
            logger.info(f"Phrase Matching Accuracy: {metrics['overall_phrase_matching_accuracy']:.1%}")
        logger.info(f"{'='*60}\n")
        
        # Save results
        experiment_id = generate_experiment_id("asr", experiment_name)
        metadata = ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_type="asr",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            dataset=experiment_name,
            description=f"ASR evaluation: {len(all_results)} total tests"
        )
        
        filepath = self.results_manager.save_experiment(metadata, all_results, metrics)
        logger.info(f"Results saved to: {filepath}")
        return filepath


def load_example_config():
    """Example configuration."""
    return {
        "transcription": [
            {"audio_path": "phrases/phrase_001.wav", "reference_text": "the quick brown fox"},
        ],
        "correct_phrases": [
            {"audio_path": "correct/audio_001.wav", "expected_phrase": "hello world"},
        ],
        "incorrect_phrases": [
            {"audio_path": "incorrect/audio_001.wav", "expected_phrase": "hello world", "actual_phrase": "goodbye world"},
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate ASR module")
    parser.add_argument("--dataset", type=str, default="dataset",
                        help="Dataset directory path")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to configuration JSON file")
    parser.add_argument("--name", type=str, default="asr_eval",
                        help="Experiment name")
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        print("WARNING: Using example configuration")
        config = load_example_config()
    
    evaluator = ASREvaluator()
    
    try:
        result_path = evaluator.run_evaluation(
            transcription_cases=config.get("transcription", []),
            correct_phrase_cases=config.get("correct_phrases", []),
            incorrect_phrase_cases=config.get("incorrect_phrases", []),
            dataset_dir=Path(args.dataset),
            experiment_name=args.name
        )
        print(f"\n✓ Evaluation complete! Results: {result_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
