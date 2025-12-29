"""
Comprehensive Feature Threshold Optimization

Test different feature threshold combinations for ensemble thresholds 0.40, 0.50, and 0.60
to find the optimal configuration that minimizes BPCER while maintaining good APCER.
"""

import sys
from pathlib import Path
import numpy as np
import librosa
import logging
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.biometrics.audio_features import AudioFeatureExtractor
from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logger = logging.getLogger(__name__)


def comprehensive_optimization():
    """Test all combinations of ensemble and feature thresholds."""
    
    spoof_detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
    feature_extractor = AudioFeatureExtractor(sample_rate=16000)
    
    dataset_dir = Path("evaluation/dataset")
    genuine_files = sorted((dataset_dir / "recordings").rglob("*.wav"))
    cloning_files = sorted((dataset_dir / "cloning").rglob("*.wav"))
    
    logger.info(f"Found {len(genuine_files)} genuine, {len(cloning_files)} cloning")
    logger.info("Extracting data...")
    
    # Extract all data once
    genuine_data = []
    cloning_data = []
    
    for i, path in enumerate(genuine_files, 1):
        try:
            with open(path, 'rb') as f:
                score = 1.0 - spoof_detector.detect_spoof(f.read())
            audio = librosa.load(path, sr=16000)[0]
            features = feature_extractor.extract_all_features(audio)
            genuine_data.append({'score': score, 'features': features})
            if i % 10 == 0:
                logger.info(f"  Genuine: {i}/{len(genuine_files)}")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    for i, path in enumerate(cloning_files, 1):
        try:
            with open(path, 'rb') as f:
                score = 1.0 - spoof_detector.detect_spoof(f.read())
            audio = librosa.load(path, sr=16000)[0]
            features = feature_extractor.extract_all_features(audio)
            cloning_data.append({'score': score, 'features': features})
            if i % 10 == 0:
                logger.info(f"  Cloning: {i}/{len(cloning_files)}")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    # Test configurations
    configs = []
    
    # For each ensemble threshold
    for ens_th in [0.40, 0.50, 0.60]:
        # Baseline (no features)
        configs.append({
            'name': f'Ensemble {ens_th:.2f} only',
            'ensemble_threshold': ens_th,
            'use_features': False
        })
        
        # Different feature threshold combinations
        feature_configs = [
            # Very permissive (let more through)
            {'snr': 50, 'artifacts': 0.6, 'noise': 0.03, 'min_ind': 2, 'label': 'Very Permissive'},
            {'snr': 50, 'artifacts': 0.6, 'noise': 0.03, 'min_ind': 3, 'label': 'Very Permissive (3+)'},
            
            # Permissive
            {'snr': 48, 'artifacts': 0.55, 'noise': 0.04, 'min_ind': 2, 'label': 'Permissive'},
            {'snr': 48, 'artifacts': 0.55, 'noise': 0.04, 'min_ind': 3, 'label': 'Permissive (3+)'},
            
            # Moderate
            {'snr': 45, 'artifacts': 0.5, 'noise': 0.05, 'min_ind': 2, 'label': 'Moderate'},
            {'snr': 45, 'artifacts': 0.5, 'noise': 0.05, 'min_ind': 3, 'label': 'Moderate (3+)'},
            
            # Balanced
            {'snr': 42, 'artifacts': 0.45, 'noise': 0.06, 'min_ind': 2, 'label': 'Balanced'},
            {'snr': 42, 'artifacts': 0.45, 'noise': 0.06, 'min_ind': 3, 'label': 'Balanced (3+)'},
        ]
        
        for fc in feature_configs:
            configs.append({
                'name': f'{ens_th:.2f} + {fc["label"]}',
                'ensemble_threshold': ens_th,
                'use_features': True,
                'snr_threshold': fc['snr'],
                'artifacts_threshold': fc['artifacts'],
                'noise_threshold': fc['noise'],
                'min_indicators': fc['min_ind']
            })
    
    # Evaluate all configurations
    results = []
    
    for config in configs:
        genuine_rejected = sum(1 for s in genuine_data if is_spoof(s, config))
        cloning_accepted = sum(1 for s in cloning_data if not is_spoof(s, config))
        
        bpcer = (genuine_rejected / len(genuine_data) * 100) if genuine_data else 0
        apcer = (cloning_accepted / len(cloning_data) * 100) if cloning_data else 0
        acer = (bpcer + apcer) / 2
        
        results.append({
            'config': config['name'],
            'bpcer': bpcer,
            'apcer': apcer,
            'acer': acer
        })
    
    # Print results
    print("\n" + "=" * 110)
    print("COMPREHENSIVE FEATURE THRESHOLD OPTIMIZATION")
    print("=" * 110)
    print()
    
    print(f"{'Configuration':<50} {'BPCER':<12} {'APCER':<12} {'ACER':<12} {'Note':<20}")
    print("-" * 110)
    
    # Find best configurations
    best_bpcer = min(results, key=lambda x: x['bpcer'])
    best_apcer = min(results, key=lambda x: x['apcer'])
    best_acer = min(results, key=lambda x: x['acer'])
    best_balance = min(results, key=lambda x: abs(x['bpcer'] - 40) + abs(x['apcer'] - 45))
    
    for r in results:
        note = ""
        if r == best_bpcer:
            note = "⭐ Best BPCER"
        elif r == best_apcer:
            note = "✅ Best APCER"
        elif r == best_acer:
            note = "🎯 Best ACER"
        elif r == best_balance:
            note = "⚖️ Best Balance"
        
        print(f"{r['config']:<50} {r['bpcer']:<12.2f} {r['apcer']:<12.2f} {r['acer']:<12.2f} {note:<20}")
    
    print()
    print("=" * 110)
    print("TOP 5 CONFIGURATIONS")
    print("=" * 110)
    print()
    
    # Sort by ACER
    top5 = sorted(results, key=lambda x: x['acer'])[:5]
    
    for i, r in enumerate(top5, 1):
        print(f"{i}. {r['config']}")
        print(f"   BPCER: {r['bpcer']:.2f}%, APCER: {r['apcer']:.2f}%, ACER: {r['acer']:.2f}%")
        print()


def is_spoof(sample: Dict, config: Dict) -> bool:
    if sample['score'] >= config['ensemble_threshold']:
        return True
    
    if not config.get('use_features', False):
        return False
    
    features = sample['features']
    indicators = 0
    
    if features['snr'] > config['snr_threshold']:
        indicators += 1
    if features['spectral_artifacts'] > config['artifacts_threshold']:
        indicators += 1
    if features['background_noise'] < config['noise_threshold']:
        indicators += 1
    
    return indicators >= config['min_indicators']


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    comprehensive_optimization()
