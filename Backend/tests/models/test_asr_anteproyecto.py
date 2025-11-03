#!/usr/bin/env python3
"""
Test script for ASRAdapter with lightweight ASR model.
Tests the speech recognition and phrase verification implementation according to anteproyecto specifications.
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

from infrastructure.biometrics.ASRAdapter import ASRAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_audio(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate test audio data for speech recognition."""
    
    # Generate a simple sine wave with some variation to simulate speech
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    
    # Mix of frequencies to simulate speech-like audio
    frequency1 = 300  # Lower frequency for vowels
    frequency2 = 1000  # Mid frequency for consonants
    frequency3 = 2000  # Higher frequency for fricatives
    
    # Create speech-like modulation
    modulation = np.sin(2 * np.pi * 5 * t)  # 5Hz modulation
    
    audio = (
        0.4 * np.sin(2 * np.pi * frequency1 * t) * (1 + 0.3 * modulation) +
        0.3 * np.sin(2 * np.pi * frequency2 * t) * (1 + 0.2 * np.sin(2 * np.pi * 8 * t)) +
        0.2 * np.sin(2 * np.pi * frequency3 * t) * (1 + 0.1 * np.sin(2 * np.pi * 12 * t))
    )
    
    # Add some noise for realism
    rng = np.random.default_rng(seed=42)
    noise = rng.normal(0, 0.03, len(audio))
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

def test_asr_initialization():
    """Test ASRAdapter initialization."""
    logger.info("Testing ASRAdapter initialization...")
    
    try:
        asr = ASRAdapter()
        logger.info(f"✓ ASR initialized with model: {asr.get_model_name()}")
        logger.info(f"✓ Model version: {asr.get_model_version()}")
        logger.info(f"✓ Model ID: {asr.get_model_id()}")
        return asr
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        raise

def test_transcription(asr):
    """Test basic transcription functionality."""
    logger.info("Testing speech transcription...")
    
    try:
        # Generate test audio samples with different characteristics
        short_audio = generate_test_audio(duration_seconds=1.0)
        medium_audio = generate_test_audio(duration_seconds=2.5)
        long_audio = generate_test_audio(duration_seconds=4.0)
        
        # Test transcription
        short_text = asr.transcribe(short_audio)
        medium_text = asr.transcribe(medium_audio)
        long_text = asr.transcribe(long_audio)
        
        logger.info(f"✓ Short audio transcription: '{short_text}'")
        logger.info(f"✓ Medium audio transcription: '{medium_text}'")
        logger.info(f"✓ Long audio transcription: '{long_text}'")
        
        # Verify transcriptions are strings and not empty
        assert isinstance(short_text, str) and len(short_text) > 0, "Short transcription invalid"
        assert isinstance(medium_text, str) and len(medium_text) > 0, "Medium transcription invalid"
        assert isinstance(long_text, str) and len(long_text) > 0, "Long transcription invalid"
        
        logger.info("✓ Transcription working correctly")
        return short_audio, medium_audio, long_audio, short_text, medium_text, long_text
        
    except Exception as e:
        logger.error(f"✗ Transcription failed: {e}")
        raise

def test_phrase_verification(asr, test_audio, expected_phrase):
    """Test phrase verification functionality."""
    logger.info(f"Testing phrase verification with: '{expected_phrase}'...")
    
    try:
        verification_result = asr.verify_phrase(test_audio, expected_phrase)
        
        # Verify required fields
        required_fields = [
            "recognized_text", "expected_phrase", "similarity", "phrase_matches",
            "confidence", "verification_quality", "details"
        ]
        
        for field in required_fields:
            assert field in verification_result, f"Missing field: {field}"
        
        # Verify field types and ranges
        assert isinstance(verification_result["recognized_text"], str)
        assert isinstance(verification_result["expected_phrase"], str)
        assert 0.0 <= verification_result["similarity"] <= 1.0
        assert isinstance(verification_result["phrase_matches"], bool)
        assert 0.0 <= verification_result["confidence"] <= 1.0
        assert verification_result["verification_quality"] in ["excellent", "good", "fair", "poor"]
        
        # Verify details structure
        details = verification_result["details"]
        detail_fields = [
            "word_accuracy", "semantic_similarity", "length_ratio", 
            "common_words", "edit_distance", "word_order_preserved", "key_words_present"
        ]
        
        for field in detail_fields:
            assert field in details, f"Missing detail field: {field}"
        
        # Log results
        logger.info(f"✓ Recognized text: '{verification_result['recognized_text']}'")
        logger.info(f"✓ Expected phrase: '{verification_result['expected_phrase']}'")
        logger.info(f"✓ Similarity: {verification_result['similarity']:.3f}")
        logger.info(f"✓ Phrase matches: {verification_result['phrase_matches']}")
        logger.info(f"✓ Confidence: {verification_result['confidence']:.3f}")
        logger.info(f"✓ Quality: {verification_result['verification_quality']}")
        
        # Log detailed analysis
        logger.info("✓ Detailed analysis:")
        logger.info(f"  - Word accuracy: {details['word_accuracy']:.3f}")
        logger.info(f"  - Semantic similarity: {details['semantic_similarity']:.3f}")
        logger.info(f"  - Length ratio: {details['length_ratio']:.3f}")
        logger.info(f"  - Edit distance: {details['edit_distance']}")
        logger.info(f"  - Word order preserved: {details['word_order_preserved']}")
        logger.info(f"  - Common words: {details['common_words']}")
        
        # Log key words analysis
        key_words = details['key_words_present']
        logger.info("✓ Key words analysis:")
        for category, present in key_words.items():
            logger.info(f"  - {category}: {'present' if present else 'not present'}")
        
        logger.info("✓ Phrase verification working correctly")
        return verification_result
        
    except Exception as e:
        logger.error(f"✗ Phrase verification failed: {e}")
        raise

def test_similarity_calculation(asr):
    """Test similarity calculation with known phrases."""
    logger.info("Testing similarity calculation...")
    
    try:
        test_cases = [
            ("hello world", "hello world", 1.0),  # Perfect match
            ("hello world", "hello earth", 0.5),  # Partial match
            ("voice authentication", "voice verification", 0.7),  # Similar words
            ("", "", 0.0),  # Empty strings
            ("test", "", 0.0),  # One empty
        ]
        
        for expected, recognized, min_similarity in test_cases:
            similarity = asr.calculate_phrase_similarity(expected, recognized)
            logger.info(f"✓ '{expected}' vs '{recognized}': {similarity:.3f}")
            
            if abs(min_similarity - 1.0) < 0.001:  # Perfect match
                assert abs(similarity - 1.0) < 0.001, f"Perfect match should be 1.0, got {similarity}"
            elif min_similarity > 0.0:
                assert similarity >= min_similarity * 0.8, f"Similarity too low: {similarity}"
            else:
                assert similarity >= 0.0, f"Similarity should be non-negative: {similarity}"
        
        logger.info("✓ Similarity calculation working correctly")
        
    except Exception as e:
        logger.error(f"✗ Similarity calculation failed: {e}")
        raise

def test_comprehensive_verification(asr):
    """Test comprehensive verification with multiple scenarios."""
    logger.info("Testing comprehensive verification scenarios...")
    
    try:
        test_scenarios = [
            {
                "expected": "voice authentication is working well",
                "description": "Long authentication phrase"
            },
            {
                "expected": "please verify my identity",
                "description": "Identity verification phrase"
            },
            {
                "expected": "hello world",
                "description": "Simple greeting"
            },
            {
                "expected": "security check",
                "description": "Short security phrase"
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            expected_phrase = scenario["expected"]
            description = scenario["description"]
            
            logger.info(f"Testing scenario: {description}")
            
            # Generate audio for this phrase
            test_audio = generate_test_audio(duration_seconds=3.0)
            
            # Verify phrase
            result = test_phrase_verification(asr, test_audio, expected_phrase)
            results.append((scenario, result))
            
            logger.info(f"✓ {description} - Quality: {result['verification_quality']}")
        
        # Analyze overall performance
        qualities = [result['verification_quality'] for _, result in results]
        excellent_count = qualities.count('excellent')
        good_count = qualities.count('good')
        fair_count = qualities.count('fair')
        poor_count = qualities.count('poor')
        
        logger.info("✓ Overall performance analysis:")
        logger.info(f"  - Excellent: {excellent_count}/{len(results)}")
        logger.info(f"  - Good: {good_count}/{len(results)}")
        logger.info(f"  - Fair: {fair_count}/{len(results)}")
        logger.info(f"  - Poor: {poor_count}/{len(results)}")
        
        # At least some results should be fair or better
        good_results = excellent_count + good_count + fair_count
        assert good_results > 0, "No good verification results"
        
        logger.info("✓ Comprehensive verification test completed")
        
    except Exception as e:
        logger.error(f"✗ Comprehensive verification failed: {e}")
        raise

def main():
    """Main test function."""
    logger.info("=" * 50)
    logger.info("ASRAdapter Test - Anteproyecto Lightweight ASR")
    logger.info("Testing speech recognition and phrase verification")
    logger.info("=" * 50)
    
    try:
        # Test initialization
        asr = test_asr_initialization()
        
        # Test transcription
        _, medium_audio, _, _, medium_text, _ = test_transcription(asr)
        
        # Test phrase verification with transcribed text
        test_phrase_verification(asr, medium_audio, medium_text)
        
        # Test similarity calculation
        test_similarity_calculation(asr)
        
        # Test comprehensive verification
        test_comprehensive_verification(asr)
        
        logger.info("=" * 50)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("ASRAdapter with lightweight ASR model working correctly")
        logger.info("Features: Speech transcription + Phrase verification + Quality analysis")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ TESTS FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()