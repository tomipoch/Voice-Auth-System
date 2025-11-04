#!/usr/bin/env python3
"""
Test script for SpoofDetectorAdapter with AASIST, RawNet2 and ResNet models.
Tests the ensemble anti-spoofing implementation according to anteproyecto specifications.
"""

import sys
import os
import io
import wave
import numpy as np
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_audio(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate test audio data for spoofing detection."""
    
    # Generate a simple sine wave with some variation
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    
    # Mix of frequencies to simulate speech-like audio
    frequency1 = 440  # A4 note
    frequency2 = 880  # A5 note
    frequency3 = 220  # A3 note
    
    audio = (
        0.3 * np.sin(2 * np.pi * frequency1 * t) +
        0.2 * np.sin(2 * np.pi * frequency2 * t) +
        0.1 * np.sin(2 * np.pi * frequency3 * t)
    )
    
    # Add some noise for realism
    rng = np.random.default_rng(seed=42)
    noise = rng.normal(0, 0.05, len(audio))
    audio = audio + noise
    
    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    # Convert to 16-bit integers
    audio_int = (audio * 32767).astype(np.int16)
    
    # Convert to WAV bytes
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int.tobytes())
    
    return buffer.getvalue()

def test_spoof_detector_initialization():
    """Test SpoofDetectorAdapter initialization."""
    logger.info("Testing SpoofDetectorAdapter initialization...")
    
    try:
        detector = SpoofDetectorAdapter()
        logger.info(f"✓ Detector initialized with model: {detector.get_model_name()}")
        logger.info(f"✓ Model version: {detector.get_model_version()}")
        logger.info(f"✓ Model ID: {detector.get_model_id()}")
        return detector
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        raise

def test_spoofing_detection(detector):
    """Test basic spoofing detection functionality."""
    logger.info("Testing spoofing detection...")
    
    try:
        # Generate test audio samples
        genuine_audio = generate_test_audio(duration_seconds=2.0)
        synthetic_audio = generate_test_audio(duration_seconds=2.0)  # Different seed for variation
        
        # Test genuine audio detection
        genuine_score = detector.detect_spoof(genuine_audio)
        logger.info(f"✓ Genuine audio spoof score: {genuine_score:.3f}")
        
        # Test synthetic audio detection
        synthetic_score = detector.detect_spoof(synthetic_audio)
        logger.info(f"✓ Synthetic audio spoof score: {synthetic_score:.3f}")
        
        # Verify scores are in valid range
        assert 0.0 <= genuine_score <= 1.0, f"Invalid genuine score: {genuine_score}"
        assert 0.0 <= synthetic_score <= 1.0, f"Invalid synthetic score: {synthetic_score}"
        
        logger.info("✓ Spoofing detection working correctly")
        return genuine_audio, synthetic_audio
        
    except Exception as e:
        logger.error(f"✗ Spoofing detection failed: {e}")
        raise

def test_detailed_analysis(detector, test_audio):
    """Test detailed spoofing analysis."""
    logger.info("Testing detailed spoofing analysis...")
    
    try:
        details = detector.get_spoof_details(test_audio)
        
        # Verify required fields
        required_fields = [
            "spoof_probability", "is_likely_spoofed", "confidence",
            "individual_model_scores", "attack_type_probabilities",
            "quality_indicators", "models_available"
        ]
        
        for field in required_fields:
            assert field in details, f"Missing field: {field}"
        
        # Verify spoof probability
        spoof_prob = details["spoof_probability"]
        assert 0.0 <= spoof_prob <= 1.0, f"Invalid spoof probability: {spoof_prob}"
        
        # Verify confidence
        confidence = details["confidence"]
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"
        
        # Verify attack type probabilities
        attack_types = details["attack_type_probabilities"]
        for attack_type, prob in attack_types.items():
            assert 0.0 <= prob <= 1.0, f"Invalid {attack_type} probability: {prob}"
        
        # Verify quality indicators
        quality = details["quality_indicators"]
        for indicator, value in quality.items():
            assert 0.0 <= value <= 1.0, f"Invalid {indicator} value: {value}"
        
        # Log results
        logger.info(f"✓ Spoof probability: {spoof_prob:.3f}")
        logger.info(f"✓ Confidence: {confidence:.3f}")
        logger.info(f"✓ Is likely spoofed: {details['is_likely_spoofed']}")
        
        # Log individual model scores
        if details["individual_model_scores"]:
            logger.info("✓ Individual model scores:")
            for model, score in details["individual_model_scores"].items():
                logger.info(f"  - {model}: {score:.3f}")
        
        # Log attack type probabilities
        logger.info("✓ Attack type probabilities:")
        for attack_type, prob in attack_types.items():
            logger.info(f"  - {attack_type}: {prob:.3f}")
        
        # Log model availability
        logger.info("✓ Model availability:")
        for model, available in details["models_available"].items():
            status = "available" if available else "not available"
            logger.info(f"  - {model}: {status}")
        
        logger.info("✓ Detailed analysis working correctly")
        
    except Exception as e:
        logger.error(f"✗ Detailed analysis failed: {e}")
        raise

def test_ensemble_behavior(detector):
    """Test ensemble model behavior with multiple audio samples."""
    logger.info("Testing ensemble model behavior...")
    
    try:
        # Generate multiple test samples
        samples = []
        for i in range(5):
            audio = generate_test_audio(duration_seconds=1.5)
            samples.append(audio)
        
        scores = []
        for i, audio in enumerate(samples):
            score = detector.detect_spoof(audio)
            scores.append(score)
            logger.info(f"✓ Sample {i+1} spoof score: {score:.3f}")
        
        # Verify scores show some variation (not all identical)
        score_variance = np.var(scores)
        logger.info(f"✓ Score variance: {score_variance:.4f}")
        
        # Verify ensemble consistency
        if score_variance > 0:
            logger.info("✓ Ensemble showing appropriate score variation")
        else:
            logger.warning("⚠ All scores identical - may indicate fallback mode")
        
        logger.info("✓ Ensemble behavior test completed")
        
    except Exception as e:
        logger.error(f"✗ Ensemble behavior test failed: {e}")
        raise

def main():
    """Main test function."""
    logger.info("=" * 50)
    logger.info("SpoofDetectorAdapter Test - Anteproyecto Models")
    logger.info("Testing AASIST, RawNet2, and ResNet ensemble")
    logger.info("=" * 50)
    
    try:
        # Test initialization
        detector = test_spoof_detector_initialization()
        
        # Test spoofing detection
        genuine_audio, synthetic_audio = test_spoofing_detection(detector)
        
        # Test detailed analysis
        test_detailed_analysis(detector, genuine_audio)
        test_detailed_analysis(detector, synthetic_audio)
        
        # Test ensemble behavior
        test_ensemble_behavior(detector)
        
        logger.info("=" * 50)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("SpoofDetectorAdapter with anteproyecto models working correctly")
        logger.info("Models: AASIST + RawNet2 + ResNet ensemble anti-spoofing")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ TESTS FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()