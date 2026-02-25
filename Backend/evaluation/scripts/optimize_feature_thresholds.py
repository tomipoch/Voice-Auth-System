"""
Threshold Optimization for Feature Engineering

This script tests different threshold configurations to find
the optimal balance between BPCER and APCER(Cloning).

Tests:
1. Different indicator requirements (2+, 3+, 4+)
2. Different feature thresholds
3. Weighted combinations
"""

import sys
import os
from pathlib import Path
import numpy as np
import librosa
import logging
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.biometrics.audio_features import AudioFeatureExtractor
from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logger = logging.getLogger(__name__)


class ThresholdOptimizer:
    """
    Optimizes feature thresholds for best BPCER/APCER balance.
    """
    
    def __init__(self):
        self.spoof_detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
        self.feature_extractor = AudioFeatureExtractor(sample_rate=16000)
        
    def load_audio(self, audio_path: Path) -> np.ndarray:
        """Load and preprocess audio file."""
        audio, sr = librosa.load(audio_path, sr=16000)
        return audio
    
    def extract_all_data(
        self,
        genuine_files: List[Path],
        cloning_files: List[Path]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract ensemble scores and features for all files.
        
        Returns:
            Tuple of (genuine_data, cloning_data)
        """
        logger.info("Extracting data from all files...")
        
        genuine_data = []
        cloning_data = []
        
        # Process genuine files
        for i, audio_path in enumerate(genuine_files, 1):
            try:
                # Get ensemble score
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                ensemble_score = self.spoof_detector.detect_spoof(audio_data)
                spoof_score = 1.0 - ensemble_score  # Invert
                
                # Load audio for feature extraction
                audio = self.load_audio(audio_path)
                
                # Extract features
                features = self.feature_extractor.extract_all_features(audio)
                
                genuine_data.append({
                    'file': audio_path.name,
                    'ensemble_score': spoof_score,
                    'features': features
                })
                
                if i % 10 == 0:
                    logger.info(f"  Processed {i}/{len(genuine_files)} genuine")
                    
            except Exception as e:
                logger.error(f"Failed to process {audio_path.name}: {e}")
        
        # Process cloning files
        for i, audio_path in enumerate(cloning_files, 1):
            try:
                # Get ensemble score
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                ensemble_score = self.spoof_detector.detect_spoof(audio_data)
                spoof_score = 1.0 - ensemble_score  # Invert
                
                # Load audio for feature extraction
                audio = self.load_audio(audio_path)
                
                # Extract features
                features = self.feature_extractor.extract_all_features(audio)
                
                cloning_data.append({
                    'file': audio_path.name,
                    'ensemble_score': spoof_score,
                    'features': features
                })
                
                if i % 10 == 0:
                    logger.info(f"  Processed {i}/{len(cloning_files)} cloning")
                    
            except Exception as e:
                logger.error(f"Failed to process {audio_path.name}: {e}")
        
        return genuine_data, cloning_data
    
    def test_configuration(
        self,
        genuine_data: List[Dict],
        cloning_data: List[Dict],
        config: Dict
    ) -> Dict:
        """
        Test a specific threshold configuration.
        
        Args:
            genuine_data: List of genuine samples with scores and features
            cloning_data: List of cloning samples with scores and features
            config: Configuration dict with thresholds
            
        Returns:
            Dict with BPCER, APCER, and ACER
        """
        ensemble_threshold = config['ensemble_threshold']
        snr_threshold = config['snr_threshold']
        artifacts_threshold = config['artifacts_threshold']
        noise_threshold = config['noise_threshold']
        pitch_threshold = config['pitch_threshold']
        min_indicators = config['min_indicators']
        
        # Evaluate genuine samples
        genuine_rejected = 0
        for sample in genuine_data:
            if self.is_spoof(sample, ensemble_threshold, snr_threshold, 
                           artifacts_threshold, noise_threshold, 
                           pitch_threshold, min_indicators):
                genuine_rejected += 1
        
        # Evaluate cloning samples
        cloning_accepted = 0
        for sample in cloning_data:
            if not self.is_spoof(sample, ensemble_threshold, snr_threshold,
                               artifacts_threshold, noise_threshold,
                               pitch_threshold, min_indicators):
                cloning_accepted += 1
        
        bpcer = (genuine_rejected / len(genuine_data) * 100) if genuine_data else 0
        apcer = (cloning_accepted / len(cloning_data) * 100) if cloning_data else 0
        acer = (bpcer + apcer) / 2
        
        return {
            'bpcer': bpcer,
            'apcer': apcer,
            'acer': acer
        }
    
    def is_spoof(
        self,
        sample: Dict,
        ensemble_threshold: float,
        snr_threshold: float,
        artifacts_threshold: float,
        noise_threshold: float,
        pitch_threshold: float,
        min_indicators: int
    ) -> bool:
        """Determine if sample is spoof based on configuration."""
        # If ensemble is confident, trust it
        if sample['ensemble_score'] >= ensemble_threshold:
            return True
        
        # Count indicators
        indicators = 0
        features = sample['features']
        
        if features['snr'] > snr_threshold:
            indicators += 1
        if features['spectral_artifacts'] > artifacts_threshold:
            indicators += 1
        if features['background_noise'] < noise_threshold:
            indicators += 1
        if features['pitch_stability'] < pitch_threshold:
            indicators += 1
        
        return indicators >= min_indicators
    
    def optimize_thresholds(
        self,
        genuine_data: List[Dict],
        cloning_data: List[Dict]
    ) -> List[Dict]:
        """
        Test multiple configurations and return results.
        
        Returns:
            List of configurations with their metrics
        """
        logger.info("Testing threshold configurations...")
        
        configurations = []
        
        # Configuration 1: Current (aggressive)
        configurations.append({
            'name': 'Current (Aggressive)',
            'ensemble_threshold': 0.5,
            'snr_threshold': 40,
            'artifacts_threshold': 0.3,
            'noise_threshold': 0.1,
            'pitch_threshold': 0.2,
            'min_indicators': 2
        })
        
        # Configuration 2: More conservative (higher thresholds)
        configurations.append({
            'name': 'Conservative',
            'ensemble_threshold': 0.5,
            'snr_threshold': 45,
            'artifacts_threshold': 0.4,
            'noise_threshold': 0.05,
            'pitch_threshold': 0.15,
            'min_indicators': 2
        })
        
        # Configuration 3: Very conservative (even higher)
        configurations.append({
            'name': 'Very Conservative',
            'ensemble_threshold': 0.5,
            'snr_threshold': 50,
            'artifacts_threshold': 0.5,
            'noise_threshold': 0.03,
            'pitch_threshold': 0.1,
            'min_indicators': 2
        })
        
        # Configuration 4: Require 3+ indicators
        configurations.append({
            'name': '3+ Indicators',
            'ensemble_threshold': 0.5,
            'snr_threshold': 40,
            'artifacts_threshold': 0.3,
            'noise_threshold': 0.1,
            'pitch_threshold': 0.2,
            'min_indicators': 3
        })
        
        # Configuration 5: Require 4 indicators (all)
        configurations.append({
            'name': '4 Indicators (All)',
            'ensemble_threshold': 0.5,
            'snr_threshold': 40,
            'artifacts_threshold': 0.3,
            'noise_threshold': 0.1,
            'pitch_threshold': 0.2,
            'min_indicators': 4
        })
        
        # Configuration 6: Only spectral artifacts (most effective)
        configurations.append({
            'name': 'Artifacts Only',
            'ensemble_threshold': 0.5,
            'snr_threshold': 100,  # Effectively disabled
            'artifacts_threshold': 0.4,
            'noise_threshold': 0.0,  # Effectively disabled
            'pitch_threshold': 0.0,  # Effectively disabled
            'min_indicators': 1
        })
        
        # Configuration 7: Balanced (moderate thresholds, 2+ indicators)
        configurations.append({
            'name': 'Balanced',
            'ensemble_threshold': 0.5,
            'snr_threshold': 42,
            'artifacts_threshold': 0.35,
            'noise_threshold': 0.08,
            'pitch_threshold': 0.18,
            'min_indicators': 2
        })
        
        # Configuration 8: Artifacts + SNR only
        configurations.append({
            'name': 'Artifacts + SNR',
            'ensemble_threshold': 0.5,
            'snr_threshold': 42,
            'artifacts_threshold': 0.35,
            'noise_threshold': 0.0,
            'pitch_threshold': 0.0,
            'min_indicators': 2
        })
        
        results = []
        
        for config in configurations:
            metrics = self.test_configuration(genuine_data, cloning_data, config)
            result = {**config, **metrics}
            results.append(result)
            logger.info(f"  {config['name']}: BPCER={metrics['bpcer']:.2f}%, APCER={metrics['apcer']:.2f}%, ACER={metrics['acer']:.2f}%")
        
        return results
    
    def generate_report(self, results: List[Dict], output_path: Path):
        """Generate optimization report."""
        with open(output_path, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("THRESHOLD OPTIMIZATION REPORT\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=" * 100 + "\n")
            f.write("CONFIGURATIONS TESTED\n")
            f.write("=" * 100 + "\n\n")
            
            # Table header
            f.write(f"{'Configuration':<25} {'BPCER':<10} {'APCER':<10} {'ACER':<10} {'Recommendation':<20}\n")
            f.write("-" * 100 + "\n")
            
            # Find best configurations
            best_acer = min(results, key=lambda x: x['acer'])
            best_apcer = min(results, key=lambda x: x['apcer'])
            best_balance = min(results, key=lambda x: abs(x['bpcer'] - x['apcer']))
            
            for result in results:
                name = result['name']
                bpcer = result['bpcer']
                apcer = result['apcer']
                acer = result['acer']
                
                recommendation = ""
                if result == best_acer:
                    recommendation = "⭐ Best ACER"
                elif result == best_apcer:
                    recommendation = "✅ Best APCER"
                elif result == best_balance:
                    recommendation = "⚖️ Most Balanced"
                
                f.write(f"{name:<25} {bpcer:<10.2f} {apcer:<10.2f} {acer:<10.2f} {recommendation:<20}\n")
            
            f.write("\n" + "=" * 100 + "\n")
            f.write("DETAILED CONFIGURATIONS\n")
            f.write("=" * 100 + "\n\n")
            
            for result in results:
                f.write(f"\n{result['name']}\n")
                f.write("-" * 50 + "\n")
                f.write(f"  Ensemble threshold:    {result['ensemble_threshold']}\n")
                f.write(f"  SNR threshold:         {result['snr_threshold']}\n")
                f.write(f"  Artifacts threshold:   {result['artifacts_threshold']}\n")
                f.write(f"  Noise threshold:       {result['noise_threshold']}\n")
                f.write(f"  Pitch threshold:       {result['pitch_threshold']}\n")
                f.write(f"  Min indicators:        {result['min_indicators']}\n")
                f.write(f"\n")
                f.write(f"  BPCER:  {result['bpcer']:.2f}%\n")
                f.write(f"  APCER:  {result['apcer']:.2f}%\n")
                f.write(f"  ACER:   {result['acer']:.2f}%\n")
            
            f.write("\n" + "=" * 100 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"1. For Best Overall Performance (Lowest ACER):\n")
            f.write(f"   Configuration: {best_acer['name']}\n")
            f.write(f"   BPCER: {best_acer['bpcer']:.2f}%, APCER: {best_acer['apcer']:.2f}%, ACER: {best_acer['acer']:.2f}%\n\n")
            
            f.write(f"2. For Best Cloning Detection (Lowest APCER):\n")
            f.write(f"   Configuration: {best_apcer['name']}\n")
            f.write(f"   BPCER: {best_apcer['bpcer']:.2f}%, APCER: {best_apcer['apcer']:.2f}%, ACER: {best_apcer['acer']:.2f}%\n\n")
            
            f.write(f"3. For Most Balanced (BPCER ≈ APCER):\n")
            f.write(f"   Configuration: {best_balance['name']}\n")
            f.write(f"   BPCER: {best_balance['bpcer']:.2f}%, APCER: {best_balance['apcer']:.2f}%, ACER: {best_balance['acer']:.2f}%\n\n")
        
        logger.info(f"Report saved to: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize feature thresholds")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset directory")
    parser.add_argument("--output", type=str, default="results/antispoofing", help="Output directory")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    dataset_dir = Path(args.dataset)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find audio files
    genuine_dir = dataset_dir / "recordings"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav")) if genuine_dir.exists() else []
    cloning_files = sorted(cloning_dir.rglob("*.wav")) if cloning_dir.exists() else []
    
    logger.info(f"Found {len(genuine_files)} genuine, {len(cloning_files)} cloning audios")
    
    if not genuine_files or not cloning_files:
        logger.error("Insufficient audio files found!")
        return
    
    # Run optimization
    optimizer = ThresholdOptimizer()
    
    # Extract all data once
    genuine_data, cloning_data = optimizer.extract_all_data(genuine_files, cloning_files)
    
    # Test configurations
    results = optimizer.optimize_thresholds(genuine_data, cloning_data)
    
    # Generate report
    report_path = output_dir / "THRESHOLD_OPTIMIZATION_REPORT.txt"
    optimizer.generate_report(results, report_path)
    
    logger.info("✓ Optimization complete!")


if __name__ == "__main__":
    main()
