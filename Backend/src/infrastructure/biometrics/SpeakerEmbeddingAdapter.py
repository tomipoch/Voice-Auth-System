"""Speaker embedding adapter for voice signature extraction."""

import numpy as np
import io
import wave
from typing import Optional, Dict, Any

from ...shared.types.common_types import VoiceEmbedding
from ...shared.constants.biometric_constants import (
    EMBEDDING_DIMENSION,
    MIN_AUDIO_DURATION_SEC,
    MAX_AUDIO_DURATION_SEC
)


class SpeakerEmbeddingAdapter:
    """
    Adapter for speaker embedding extraction.
    In production, this would integrate with real ML models like ECAPA-TDNN,
    x-vector, or similar speaker recognition models.
    """
    
    def __init__(self, model_id: int = 1, model_name: str = "ecapa_tdnn_v1"):
        self._model_id = model_id
        self._model_name = model_name
        self._model_version = "1.0.0"
        
        # In production, load actual ML model here
        # self._model = torch.jit.load("path/to/speaker_model.pt")
    
    def extract_embedding(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> VoiceEmbedding:
        """
        Extract speaker embedding from audio.
        
        In production, this would:
        1. Preprocess audio (resample, normalize, etc.)
        2. Run through neural network (ECAPA-TDNN, etc.)
        3. Extract fixed-size embedding vector
        """
        
        # Validate audio first
        quality_info = self.validate_audio_quality(audio_data, audio_format)
        if not quality_info["is_valid"]:
            raise ValueError(f"Invalid audio: {quality_info['reason']}")
        
        # Mock implementation - in production, replace with actual model inference
        # For now, generate a pseudo-random embedding based on audio characteristics
        embedding = self._mock_extract_embedding(audio_data)
        
        return embedding
    
    def validate_audio_quality(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> Dict[str, Any]:
        """Validate audio quality for processing."""
        
        try:
            # Basic validation
            if len(audio_data) == 0:
                return {"is_valid": False, "reason": "Empty audio data"}
            
            if audio_format.lower() not in ["wav", "mp3", "flac", "m4a"]:
                return {"is_valid": False, "reason": f"Unsupported format: {audio_format}"}
            
            # For WAV files, we can do more detailed validation
            if audio_format.lower() == "wav":
                return self._validate_wav_audio(audio_data)
            
            # For other formats, basic validation
            return {
                "is_valid": True,
                "duration_sec": 3.0,  # Mock duration
                "sample_rate": 16000,
                "channels": 1,
                "snr_db": 25.0
            }
            
        except Exception as e:
            return {"is_valid": False, "reason": f"Audio validation error: {str(e)}"}
    
    def _validate_wav_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Validate WAV audio format."""
        try:
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                duration_sec = frames / sample_rate
                
                # Check duration limits
                if duration_sec < MIN_AUDIO_DURATION_SEC:
                    return {
                        "is_valid": False,
                        "reason": f"Audio too short: {duration_sec:.2f}s (min: {MIN_AUDIO_DURATION_SEC}s)"
                    }
                
                if duration_sec > MAX_AUDIO_DURATION_SEC:
                    return {
                        "is_valid": False,
                        "reason": f"Audio too long: {duration_sec:.2f}s (max: {MAX_AUDIO_DURATION_SEC}s)"
                    }
                
                # Check channels (prefer mono)
                if channels > 2:
                    return {"is_valid": False, "reason": f"Too many channels: {channels}"}
                
                # Check sample rate (prefer 16kHz)
                if sample_rate < 8000:
                    return {"is_valid": False, "reason": f"Sample rate too low: {sample_rate}Hz"}
                
                # Estimate SNR (mock calculation)
                snr_db = self._estimate_snr()
                
                return {
                    "is_valid": True,
                    "duration_sec": duration_sec,
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "sample_width": sample_width,
                    "snr_db": snr_db
                }
                
        except Exception as e:
            return {"is_valid": False, "reason": f"WAV validation error: {str(e)}"}
    
    def _estimate_snr(self) -> float:
        """Estimate Signal-to-Noise Ratio (mock implementation)."""
        # In production, this would analyze actual audio signal
        # For now, return a reasonable mock value
        rng = np.random.default_rng(seed=42)
        return rng.uniform(15.0, 30.0)
    
    def _mock_extract_embedding(self, audio_data: bytes) -> VoiceEmbedding:
        """
        Mock embedding extraction for demonstration.
        In production, replace with actual neural network inference.
        """
        
        # Create a pseudo-random but deterministic embedding based on audio
        # This ensures same audio produces same embedding (for testing)
        hash_value = hash(audio_data) % (2**32)
        rng = np.random.default_rng(seed=hash_value)
        
        # Generate random embedding
        embedding = rng.normal(0, 1, EMBEDDING_DIMENSION).astype(np.float32)
        
        # Normalize to unit vector
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def get_model_id(self) -> int:
        """Get model ID for audit trail."""
        return self._model_id
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    def get_model_version(self) -> str:
        """Get model version."""
        return self._model_version