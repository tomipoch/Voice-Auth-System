"""Test script for real ECAPA-TDNN speaker embedding extraction."""

import sys
import logging
import numpy as np
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
from infrastructure.biometrics.model_manager import model_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_audio() -> bytes:
    """Create a simple test WAV audio for testing."""
    import wave
    import numpy as np
    import io
    
    # Generate a simple sine wave
    sample_rate = 16000
    duration = 3.0  # seconds
    frequency = 440  # Hz (A4 note)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return buffer.getvalue()


def test_model_manager():
    """Test the model manager functionality."""
    logger.info("Testing Model Manager...")
    
    # List all models
    models = model_manager.list_models()
    logger.info(f"Available models: {list(models.keys())}")
    
    for model_id, info in models.items():
        logger.info(f"{model_id}: {info['name']} - Available: {info['available']}")
    
    # Test download (this might take a while for real models)
    logger.info("Testing model download for ECAPA-TDNN...")
    success = model_manager.download_model("ecapa_tdnn")
    logger.info(f"Download result: {success}")
    
    return success


def test_speaker_embedding():
    """Test speaker embedding extraction."""
    logger.info("Testing Speaker Embedding Extraction...")
    
    # Create adapter
    adapter = SpeakerEmbeddingAdapter(use_gpu=False)  # Use CPU for testing
    
    # Create test audio
    logger.info("Creating test audio...")
    test_audio = create_test_audio()
    logger.info(f"Test audio size: {len(test_audio)} bytes")
    
    try:
        # Extract embedding
        logger.info("Extracting embedding...")
        embedding = adapter.extract_embedding(test_audio, "wav")
        
        logger.info(f"Embedding shape: {embedding.shape}")
        logger.info(f"Embedding type: {type(embedding)}")
        logger.info(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
        logger.info(f"First 5 values: {embedding[:5]}")
        
        # Test with same audio again (should produce same embedding)
        embedding2 = adapter.extract_embedding(test_audio, "wav")
        similarity = np.dot(embedding, embedding2)
        logger.info(f"Self-similarity: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in embedding extraction: {e}", exc_info=True)
        return False


def main():
    """Main test function."""
    logger.info("Starting ECAPA-TDNN tests...")
    
    try:
        # Test model manager
        model_success = test_model_manager()
        
        # Test speaker embedding
        embedding_success = test_speaker_embedding()
        
        if model_success and embedding_success:
            logger.info("✅ All tests passed!")
        else:
            logger.error("❌ Some tests failed")
            
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()