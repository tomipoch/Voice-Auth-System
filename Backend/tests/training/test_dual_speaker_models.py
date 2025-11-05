#!/usr/bin/env python3
"""
Test script for dual model support in SpeakerEmbeddingAdapter.
Tests ECAPA-TDNN and x-vector models comparison according to anteproyecto specifications.
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

from infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_audio(duration_seconds: float = 3.0, sample_rate: int = 16000, seed: int = 42) -> bytes:
    """Generate test audio data for speaker recognition."""
    
    # Generate speech-like audio with speaker characteristics
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    
    # Create speaker-specific voice characteristics
    rng = np.random.default_rng(seed=seed)
    
    # Fundamental frequency (varies by speaker)
    f0 = 150 + seed % 100  # Base frequency between 150-250 Hz
    
    # Formant frequencies (speaker-specific)
    f1 = 700 + (seed % 50) * 10  # First formant
    f2 = 1220 + (seed % 30) * 20  # Second formant
    f3 = 2600 + (seed % 20) * 30  # Third formant
    
    # Generate harmonic content
    audio = np.zeros_like(t)
    
    # Fundamental and harmonics
    for harmonic in range(1, 6):
        freq = f0 * harmonic
        if freq < sample_rate / 2:  # Avoid aliasing
            amplitude = 1.0 / harmonic  # Harmonic series decay
            audio += amplitude * np.sin(2 * np.pi * freq * t)
    
    # Add formant resonances
    formant_content = (
        0.3 * np.sin(2 * np.pi * f1 * t) +
        0.2 * np.sin(2 * np.pi * f2 * t) +
        0.1 * np.sin(2 * np.pi * f3 * t)
    )
    
    # Modulate with speech-like envelope
    envelope = np.sin(2 * np.pi * 3 * t) ** 2  # 3 Hz modulation
    audio = audio * envelope + 0.2 * formant_content
    
    # Add realistic noise
    noise = rng.normal(0, 0.02, len(audio))
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

def test_dual_model_initialization():
    """Test initialization with both model types."""
    logger.info("Testing dual model initialization...")
    
    try:
        # Test ECAPA-TDNN initialization
        ecapa_adapter = SpeakerEmbeddingAdapter(model_type="ecapa_tdnn")
        logger.info(f"✓ ECAPA-TDNN adapter: {ecapa_adapter.get_model_name()}")
        
        # Test x-vector initialization
        xvector_adapter = SpeakerEmbeddingAdapter(model_type="x_vector")
        logger.info(f"✓ x-vector adapter: {xvector_adapter.get_model_name()}")
        
        # Test model info
        ecapa_info = ecapa_adapter.get_model_info()
        xvector_info = xvector_adapter.get_model_info()
        
        logger.info(f"✓ ECAPA-TDNN current type: {ecapa_info['current_model_type']}")
        logger.info(f"✓ x-vector current type: {xvector_info['current_model_type']}")
        
        # Test anteproyecto compliance
        compliance = ecapa_info['anteproyecto_compliance']
        logger.info(f"✓ Primary model: {compliance['primary_model']}")
        logger.info(f"✓ Alternative model: {compliance['alternative_model']}")
        logger.info(f"✓ Dataset: {compliance['dataset']}")
        
        return ecapa_adapter
        
    except Exception as e:
        logger.error(f"✗ Dual model initialization failed: {e}")
        raise

def test_model_switching(adapter):
    """Test switching between model types."""
    logger.info("Testing model switching...")
    
    try:
        # Start with ECAPA-TDNN
        original_type = adapter.get_model_type()
        logger.info(f"✓ Starting with: {original_type}")
        
        # Switch to x-vector
        success = adapter.switch_model_type("x_vector")
        new_type = adapter.get_model_type()
        logger.info(f"✓ Switched to: {new_type}, success: {success}")
        assert new_type == "x_vector", f"Expected x_vector, got {new_type}"
        
        # Switch back to ECAPA-TDNN
        success = adapter.switch_model_type("ecapa_tdnn")
        final_type = adapter.get_model_type()
        logger.info(f"✓ Switched back to: {final_type}, success: {success}")
        assert final_type == "ecapa_tdnn", f"Expected ecapa_tdnn, got {final_type}"
        
        # Test invalid model type
        success = adapter.switch_model_type("invalid_model")
        assert not success, "Invalid model switch should fail"
        logger.info("✓ Invalid model type correctly rejected")
        
        logger.info("✓ Model switching working correctly")
        
    except Exception as e:
        logger.error(f"✗ Model switching failed: {e}")
        raise

def test_individual_embeddings(adapter):
    """Test individual embedding extraction with both models."""
    logger.info("Testing individual embedding extraction...")
    
    try:
        # Generate test audio
        test_audio = generate_test_audio(seed=123)
        
        # Test ECAPA-TDNN embedding
        adapter.switch_model_type("ecapa_tdnn")
        ecapa_embedding = adapter.extract_embedding(test_audio, "wav")
        
        logger.info(f"✓ ECAPA-TDNN embedding shape: {ecapa_embedding.shape}")
        logger.info(f"✓ ECAPA-TDNN embedding norm: {np.linalg.norm(ecapa_embedding):.3f}")
        
        # Verify embedding properties
        assert len(ecapa_embedding) == 192, f"Expected 192 dimensions, got {len(ecapa_embedding)}"
        assert np.allclose(np.linalg.norm(ecapa_embedding), 1.0, atol=1e-6), "Embedding should be normalized"
        
        # Test x-vector embedding
        adapter.switch_model_type("x_vector")
        xvector_embedding = adapter.extract_embedding(test_audio, "wav")
        
        logger.info(f"✓ x-vector embedding shape: {xvector_embedding.shape}")
        logger.info(f"✓ x-vector embedding norm: {np.linalg.norm(xvector_embedding):.3f}")
        
        # Verify embedding properties
        assert len(xvector_embedding) == 192, f"Expected 192 dimensions, got {len(xvector_embedding)}"
        assert np.allclose(np.linalg.norm(xvector_embedding), 1.0, atol=1e-6), "Embedding should be normalized"
        
        logger.info("✓ Individual embeddings extracted correctly")
        return ecapa_embedding, xvector_embedding
        
    except Exception as e:
        logger.error(f"✗ Individual embedding extraction failed: {e}")
        raise

def test_model_comparison(adapter):
    """Test comprehensive model comparison functionality."""
    logger.info("Testing model comparison...")
    
    try:
        # Generate test audio for different speakers
        speaker1_audio = generate_test_audio(seed=100)
        speaker2_audio = generate_test_audio(seed=200)
        
        # Compare models for speaker 1
        logger.info("Comparing models for speaker 1...")
        comparison1 = adapter.compare_models(speaker1_audio, "wav")
        
        # Verify comparison structure
        assert comparison1["success"], "Comparison should succeed"
        assert comparison1["ecapa_tdnn"] is not None, "ECAPA-TDNN result missing"
        assert comparison1["x_vector"] is not None, "x-vector result missing"
        assert comparison1["comparison"] is not None, "Comparison metrics missing"
        
        # Log comparison results
        comp_metrics = comparison1["comparison"]
        logger.info(f"✓ Speaker 1 - Cosine similarity: {comp_metrics['cosine_similarity']:.3f}")
        logger.info(f"✓ Speaker 1 - Euclidean distance: {comp_metrics['euclidean_distance']:.3f}")
        logger.info(f"✓ Speaker 1 - Correlation: {comp_metrics['correlation']:.3f}")
        logger.info(f"✓ Speaker 1 - Combined score: {comp_metrics['similarity_score']:.3f}")
        
        # Compare models for speaker 2
        logger.info("Comparing models for speaker 2...")
        comparison2 = adapter.compare_models(speaker2_audio, "wav")
        
        assert comparison2["success"], "Comparison should succeed"
        
        comp_metrics2 = comparison2["comparison"]
        logger.info(f"✓ Speaker 2 - Cosine similarity: {comp_metrics2['cosine_similarity']:.3f}")
        logger.info(f"✓ Speaker 2 - Euclidean distance: {comp_metrics2['euclidean_distance']:.3f}")
        logger.info(f"✓ Speaker 2 - Correlation: {comp_metrics2['correlation']:.3f}")
        logger.info(f"✓ Speaker 2 - Combined score: {comp_metrics2['similarity_score']:.3f}")
        
        # Verify embedding properties
        for speaker_name, comparison in [("Speaker 1", comparison1), ("Speaker 2", comparison2)]:
            ecapa_info = comparison["ecapa_tdnn"]
            xvector_info = comparison["x_vector"]
            
            assert ecapa_info["dimension"] == 192, f"{speaker_name} ECAPA-TDNN wrong dimension"
            assert xvector_info["dimension"] == 192, f"{speaker_name} x-vector wrong dimension"
            assert abs(ecapa_info["norm"] - 1.0) < 0.01, f"{speaker_name} ECAPA-TDNN not normalized"
            assert abs(xvector_info["norm"] - 1.0) < 0.01, f"{speaker_name} x-vector not normalized"
        
        logger.info("✓ Model comparison working correctly")
        return comparison1, comparison2
        
    except Exception as e:
        logger.error(f"✗ Model comparison failed: {e}")
        raise

def test_speaker_discrimination(adapter):
    """Test that both models can discriminate between different speakers."""
    logger.info("Testing speaker discrimination...")
    
    try:
        # Generate audio for 3 different speakers
        speakers = []
        for i, seed in enumerate([300, 400, 500]):
            audio = generate_test_audio(seed=seed)
            speakers.append((f"Speaker_{i+1}", audio))
        
        # Test discrimination for each model
        for model_type in ["ecapa_tdnn", "x_vector"]:
            adapter.switch_model_type(model_type)
            
            # Extract embeddings for all speakers
            embeddings = {}
            for speaker_name, audio in speakers:
                embedding = adapter.extract_embedding(audio, "wav")
                embeddings[speaker_name] = embedding
            
            # Test discrimination capability
            discrimination_score = _test_model_discrimination(embeddings, model_type)
            logger.info(f"✓ {model_type.upper()} discrimination score: {discrimination_score:.3f}")
            
            # Good models should have high discrimination
            assert discrimination_score > 0.3, f"{model_type} discrimination too low"
        
        logger.info("✓ Speaker discrimination test passed for both models")
        
    except Exception as e:
        logger.error(f"✗ Speaker discrimination test failed: {e}")
        raise

def _test_model_discrimination(embeddings, model_type):
    """Helper function to test discrimination for a single model."""
    speaker_names = list(embeddings.keys())
    similarities = []
    
    # Calculate all pairwise similarities
    for i, speaker1 in enumerate(speaker_names):
        for j, speaker2 in enumerate(speaker_names):
            if i != j:  # Different speakers
                emb1 = embeddings[speaker1]
                emb2 = embeddings[speaker2]
                sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                similarities.append(sim)
                logger.info(f"  {speaker1} vs {speaker2}: {sim:.3f}")
    
    # Return discrimination metric (1 - average similarity)
    avg_similarity = np.mean(similarities)
    return 1.0 - avg_similarity

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("SpeakerEmbeddingAdapter Dual Model Test - Anteproyecto")
    logger.info("Testing ECAPA-TDNN and x-vector models comparison")
    logger.info("=" * 60)
    
    try:
        # Test dual model initialization
        adapter = test_dual_model_initialization()
        
        # Test model switching
        test_model_switching(adapter)
        
        # Test individual embeddings
        test_individual_embeddings(adapter)
        
        # Test model comparison
        test_model_comparison(adapter)
        
        # Test speaker discrimination
        test_speaker_discrimination(adapter)
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("Dual model support working correctly:")
        logger.info("- ECAPA-TDNN: Primary speaker recognition model")
        logger.info("- x-vector: Alternative model for academic comparison")
        logger.info("- Model switching and comparison functionality")
        logger.info("- Speaker discrimination capabilities")
        logger.info("- Anteproyecto compliance verified")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ TESTS FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()