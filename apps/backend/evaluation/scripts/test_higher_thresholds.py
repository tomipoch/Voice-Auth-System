"""
Test Higher Ensemble Thresholds (0.60, 0.70)

Test if higher thresholds reduce BPCER.
"""

import sys
import os
from pathlib import Path
import numpy as np
import librosa
import logging
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.biometrics.audio_features import AudioFeatureExtractor
from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

logger = logging.getLogger(__name__)


def test_higher_thresholds():
    """Test ensemble thresholds 0.60 and 0.70."""
    
    spoof_detector = SpoofDetectorAdapter(model_name="ensemble_antispoofing", use_gpu=True)
    feature_extractor = AudioFeatureExtractor(sample_rate=16000)
    
    dataset_dir = Path("evaluation/dataset")
    genuine_dir = dataset_dir / "recordings"
    cloning_dir = dataset_dir / "cloning"
    
    genuine_files = sorted(genuine_dir.rglob("*.wav"))
    cloning_files = sorted(cloning_dir.rglob("*.wav"))
    
    logger.info(f"Found {len(genuine_files)} genuine, {len(cloning_files)} cloning audios")
    logger.info("Extracting ensemble scores and features...")
    
    genuine_data = []
    cloning_data = []
    
    # Process genuine
    for i, audio_path in enumerate(genuine_files, 1):
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            ensemble_score = spoof_detector.detect_spoof(audio_data)
            spoof_score = 1.0 - ensemble_score
            
            audio = librosa.load(audio_path, sr=16000)[0]
            features = feature_extractor.extract_all_features(audio)
            
            genuine_data.append({'score': spoof_score, 'features': features})
            
            if i % 10 == 0:
                logger.info(f"  Processed {i}/{len(genuine_files)} genuine")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    # Process cloning
    for i, audio_path in enumerate(cloning_files, 1):
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            ensemble_score = spoof_detector.detect_spoof(audio_data)
            spoof_score = 1.0 - ensemble_score
            
            audio = librosa.load(audio_path, sr=16000)[0]
            features = feature_extractor.extract_all_features(audio)
            
            cloning_data.append({'score': spoof_score, 'features': features})
            
            if i % 10 == 0:
                logger.info(f"  Processed {i}/{len(cloning_files)} cloning")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    # Test configurations
    configs = [
        {'name': 'Baseline (0.50 only)', 'ensemble_threshold': 0.50, 'use_features': False},
        {'name': 'Ensemble 0.60 only', 'ensemble_threshold': 0.60, 'use_features': False},
        {'name': 'Ensemble 0.70 only', 'ensemble_threshold': 0.70, 'use_features': False},
        {
            'name': '0.60 + Features (Conservative)',
            'ensemble_threshold': 0.60,
            'use_features': True,
            'snr_threshold': 45,
            'artifacts_threshold': 0.5,
            'noise_threshold': 0.05,
            'min_indicators': 2
        },
        {
            'name': '0.60 + Features (Very Conservative)',
            'ensemble_threshold': 0.60,
            'use_features': True,
            'snr_threshold': 50,
            'artifacts_threshold': 0.6,
            'noise_threshold': 0.03,
            'min_indicators': 2
        },
        {
            'name': '0.60 + Features (3+ indicators)',
            'ensemble_threshold': 0.60,
            'use_features': True,
            'snr_threshold': 45,
            'artifacts_threshold': 0.4,
            'noise_threshold': 0.05,
            'min_indicators': 3
        }
    ]
    
    print("\n" + "=" * 100)
    print("EXACT METRICS FOR HIGHER ENSEMBLE THRESHOLDS")
    print("=" * 100)
    print()
    
    print(f"{'Configuration':<50} {'BPCER':<12} {'APCER':<12} {'ACER':<12}")
    print("-" * 100)
    
    for config in configs:
        genuine_rejected = sum(1 for s in genuine_data if is_spoof(s, config))
        cloning_accepted = sum(1 for s in cloning_data if not is_spoof(s, config))
        
        bpcer = (genuine_rejected / len(genuine_data) * 100) if genuine_data else 0
        apcer = (cloning_accepted / len(cloning_data) * 100) if cloning_data else 0
        acer = (bpcer + apcer) / 2
        
        print(f"{config['name']:<50} {bpcer:<12.2f} {apcer:<12.2f} {acer:<12.2f}")
    
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
    test_higher_thresholds()
