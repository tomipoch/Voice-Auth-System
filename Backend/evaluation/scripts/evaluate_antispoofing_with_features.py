"""
Evaluate Anti-Spoofing with Feature Engineering

This script evaluates the improvement in anti-spoofing performance
when using extracted audio features in addition to the ensemble model.

Compares:
- Baseline: Ensemble model only
- Enhanced: Ensemble + audio features
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


class FeatureEnhancedEvaluator:
    """
    Evaluates anti-spoofing with and without feature engineering.
    """
    
    def __init__(self):
        self.spoof_detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
        self.feature_extractor = AudioFeatureExtractor(sample_rate=16000)
        
    def load_audio(self, audio_path: Path) -> np.ndarray:
        """Load and preprocess audio file."""
        audio, sr = librosa.load(audio_path, sr=16000)
        return audio
    
    def evaluate_baseline(
        self,
        genuine_files: List[Path],
        cloning_files: List[Path],
        threshold: float = 0.5
    ) -> Dict:
        """
        Evaluate baseline (ensemble only).
        
        Returns:
            Dict with BPCER, APCER, and detailed results
        """
        logger.info("Evaluating baseline (ensemble only)...")
        
        genuine_scores = []
        cloning_scores = []
        
        # Process genuine files
        for audio_path in genuine_files:
            try:
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                score = self.spoof_detector.detect_spoof(audio_data)
                # Invert score (model returns genuineness)
                spoof_score = 1.0 - score
                genuine_scores.append(spoof_score)
            except Exception as e:
                logger.error(f"Failed to process {audio_path.name}: {e}")
        
        # Process cloning files
        for audio_path in cloning_files:
            try:
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                score = self.spoof_detector.detect_spoof(audio_data)
                # Invert score
                spoof_score = 1.0 - score
                cloning_scores.append(spoof_score)
            except Exception as e:
                logger.error(f"Failed to process {audio_path.name}: {e}")
        
        genuine_scores = np.array(genuine_scores)
        cloning_scores = np.array(cloning_scores)
        
        # Calculate metrics
        bpcer = np.sum(genuine_scores >= threshold) / len(genuine_scores) * 100
        apcer = np.sum(cloning_scores < threshold) / len(cloning_scores) * 100
        acer = (bpcer + apcer) / 2
        
        return {
            'bpcer': bpcer,
            'apcer_cloning': apcer,
            'acer': acer,
            'genuine_scores': genuine_scores,
            'cloning_scores': cloning_scores
        }
    
    def evaluate_with_features(
        self,
        genuine_files: List[Path],
        cloning_files: List[Path],
        ensemble_threshold: float = 0.5
    ) -> Dict:
        """
        Evaluate with feature engineering.
        
        Uses ensemble score + extracted features for decision.
        
        Returns:
            Dict with BPCER, APCER, and detailed results
        """
        logger.info("Evaluating with feature engineering...")
        
        genuine_results = []
        cloning_results = []
        
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
                
                # Enhanced decision
                is_spoof = self.make_enhanced_decision(spoof_score, features, ensemble_threshold)
                
                genuine_results.append({
                    'file': audio_path.name,
                    'ensemble_score': spoof_score,
                    'features': features,
                    'is_spoof': is_spoof
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
                
                # Enhanced decision
                is_spoof = self.make_enhanced_decision(spoof_score, features, ensemble_threshold)
                
                cloning_results.append({
                    'file': audio_path.name,
                    'ensemble_score': spoof_score,
                    'features': features,
                    'is_spoof': is_spoof
                })
                
                if i % 10 == 0:
                    logger.info(f"  Processed {i}/{len(cloning_files)} cloning")
                    
            except Exception as e:
                logger.error(f"Failed to process {audio_path.name}: {e}")
        
        # Calculate metrics
        genuine_rejected = sum(1 for r in genuine_results if r['is_spoof'])
        cloning_accepted = sum(1 for r in cloning_results if not r['is_spoof'])
        
        bpcer = (genuine_rejected / len(genuine_results) * 100) if genuine_results else 0
        apcer = (cloning_accepted / len(cloning_results) * 100) if cloning_results else 0
        acer = (bpcer + apcer) / 2
        
        return {
            'bpcer': bpcer,
            'apcer_cloning': apcer,
            'acer': acer,
            'genuine_results': genuine_results,
            'cloning_results': cloning_results
        }
    
    def make_enhanced_decision(
        self,
        ensemble_score: float,
        features: Dict[str, float],
        ensemble_threshold: float
    ) -> bool:
        """
        Make enhanced spoof detection decision.
        
        Combines ensemble score with extracted features.
        
        Args:
            ensemble_score: Spoof probability from ensemble (0-1)
            features: Extracted audio features
            ensemble_threshold: Threshold for ensemble score
            
        Returns:
            True if classified as spoof, False if genuine
        """
        # If ensemble is confident, trust it
        if ensemble_score >= ensemble_threshold:
            return True  # Spoof
        
        # Check for cloning indicators in features
        cloning_indicators = 0
        
        # 1. SNR too high (overly clean)
        if features['snr'] > 40:
            cloning_indicators += 1
        
        # 2. Spectral artifacts
        if features['spectral_artifacts'] > 0.3:
            cloning_indicators += 1
        
        # 3. Insufficient background noise
        if features['background_noise'] < 0.1:
            cloning_indicators += 1
        
        # 4. Pitch too stable
        if features['pitch_stability'] < 0.2:
            cloning_indicators += 1
        
        # If 2 or more indicators, classify as spoof
        # This catches cloning that ensemble misses
        return cloning_indicators >= 2
    
    def generate_report(
        self,
        baseline_results: Dict,
        enhanced_results: Dict,
        output_path: Path
    ):
        """Generate comparison report."""
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("FEATURE ENGINEERING EVALUATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("BASELINE (Ensemble Only)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"BPCER:          {baseline_results['bpcer']:.2f}%\n")
            f.write(f"APCER(Cloning): {baseline_results['apcer_cloning']:.2f}%\n")
            f.write(f"ACER:           {baseline_results['acer']:.2f}%\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("ENHANCED (Ensemble + Features)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"BPCER:          {enhanced_results['bpcer']:.2f}%\n")
            f.write(f"APCER(Cloning): {enhanced_results['apcer_cloning']:.2f}%\n")
            f.write(f"ACER:           {enhanced_results['acer']:.2f}%\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("IMPROVEMENT\n")
            f.write("=" * 80 + "\n\n")
            
            bpcer_diff = enhanced_results['bpcer'] - baseline_results['bpcer']
            apcer_diff = enhanced_results['apcer_cloning'] - baseline_results['apcer_cloning']
            acer_diff = enhanced_results['acer'] - baseline_results['acer']
            
            f.write(f"BPCER:          {bpcer_diff:+.2f}% ")
            f.write("(worse)\n" if bpcer_diff > 0 else "(better)\n")
            
            f.write(f"APCER(Cloning): {apcer_diff:+.2f}% ")
            f.write("(worse)\n" if apcer_diff > 0 else "(better) ✓\n")
            
            f.write(f"ACER:           {acer_diff:+.2f}% ")
            f.write("(worse)\n" if acer_diff > 0 else "(better)\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("FEATURE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            # Analyze which features helped most
            if 'cloning_results' in enhanced_results:
                cloning_results = enhanced_results['cloning_results']
                
                # Count how many cloning samples were caught by each feature
                snr_catches = sum(1 for r in cloning_results if r['features']['snr'] > 40)
                artifact_catches = sum(1 for r in cloning_results if r['features']['spectral_artifacts'] > 0.3)
                noise_catches = sum(1 for r in cloning_results if r['features']['background_noise'] < 0.1)
                pitch_catches = sum(1 for r in cloning_results if r['features']['pitch_stability'] < 0.2)
                
                total = len(cloning_results)
                
                f.write(f"Cloning samples with indicators:\n")
                f.write(f"  SNR > 40:                {snr_catches}/{total} ({snr_catches/total*100:.1f}%)\n")
                f.write(f"  Spectral artifacts > 0.3: {artifact_catches}/{total} ({artifact_catches/total*100:.1f}%)\n")
                f.write(f"  Background noise < 0.1:   {noise_catches}/{total} ({noise_catches/total*100:.1f}%)\n")
                f.write(f"  Pitch stability < 0.2:    {pitch_catches}/{total} ({pitch_catches/total*100:.1f}%)\n")
        
        logger.info(f"Report saved to: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate anti-spoofing with feature engineering")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset directory")
    parser.add_argument("--output", type=str, default="results/antispoofing", help="Output directory")
    parser.add_argument("--threshold", type=float, default=0.5, help="Ensemble threshold")
    
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
    
    # Run evaluation
    evaluator = FeatureEnhancedEvaluator()
    
    # Baseline
    baseline_results = evaluator.evaluate_baseline(
        genuine_files, cloning_files, threshold=args.threshold
    )
    
    # Enhanced
    enhanced_results = evaluator.evaluate_with_features(
        genuine_files, cloning_files, ensemble_threshold=args.threshold
    )
    
    # Generate report
    report_path = output_dir / "FEATURE_ENGINEERING_EVALUATION.txt"
    evaluator.generate_report(baseline_results, enhanced_results, report_path)
    
    logger.info("✓ Evaluation complete!")
    logger.info(f"\nBaseline APCER(Cloning): {baseline_results['apcer_cloning']:.2f}%")
    logger.info(f"Enhanced APCER(Cloning): {enhanced_results['apcer_cloning']:.2f}%")
    logger.info(f"Improvement: {baseline_results['apcer_cloning'] - enhanced_results['apcer_cloning']:.2f}%")


if __name__ == "__main__":
    main()
