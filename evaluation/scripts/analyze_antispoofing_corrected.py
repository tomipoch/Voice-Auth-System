"""
Corrected Anti-Spoofing Analysis Script

This script properly calculates BPCER, APCER, and other anti-spoofing metrics
according to ISO/IEC 30107-3 standard.

Key corrections:
- BPCER = % of genuine samples REJECTED (score >= threshold)
- APCER = % of attack samples ACCEPTED (score < threshold)
- No score inversion - use spoof probability directly
- Proper threshold interpretation: higher score = more likely spoof

Usage:
    python analyze_antispoofing_corrected.py --dataset dataset/
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
except ImportError as e:
    print(f"Error importing biometric components: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)


class CorrectedAntiSpoofingAnalyzer:
    """
    Corrected analyzer for anti-spoofing metrics.
    
    Properly implements ISO/IEC 30107-3 metrics:
    - BPCER (Bona Fide Presentation Classification Error Rate)
    - APCER (Attack Presentation Classification Error Rate)
    - ACER (Average Classification Error Rate)
    """
    
    def __init__(self, model_name: str = "ensemble_antispoofing"):
        self.model_name = model_name
        self.spoof_detector = SpoofDetectorAdapter(model_name=model_name, use_gpu=True)
        
    def load_and_score_audios(
        self,
        audio_paths: List[Path],
        label: str
    ) -> Tuple[List[float], List[str]]:
        """
        Load audios and get spoof scores.
        
        Args:
            audio_paths: List of audio file paths
            label: Label for these audios (e.g., 'genuine', 'tts', 'cloning')
            
        Returns:
            Tuple of (scores, filenames)
        """
        scores = []
        filenames = []
        
        logger.info(f"Processing {len(audio_paths)} {label} audios...")
        
        for i, audio_path in enumerate(audio_paths, 1):
            if not audio_path.exists():
                logger.warning(f"  Audio not found: {audio_path}")
                continue
                
            try:
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                spoof_prob = self.spoof_detector.detect_spoof(audio_data)
                scores.append(spoof_prob)
                filenames.append(audio_path.name)
                
                if i % 20 == 0:
                    logger.info(f"  Processed {i}/{len(audio_paths)}")
                    
            except Exception as e:
                logger.error(f"  Failed to process {audio_path.name}: {e}")
        
        logger.info(f"  {label}: {len(scores)} audios, mean score: {np.mean(scores):.3f}")
        return scores, filenames
    
    def calculate_bpcer(self, genuine_scores: np.ndarray, threshold: float) -> float:
        """
        Calculate BPCER (Bona Fide Presentation Classification Error Rate).
        
        BPCER = % of genuine samples with score >= threshold (incorrectly rejected)
        
        Args:
            genuine_scores: Spoof probability scores for genuine audios
            threshold: Decision threshold
            
        Returns:
            BPCER as percentage (0-100)
        """
        rejected = np.sum(genuine_scores >= threshold)
        total = len(genuine_scores)
        return (rejected / total * 100) if total > 0 else 0.0
    
    def calculate_apcer(self, attack_scores: np.ndarray, threshold: float) -> float:
        """
        Calculate APCER (Attack Presentation Classification Error Rate).
        
        APCER = % of attack samples with score < threshold (incorrectly accepted)
        
        Args:
            attack_scores: Spoof probability scores for attack audios
            threshold: Decision threshold
            
        Returns:
            APCER as percentage (0-100)
        """
        accepted = np.sum(attack_scores < threshold)
        total = len(attack_scores)
        return (accepted / total * 100) if total > 0 else 0.0
    
    def calculate_acer(self, bpcer: float, apcer: float) -> float:
        """
        Calculate ACER (Average Classification Error Rate).
        
        ACER = (BPCER + APCER) / 2
        """
        return (bpcer + apcer) / 2
    
    def find_optimal_threshold(
        self,
        genuine_scores: np.ndarray,
        attack_scores: np.ndarray,
        thresholds: np.ndarray = None
    ) -> Dict:
        """
        Find optimal threshold that minimizes ACER.
        
        Args:
            genuine_scores: Scores for genuine audios
            attack_scores: Scores for attack audios
            thresholds: Array of thresholds to test (default: 0.0 to 1.0 in steps of 0.01)
            
        Returns:
            Dict with optimal threshold and metrics
        """
        if thresholds is None:
            thresholds = np.arange(0.0, 1.01, 0.01)
        
        best_acer = float('inf')
        best_threshold = 0.5
        best_metrics = {}
        
        all_metrics = []
        
        for threshold in thresholds:
            bpcer = self.calculate_bpcer(genuine_scores, threshold)
            apcer = self.calculate_apcer(attack_scores, threshold)
            acer = self.calculate_acer(bpcer, apcer)
            
            metrics = {
                'threshold': float(threshold),
                'bpcer': bpcer,
                'apcer': apcer,
                'acer': acer
            }
            all_metrics.append(metrics)
            
            if acer < best_acer:
                best_acer = acer
                best_threshold = threshold
                best_metrics = metrics
        
        return {
            'optimal': best_metrics,
            'all_metrics': all_metrics
        }
    
    def analyze_by_attack_type(
        self,
        genuine_scores: np.ndarray,
        tts_scores: np.ndarray,
        cloning_scores: np.ndarray,
        thresholds: List[float] = None
    ) -> Dict:
        """
        Analyze metrics by attack type.
        
        Args:
            genuine_scores: Scores for genuine audios
            tts_scores: Scores for TTS attacks
            cloning_scores: Scores for voice cloning attacks
            thresholds: List of thresholds to analyze
            
        Returns:
            Dict with metrics by attack type
        """
        if thresholds is None:
            thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        results = {}
        
        for threshold in thresholds:
            bpcer = self.calculate_bpcer(genuine_scores, threshold)
            apcer_tts = self.calculate_apcer(tts_scores, threshold)
            apcer_cloning = self.calculate_apcer(cloning_scores, threshold)
            
            # Combined APCER (all attacks)
            all_attacks = np.concatenate([tts_scores, cloning_scores])
            apcer_all = self.calculate_apcer(all_attacks, threshold)
            
            acer = self.calculate_acer(bpcer, apcer_all)
            
            results[threshold] = {
                'bpcer': bpcer,
                'apcer_tts': apcer_tts,
                'apcer_cloning': apcer_cloning,
                'apcer_all': apcer_all,
                'acer': acer
            }
        
        return results
    
    def generate_report(
        self,
        genuine_scores: np.ndarray,
        tts_scores: np.ndarray,
        cloning_scores: np.ndarray,
        output_dir: Path
    ) -> Path:
        """
        Generate comprehensive corrected report.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "ANTISPOOFING_CORRECTED_REPORT.txt"
        
        # Calculate statistics
        genuine_stats = {
            'mean': np.mean(genuine_scores),
            'std': np.std(genuine_scores),
            'min': np.min(genuine_scores),
            'max': np.max(genuine_scores)
        }
        
        tts_stats = {
            'mean': np.mean(tts_scores),
            'std': np.std(tts_scores),
            'min': np.min(tts_scores),
            'max': np.max(tts_scores)
        }
        
        cloning_stats = {
            'mean': np.mean(cloning_scores),
            'std': np.std(cloning_scores),
            'min': np.min(cloning_scores),
            'max': np.max(cloning_scores)
        }
        
        # Find optimal threshold
        all_attacks = np.concatenate([tts_scores, cloning_scores])
        optimal_result = self.find_optimal_threshold(genuine_scores, all_attacks)
        
        # Analyze by attack type
        threshold_analysis = self.analyze_by_attack_type(
            genuine_scores, tts_scores, cloning_scores
        )
        
        # Generate report
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("CORRECTED ANTI-SPOOFING EVALUATION REPORT\n")
            f.write("Metrics according to ISO/IEC 30107-3\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {self.model_name}\n\n")
            
            f.write("DATASET\n")
            f.write("-" * 80 + "\n")
            f.write(f"Genuine audios: {len(genuine_scores)}\n")
            f.write(f"TTS attacks: {len(tts_scores)}\n")
            f.write(f"Voice Cloning attacks: {len(cloning_scores)}\n")
            f.write(f"Total attacks: {len(all_attacks)}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("SCORE DISTRIBUTIONS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("Genuine (Bonafide):\n")
            f.write(f"  Mean:   {genuine_stats['mean']:.4f}\n")
            f.write(f"  Std:    {genuine_stats['std']:.4f}\n")
            f.write(f"  Range:  [{genuine_stats['min']:.4f} - {genuine_stats['max']:.4f}]\n\n")
            
            f.write("TTS Attacks:\n")
            f.write(f"  Mean:   {tts_stats['mean']:.4f}\n")
            f.write(f"  Std:    {tts_stats['std']:.4f}\n")
            f.write(f"  Range:  [{tts_stats['min']:.4f} - {tts_stats['max']:.4f}]\n\n")
            
            f.write("Voice Cloning Attacks:\n")
            f.write(f"  Mean:   {cloning_stats['mean']:.4f}\n")
            f.write(f"  Std:    {cloning_stats['std']:.4f}\n")
            f.write(f"  Range:  [{cloning_stats['min']:.4f} - {cloning_stats['max']:.4f}]\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("OPTIMAL THRESHOLD\n")
            f.write("=" * 80 + "\n\n")
            
            opt = optimal_result['optimal']
            f.write(f"Threshold: {opt['threshold']:.3f}\n")
            f.write(f"BPCER:     {opt['bpcer']:.2f}% (genuine rejected)\n")
            f.write(f"APCER:     {opt['apcer']:.2f}% (attacks accepted)\n")
            f.write(f"ACER:      {opt['acer']:.2f}%\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("METRICS BY THRESHOLD\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"{'Threshold':<12} {'BPCER':<10} {'APCER(TTS)':<13} {'APCER(Clone)':<15} {'APCER(All)':<12} {'ACER':<10}\n")
            f.write("-" * 80 + "\n")
            
            for threshold in sorted(threshold_analysis.keys()):
                m = threshold_analysis[threshold]
                f.write(f"{threshold:<12.2f} {m['bpcer']:<10.2f} {m['apcer_tts']:<13.2f} "
                       f"{m['apcer_cloning']:<15.2f} {m['apcer_all']:<12.2f} {m['acer']:<10.2f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("INTERPRETATION\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("BPCER (Bona Fide Presentation Classification Error Rate):\n")
            f.write("  - Percentage of GENUINE audios REJECTED (score >= threshold)\n")
            f.write("  - Lower is better (less genuine users rejected)\n\n")
            
            f.write("APCER (Attack Presentation Classification Error Rate):\n")
            f.write("  - Percentage of ATTACK audios ACCEPTED (score < threshold)\n")
            f.write("  - Lower is better (fewer attacks get through)\n\n")
            
            f.write("ACER (Average Classification Error Rate):\n")
            f.write("  - Average of BPCER and APCER\n")
            f.write("  - Optimal threshold minimizes ACER\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("KEY FINDINGS\n")
            f.write("=" * 80 + "\n\n")
            
            # Separation analysis
            separation_tts = tts_stats['mean'] - genuine_stats['mean']
            separation_cloning = cloning_stats['mean'] - genuine_stats['mean']
            
            f.write(f"1. TTS Detection:\n")
            f.write(f"   - Score separation: {separation_tts:.3f}\n")
            if separation_tts > 0.2:
                f.write(f"   - ✓ Good separation (TTS scores higher than genuine)\n")
            else:
                f.write(f"   - ✗ Poor separation (TTS scores similar to genuine)\n")
            
            # Find closest threshold in analysis
            opt_thresh = opt['threshold']
            if opt_thresh in threshold_analysis:
                f.write(f"   - APCER @ optimal: {threshold_analysis[opt_thresh]['apcer_tts']:.2f}%\n\n")
            else:
                # Use closest threshold
                closest_thresh = min(threshold_analysis.keys(), key=lambda x: abs(x - opt_thresh))
                f.write(f"   - APCER @ {closest_thresh:.2f}: {threshold_analysis[closest_thresh]['apcer_tts']:.2f}%\n\n")
            
            f.write(f"2. Voice Cloning Detection:\n")
            f.write(f"   - Score separation: {separation_cloning:.3f}\n")
            if separation_cloning > 0.1:
                f.write(f"   - ✓ Moderate separation\n")
            else:
                f.write(f"   - ✗ Poor separation (challenging to detect)\n")
            
            if opt_thresh in threshold_analysis:
                f.write(f"   - APCER @ optimal: {threshold_analysis[opt_thresh]['apcer_cloning']:.2f}%\n\n")
            else:
                f.write(f"   - APCER @ {closest_thresh:.2f}: {threshold_analysis[closest_thresh]['apcer_cloning']:.2f}%\n\n")
            
            f.write(f"3. Recommended Threshold:\n")
            f.write(f"   - For balanced performance: {opt['threshold']:.3f}\n")
            f.write(f"   - For high security (low APCER): 0.3-0.4\n")
            f.write(f"   - For high usability (low BPCER): 0.6-0.7\n\n")
        
        logger.info(f"Report saved to: {report_path}")
        return report_path
    
    def create_visualizations(
        self,
        genuine_scores: np.ndarray,
        tts_scores: np.ndarray,
        cloning_scores: np.ndarray,
        output_dir: Path
    ):
        """
        Create corrected visualizations.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Score distributions
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Anti-Spoofing Score Distributions (Corrected)', fontsize=16, fontweight='bold')
        
        # Histogram
        ax = axes[0, 0]
        ax.hist(genuine_scores, bins=30, alpha=0.6, label='Genuine', color='green', edgecolor='black')
        ax.hist(tts_scores, bins=30, alpha=0.6, label='TTS', color='red', edgecolor='black')
        ax.hist(cloning_scores, bins=30, alpha=0.6, label='Cloning', color='orange', edgecolor='black')
        ax.axvline(0.5, color='black', linestyle='--', linewidth=2, label='Threshold 0.5')
        ax.set_xlabel('Spoof Probability Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Score Distribution', fontsize=13, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Box plot
        ax = axes[0, 1]
        data = [genuine_scores, tts_scores, cloning_scores]
        bp = ax.boxplot(data, labels=['Genuine', 'TTS', 'Cloning'], patch_artist=True)
        colors = ['lightgreen', 'lightcoral', 'lightsalmon']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        ax.set_ylabel('Spoof Probability Score', fontsize=12)
        ax.set_title('Score Distribution by Type', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # BPCER/APCER curves
        ax = axes[1, 0]
        all_attacks = np.concatenate([tts_scores, cloning_scores])
        thresholds = np.arange(0.0, 1.01, 0.01)
        
        bpcers = [self.calculate_bpcer(genuine_scores, t) for t in thresholds]
        apcers_all = [self.calculate_apcer(all_attacks, t) for t in thresholds]
        apcers_tts = [self.calculate_apcer(tts_scores, t) for t in thresholds]
        apcers_cloning = [self.calculate_apcer(cloning_scores, t) for t in thresholds]
        
        ax.plot(thresholds, bpcers, 'g-', linewidth=2, label='BPCER (Genuine Rejected)')
        ax.plot(thresholds, apcers_all, 'r-', linewidth=2, label='APCER All (Attacks Accepted)')
        ax.plot(thresholds, apcers_tts, 'r--', linewidth=1.5, alpha=0.7, label='APCER TTS')
        ax.plot(thresholds, apcers_cloning, 'orange', linestyle='--', linewidth=1.5, alpha=0.7, label='APCER Cloning')
        ax.set_xlabel('Threshold', fontsize=12)
        ax.set_ylabel('Error Rate (%)', fontsize=12)
        ax.set_title('BPCER vs APCER', fontsize=13, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # ACER by threshold
        ax = axes[1, 1]
        acers = [(b + a) / 2 for b, a in zip(bpcers, apcers_all)]
        ax.plot(thresholds, acers, 'b-', linewidth=2, label='ACER')
        min_acer_idx = np.argmin(acers)
        ax.axvline(thresholds[min_acer_idx], color='red', linestyle='--', linewidth=2, 
                   label=f'Optimal: {thresholds[min_acer_idx]:.2f}')
        ax.set_xlabel('Threshold', fontsize=12)
        ax.set_ylabel('ACER (%)', fontsize=12)
        ax.set_title('ACER Optimization', fontsize=13, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_path = output_dir / 'antispoofing_corrected_analysis.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to: {plot_path}")
        return plot_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Corrected anti-spoofing analysis")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset directory")
    parser.add_argument("--output", type=str, default="results/antispoofing", help="Output directory")
    parser.add_argument("--model", type=str, default="ensemble_antispoofing", help="Model name")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    dataset_dir = Path(args.dataset)
    output_dir = Path(args.output)
    
    # Find audio files
    genuine_dir = dataset_dir / "recordings"
    tts_dir = dataset_dir / "attacks"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav")) if genuine_dir.exists() else []
    tts_files = sorted(tts_dir.rglob("*.wav")) if tts_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav")) if cloning_dir.exists() else []
    
    logger.info(f"Found {len(genuine_files)} genuine, {len(tts_files)} TTS, {len(cloning_files)} cloning audios")
    
    if not genuine_files or not (tts_files or cloning_files):
        logger.error("Insufficient audio files found!")
        return
    
    # Run analysis
    analyzer = CorrectedAntiSpoofingAnalyzer(model_name=args.model)
    
    genuine_scores, _ = analyzer.load_and_score_audios(genuine_files, "genuine")
    tts_scores, _ = analyzer.load_and_score_audios(tts_files, "TTS") if tts_files else ([], [])
    cloning_scores, _ = analyzer.load_and_score_audios(cloning_files, "cloning") if cloning_files else ([], [])
    
    genuine_scores = np.array(genuine_scores)
    tts_scores = np.array(tts_scores) if tts_scores else np.array([])
    cloning_scores = np.array(cloning_scores) if cloning_scores else np.array([])
    
    # Generate report and visualizations
    analyzer.generate_report(genuine_scores, tts_scores, cloning_scores, output_dir)
    analyzer.create_visualizations(genuine_scores, tts_scores, cloning_scores, Path("plots/antispoofing"))
    
    logger.info("✓ Corrected analysis complete!")


if __name__ == "__main__":
    main()
