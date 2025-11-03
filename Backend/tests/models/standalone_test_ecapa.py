"""Standalone test script for ECAPA-TDNN speaker embedding extraction."""

import sys
import os
import logging
import numpy as np
import torch
import torchaudio
import io
import wave
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants (from shared/constants/biometric_constants.py)
EMBEDDING_DIMENSION = 512
MIN_AUDIO_DURATION_SEC = 1.0
MAX_AUDIO_DURATION_SEC = 30.0

def create_test_audio() -> bytes:
    """Create a simple test WAV audio for testing."""
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


def test_speechbrain_installation():
    """Test if SpeechBrain is properly installed."""
    try:
        import speechbrain
        from speechbrain.pretrained import EncoderClassifier
        logger.info(f"SpeechBrain version: {speechbrain.__version__}")
        logger.info("✅ SpeechBrain imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ SpeechBrain import failed: {e}")
        return False


def test_ecapa_tdnn_download():
    """Test downloading ECAPA-TDNN model."""
    try:
        from speechbrain.pretrained import EncoderClassifier
        
        logger.info("Downloading ECAPA-TDNN model (this may take a few minutes)...")
        
        # Create models directory
        models_dir = Path("../../models/ecapa_tdnn")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download model
        classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(models_dir),
            run_opts={"device": "cpu"}  # Use CPU for testing
        )
        
        logger.info("✅ Model downloaded successfully")
        return classifier
        
    except Exception as e:
        logger.error(f"❌ Model download failed: {e}")
        return None


def test_embedding_extraction(classifier):
    """Test embedding extraction with the real model."""
    try:
        # Create test audio
        logger.info("Creating test audio...")
        test_audio = create_test_audio()
        
        # Load audio from bytes
        audio_file = io.BytesIO(test_audio)
        with wave.open(audio_file, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            
            # Convert to numpy array
            waveform = np.frombuffer(frames, dtype=np.int16)
            waveform = waveform.astype(np.float32) / np.iinfo(np.int16).max
        
        # Convert to tensor
        waveform_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)
        
        logger.info(f"Audio shape: {waveform_tensor.shape}")
        logger.info(f"Sample rate: {sample_rate}")
        
        # Extract embedding
        logger.info("Extracting embedding with ECAPA-TDNN...")
        with torch.no_grad():
            embeddings = classifier.encode_batch(waveform_tensor)
            embedding = embeddings.squeeze().cpu().numpy()
        
        logger.info("✅ Embedding extracted successfully")
        logger.info(f"Embedding shape: {embedding.shape}")
        logger.info(f"Embedding type: {type(embedding)}")
        logger.info(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
        logger.info(f"First 5 values: {embedding[:5]}")
        
        # Test with same audio again (should produce same or very similar embedding)
        with torch.no_grad():
            embeddings2 = classifier.encode_batch(waveform_tensor)
            embedding2 = embeddings2.squeeze().cpu().numpy()
        
        # Calculate similarity
        similarity = np.dot(embedding, embedding2) / (np.linalg.norm(embedding) * np.linalg.norm(embedding2))
        logger.info(f"Self-similarity: {similarity:.4f}")
        
        if similarity > 0.99:
            logger.info("✅ Embedding extraction is deterministic")
        else:
            logger.warning(f"⚠️ Embedding extraction may not be deterministic (similarity: {similarity:.4f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding extraction failed: {e}", exc_info=True)
        return False


def main():
    """Main test function."""
    logger.info("🚀 Starting ECAPA-TDNN standalone tests...")
    
    try:
        # Test 1: SpeechBrain installation
        if not test_speechbrain_installation():
            logger.error("❌ SpeechBrain not available. Please install with: pip install speechbrain")
            return
        
        # Test 2: Model download
        classifier = test_ecapa_tdnn_download()
        if classifier is None:
            logger.error("❌ Could not download ECAPA-TDNN model")
            return
        
        # Test 3: Embedding extraction
        if not test_embedding_extraction(classifier):
            logger.error("❌ Embedding extraction failed")
            return
        
        logger.info("🎉 All tests passed! ECAPA-TDNN is working correctly.")
        
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()