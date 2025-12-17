"""
Biometric Metrics Calculator

This module implements standard biometric metrics used in authentication systems:
- FAR (False Acceptance Rate): Rate of impostor acceptance
- FRR (False Rejection Rate): Rate of genuine rejection  
- EER (Equal Error Rate): Point where FAR = FRR
- ROC curves and threshold optimization

Based on ISO/IEC 19795 standards for biometric performance testing.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BiometricScores:
    """Container for biometric test scores."""
    genuine_scores: np.ndarray  # Scores from genuine attempts
    impostor_scores: np.ndarray  # Scores from impostor attempts
    
    def __post_init__(self):
        """Validate scores after initialization."""
        self.genuine_scores = np.asarray(self.genuine_scores, dtype=np.float64)
        self.impostor_scores = np.asarray(self.impostor_scores, dtype=np.float64)
        
        if len(self.genuine_scores) == 0:
            raise ValueError("genuine_scores cannot be empty")
        if len(self.impostor_scores) == 0:
            raise ValueError("impostor_scores cannot be empty")
        
        # Validate score ranges [0, 1]
        if not (0 <= self.genuine_scores.min() and self.genuine_scores.max() <= 1):
            logger.warning("Genuine scores outside [0, 1] range")
        if not (0 <= self.impostor_scores.min() and self.impostor_scores.max() <= 1):
            logger.warning("Impostor scores outside [0, 1] range")


@dataclass
class MetricsResult:
    """Results from biometric metrics calculation."""
    threshold: float
    far: float  # False Acceptance Rate
    frr: float  # False Rejection Rate
    eer: Optional[float] = None  # Equal Error Rate (if found)
    eer_threshold: Optional[float] = None  # Threshold at EER
    
    def __str__(self) -> str:
        if self.eer is not None:
            return (f"Threshold: {self.threshold:.3f}, FAR: {self.far:.3%}, "
                   f"FRR: {self.frr:.3%}, EER: {self.eer:.3%} @ {self.eer_threshold:.3f}")
        return f"Threshold: {self.threshold:.3f}, FAR: {self.far:.3%}, FRR: {self.frr:.3%}"


class BiometricMetrics:
    """
    Calculator for biometric authentication metrics.
    
    Implements standard metrics for evaluating biometric systems according to
    ISO/IEC 19795 and academic best practices.
    """
    
    def __init__(self, scores: BiometricScores):
        """
        Initialize metrics calculator.
        
        Args:
            scores: BiometricScores object with genuine and impostor scores
        """
        self.scores = scores
        logger.info(
            f"Initialized BiometricMetrics with {len(scores.genuine_scores)} "
            f"genuine and {len(scores.impostor_scores)} impostor scores"
        )
    
    def calculate_far_frr(self, threshold: float) -> Tuple[float, float]:
        """
        Calculate FAR and FRR for a given threshold.
        
        FAR = Number of impostors accepted / Total impostors
        FRR = Number of genuines rejected / Total genuines
        
        Decision rule: Accept if score >= threshold
        
        Args:
            threshold: Decision threshold in [0, 1]
            
        Returns:
            Tuple of (FAR, FRR)
        """
        # FAR: impostor scores that meet threshold (false accepts)
        false_accepts = np.sum(self.scores.impostor_scores >= threshold)
        far = false_accepts / len(self.scores.impostor_scores)
        
        # FRR: genuine scores below threshold (false rejects)
        false_rejects = np.sum(self.scores.genuine_scores < threshold)
        frr = false_rejects / len(self.scores.genuine_scores)
        
        return far, frr
    
    def sweep_thresholds(
        self, 
        num_thresholds: int = 1000,
        threshold_range: Optional[Tuple[float, float]] = None
    ) -> List[MetricsResult]:
        """
        Calculate FAR and FRR across multiple thresholds.
        
        Args:
            num_thresholds: Number of thresholds to test
            threshold_range: Optional (min, max) range. Defaults to score range.
            
        Returns:
            List of MetricsResult objects
        """
        if threshold_range is None:
            # Use range of all scores
            all_scores = np.concatenate([
                self.scores.genuine_scores,
                self.scores.impostor_scores
            ])
            min_threshold = float(all_scores.min())
            max_threshold = float(all_scores.max())
        else:
            min_threshold, max_threshold = threshold_range
        
        thresholds = np.linspace(min_threshold, max_threshold, num_thresholds)
        results = []
        
        for threshold in thresholds:
            far, frr = self.calculate_far_frr(threshold)
            results.append(MetricsResult(
                threshold=float(threshold),
                far=float(far),
                frr=float(frr)
            ))
        
        logger.debug(f"Swept {num_thresholds} thresholds from {min_threshold:.3f} to {max_threshold:.3f}")
        return results
    
    def find_eer(self, num_thresholds: int = 1000) -> MetricsResult:
        """
        Find Equal Error Rate (EER) - point where FAR = FRR.
        
        Uses linear interpolation if exact crossover not found.
        
        Args:
            num_thresholds: Number of thresholds to test
            
        Returns:
            MetricsResult with EER information
        """
        results = self.sweep_thresholds(num_thresholds)
        
        # Find point where FAR and FRR are closest
        min_diff = float('inf')
        eer_result = None
        
        for i, result in enumerate(results):
            diff = abs(result.far - result.frr)
            if diff < min_diff:
                min_diff = diff
                eer_result = result
        
        # Try interpolation for better accuracy
        if eer_result and len(results) > 1:
            eer_result = self._interpolate_eer(results)
        
        if eer_result:
            # Add EER fields
            eer_result.eer = (eer_result.far + eer_result.frr) / 2
            eer_result.eer_threshold = eer_result.threshold
            logger.info(f"Found EER: {eer_result.eer:.3%} at threshold {eer_result.eer_threshold:.3f}")
        else:
            raise ValueError("Could not find EER")
        
        return eer_result
    
    def _interpolate_eer(self, results: List[MetricsResult]) -> MetricsResult:
        """
        Interpolate EER using linear interpolation.
        
        Finds crossover point where FAR and FRR curves intersect.
        """
        fars = np.array([r.far for r in results])
        frrs = np.array([r.frr for r in results])
        thresholds = np.array([r.threshold for r in results])
        
        # Find crossover: where FAR - FRR changes sign
        diff = fars - frrs
        
        # Look for sign change
        for i in range(len(diff) - 1):
            if diff[i] * diff[i + 1] < 0:  # Sign change
                # Linear interpolation
                t1, t2 = thresholds[i], thresholds[i + 1]
                f1, f2 = fars[i], fars[i + 1]
                r1, r2 = frrs[i], frrs[i + 1]
                
                # Interpolate threshold where FAR = FRR
                # far(t) = f1 + (f2-f1)/(t2-t1) * (t-t1)
                # frr(t) = r1 + (r2-r1)/(t2-t1) * (t-t1)
                # Solve for t where far(t) = frr(t)
                
                if t2 != t1:
                    alpha = (r1 - f1) / ((f2 - f1) - (r2 - r1))
                    t_eer = t1 + alpha * (t2 - t1)
                    far_eer = f1 + alpha * (f2 - f1)
                    frr_eer = r1 + alpha * (r2 - r1)
                    
                    return MetricsResult(
                        threshold=float(t_eer),
                        far=float(far_eer),
                        frr=float(frr_eer)
                    )
        
        # If no crossover found, return closest point
        min_idx = np.argmin(np.abs(diff))
        return results[min_idx]
    
    def get_roc_curve(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate ROC (Receiver Operating Characteristic) curve data.
        
        ROC curve plots FAR (x-axis) vs. (1 - FRR) (y-axis).
        A perfect system would have a curve along the left and top edges.
        
        Args:
            num_points: Number of points in the curve
            
        Returns:
            Tuple of (far_values, tpr_values) where TPR = 1 - FRR
        """
        results = self.sweep_thresholds(num_points)
        
        far_values = np.array([r.far for r in results])
        frr_values = np.array([r.frr for r in results])
        tpr_values = 1 - frr_values  # True Positive Rate
        
        # Sort by FAR for proper ROC curve
        sorted_indices = np.argsort(far_values)
        
        return far_values[sorted_indices], tpr_values[sorted_indices]
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical summary of scores.
        
        Returns:
            Dictionary with statistical measures
        """
        return {
            "genuine_mean": float(np.mean(self.scores.genuine_scores)),
            "genuine_std": float(np.std(self.scores.genuine_scores)),
            "genuine_median": float(np.median(self.scores.genuine_scores)),
            "genuine_min": float(np.min(self.scores.genuine_scores)),
            "genuine_max": float(np.max(self.scores.genuine_scores)),
            "impostor_mean": float(np.mean(self.scores.impostor_scores)),
            "impostor_std": float(np.std(self.scores.impostor_scores)),
            "impostor_median": float(np.median(self.scores.impostor_scores)),
            "impostor_min": float(np.min(self.scores.impostor_scores)),
            "impostor_max": float(np.max(self.scores.impostor_scores)),
            "genuine_count": len(self.scores.genuine_scores),
            "impostor_count": len(self.scores.impostor_scores),
        }


class ThresholdOptimizer:
    """
    Helper class for finding optimal operating thresholds.
    """
    
    @staticmethod
    def find_threshold_at_far(
        metrics: BiometricMetrics,
        target_far: float,
        num_thresholds: int = 1000
    ) -> MetricsResult:
        """
        Find threshold that achieves a target FAR.
        
        Useful for security-critical applications where FAR must be minimized.
        
        Args:
            metrics: BiometricMetrics object
            target_far: Desired FAR (e.g., 0.01 for 1%)
            num_thresholds: Search resolution
            
        Returns:
            MetricsResult at closest threshold to target FAR
        """
        results = metrics.sweep_thresholds(num_thresholds)
        
        # Find threshold with FAR closest to target
        min_diff = float('inf')
        best_result = None
        
        for result in results:
            diff = abs(result.far - target_far)
            if diff < min_diff:
                min_diff = diff
                best_result = result
        
        logger.info(
            f"Found threshold {best_result.threshold:.3f} for target FAR {target_far:.3%} "
            f"(actual FAR: {best_result.far:.3%}, FRR: {best_result.frr:.3%})"
        )
        return best_result
    
    @staticmethod
    def find_threshold_at_frr(
        metrics: BiometricMetrics,
        target_frr: float,
        num_thresholds: int = 1000
    ) -> MetricsResult:
        """
        Find threshold that achieves a target FRR.
        
        Useful for user-friendly applications where false rejection should be minimized.
        
        Args:
            metrics: BiometricMetrics object
            target_frr: Desired FRR (e.g., 0.05 for 5%)
            num_thresholds: Search resolution
            
        Returns:
            MetricsResult at closest threshold to target FRR
        """
        results = metrics.sweep_thresholds(num_thresholds)
        
        # Find threshold with FRR closest to target
        min_diff = float('inf')
        best_result = None
        
        for result in results:
            diff = abs(result.frr - target_frr)
            if diff < min_diff:
                min_diff = diff
                best_result = result
        
        logger.info(
            f"Found threshold {best_result.threshold:.3f} for target FRR {target_frr:.3%} "
            f"(actual FRR: {best_result.frr:.3%}, FAR: {best_result.far:.3%})"
        )
        return best_result


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER) for ASR evaluation.
    
    WER = (Substitutions + Deletions + Insertions) / Total words in reference
    
    Args:
        reference: Ground truth text
        hypothesis: ASR transcription
        
    Returns:
        WER as a float (0.0 = perfect, higher is worse)
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    
    # Use dynamic programming to find edit distance
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
        return 1.0 if len(hyp_words) > 0 else 0.0
    
    wer = float(d[len(ref_words)][len(hyp_words)]) / len(ref_words)
    return wer


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Simulate genuine and impostor scores
    np.random.seed(42)
    genuine = np.random.beta(8, 2, 100)  # High scores for genuines
    impostor = np.random.beta(2, 5, 150)  # Low scores for impostors
    
    scores = BiometricScores(genuine_scores=genuine, impostor_scores=impostor)
    metrics = BiometricMetrics(scores)
    
    # Find EER
    eer_result = metrics.find_eer()
    print(f"\n{eer_result}")
    
    # Get statistics
    stats = metrics.get_statistics()
    print(f"\nGenuine scores: μ={stats['genuine_mean']:.3f}, σ={stats['genuine_std']:.3f}")
    print(f"Impostor scores: μ={stats['impostor_mean']:.3f}, σ={stats['impostor_std']:.3f}")
    
    # Find threshold for specific FAR
    optimizer = ThresholdOptimizer()
    result_far = optimizer.find_threshold_at_far(metrics, target_far=0.01)
    print(f"\nAt FAR=1%: {result_far}")
