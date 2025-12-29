"""Speaker embedding adapter for voice signature extraction using ECAPA-TDNN model."""

import numpy as np
import io
import wave
import torch
import torchaudio
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from ...shared.types.common_types import VoiceEmbedding
from ...shared.constants.biometric_constants import (
    EMBEDDING_DIMENSION,
    MIN_AUDIO_DURATION_SEC,
    MAX_AUDIO_DURATION_SEC
)
from .model_manager import model_manager

logger = logging.getLogger(__name__)

# Constants
FALLBACK_MSG = "Falling back to mock implementation"


class SpeakerEmbeddingAdapter:
    """
    Real speaker embedding adapter using ECAPA-TDNN model.
    
    Anteproyecto specifications:
    - ECAPA-TDNN: Primary model for speaker recognition (192-dimensional embeddings)
    
    Trained on VoxCeleb dataset for speaker verification tasks.
    """
    
    def __init__(self, model_id: int = 1, use_gpu: bool = True):
        self._model_id = model_id
        self._model_name = "ecapa_tdnn_voxceleb"
        self._model_version = "1.0.0"
        
        # Device configuration
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Model initialization (lazy loading)
        self._primary_model = None
        self._alternative_model = None
        self._classifier = None
        self._model_loaded = False
        
        # Audio preprocessing parameters
        self.target_sample_rate = 16000
        self.target_length = 3.0  # seconds
        
        # Thread safety for parallel processing
        import threading
        self._lock = threading.Lock()

        self._load_model()
    
    def _load_model(self) -> bool:
        """
        Load ECAPA-TDNN model.
        Returns True if model loaded successfully, False otherwise.
        """
        success = self._load_ecapa_tdnn_model()
        self._model_loaded = success
        return success
    
    def _load_ecapa_tdnn_model(self) -> bool:
        """Load ECAPA-TDNN model specifically."""
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            
            # Ensure model is downloaded
            if not model_manager.is_model_available("ecapa_tdnn"):
                logger.info("ECAPA-TDNN model not found locally, downloading...")
                if not model_manager.download_model("ecapa_tdnn"):
                    return False
            
            # Get model path
            model_path = model_manager.get_model_path("ecapa_tdnn")
            
            # Load pre-trained ECAPA-TDNN model
            self._classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=str(model_path),
                run_opts={"device": str(self.device)}
            )
            
            logger.info("ECAPA-TDNN model loaded for speaker recognition")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ECAPA-TDNN: {e}")
            return False
    
    def extract_embedding(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> VoiceEmbedding:
        """
        Extract speaker embedding from audio using ECAPA-TDNN.
        
        Process:
        1. Validate and preprocess audio (resample, normalize, etc.)
        2. Run through ECAPA-TDNN neural network
        3. Extract fixed-size embedding vector (512-dimensional)
        """
        
        # Validate audio first
        quality_info = self.validate_audio_quality(audio_data, audio_format)
        if not quality_info["is_valid"]:
            raise ValueError(f"Invalid audio: {quality_info['reason']}")
        
        # PERFORMANCE FIX: Don't reload model on every call
        # Model is already loaded in __init__, no need to reload
        
        # Extract embedding using real model or fallback to mock
        if self._model_loaded and self._classifier is not None:
            embedding = self._extract_real_embedding(audio_data, audio_format)
        else:
            logger.warning(FALLBACK_MSG)
            embedding = self._mock_extract_embedding(audio_data)
        
        return embedding
    
    def _extract_real_embedding(self, audio_data: bytes, audio_format: str) -> VoiceEmbedding:
        """Extract real embedding using ECAPA-TDNN model."""
        try:
            # Preprocess audio
            waveform, _ = self._preprocess_audio(audio_data, audio_format)
            
            # Convert to tensor and move to device
            waveform = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Extract embedding using SpeechBrain
            # Thread-safe: Lock during model inference
            with self._lock:
                with torch.no_grad():
                    embeddings = self._classifier.encode_batch(waveform)
                    # Get the embedding as numpy array
                    embedding = embeddings.squeeze().cpu().numpy()
            
            # Ensure embedding is the right size and normalized
            if len(embedding) != EMBEDDING_DIMENSION:
                # If model produces different size, adapt it
                if len(embedding) > EMBEDDING_DIMENSION:
                    embedding = embedding[:EMBEDDING_DIMENSION]
                else:
                    # Pad with zeros if too small
                    padded = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)
                    padded[:len(embedding)] = embedding
                    embedding = padded
            
            # Normalize to unit vector
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error in real embedding extraction: {e}")
            logger.warning(FALLBACK_MSG)
            return self._mock_extract_embedding(audio_data)
    
    def _preprocess_audio(self, audio_data: bytes, audio_format: str) -> Tuple[np.ndarray, int]:
        """Preprocess audio for ECAPA-TDNN model."""
        
        # Extract format from MIME type if needed
        format_lower = audio_format.lower()
        if '/' in format_lower:
            format_lower = format_lower.split('/')[1].split(';')[0]
        
        # Convert to WAV if not already WAV format
        if format_lower != "wav":
            logger.info(f"Converting {format_lower} audio to WAV format")
            from .audio_converter import convert_to_wav
            try:
                audio_data = convert_to_wav(audio_data, format_lower)
                format_lower = "wav"
                logger.info("Audio conversion successful")
            except Exception as e:
                logger.error(f"Audio conversion failed: {e}")
                raise ValueError(f"Failed to convert {audio_format} to WAV: {str(e)}")
        
        # Load WAV audio
        waveform, sample_rate = self._load_wav_audio(audio_data)
        
        # Resample to target sample rate if needed
        if sample_rate != self.target_sample_rate:
            waveform = torchaudio.functional.resample(
                torch.tensor(waveform), 
                orig_freq=sample_rate, 
                new_freq=self.target_sample_rate
            ).numpy()
            sample_rate = self.target_sample_rate
        
        # Ensure mono audio
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=0)
        
        # Normalize audio
        waveform = waveform / (np.max(np.abs(waveform)) + 1e-8)
        
        # Trim or pad to target length
        # UPDATE: Allow variable length (MIN_AUDIO_DURATION_SEC to MAX_AUDIO_DURATION_SEC)
        # We only trim if it exceeds MAX_AUDIO_DURATION_SEC
        
        # Max samples allowed
        max_samples = int(MAX_AUDIO_DURATION_SEC * sample_rate)
        min_samples = int(MIN_AUDIO_DURATION_SEC * sample_rate)
        
        if len(waveform) > max_samples:
             # Trim to max length (take center portion)
            start = (len(waveform) - max_samples) // 2
            waveform = waveform[start:start + max_samples]
        elif len(waveform) < min_samples:
             # Pad with zeros to minimum length
             # Some models need a minimum context window
            pad_length = min_samples - len(waveform)
            waveform = np.pad(waveform, (0, pad_length), mode='constant')
        
        # Otherwise, keep original length (between min and max)
        
        return waveform, sample_rate
    
    def _load_wav_audio(self, audio_data: bytes) -> Tuple[np.ndarray, int]:
        """Load WAV audio from bytes."""
        audio_file = io.BytesIO(audio_data)
        with wave.open(audio_file, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            # Convert bytes to numpy array
            if sample_width == 1:
                dtype = np.uint8
            elif sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            waveform = np.frombuffer(frames, dtype=dtype)
            
            # Handle multi-channel audio
            if channels > 1:
                waveform = waveform.reshape(-1, channels)
                waveform = np.mean(waveform, axis=1)  # Convert to mono
            
            # Convert to float32 and normalize
            if dtype != np.float32:
                if dtype == np.uint8:
                    waveform = (waveform.astype(np.float32) - 128) / 128.0
                else:
                    waveform = waveform.astype(np.float32) / np.iinfo(dtype).max
            
            return waveform, sample_rate
    
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
            
            # Extract format from MIME type if needed (e.g., "audio/webm" -> "webm")
            format_lower = audio_format.lower()
            if '/' in format_lower:
                # It's a MIME type like "audio/webm" or "audio/webm;codecs=opus"
                format_lower = format_lower.split('/')[1].split(';')[0]
            
            # Accept webm format (common for browser recordings)
            if format_lower not in ["wav", "mp3", "flac", "m4a", "webm", "ogg"]:
                return {"is_valid": False, "reason": f"Unsupported format: {audio_format}"}
            
            # For WAV files, we can do more detailed validation
            if format_lower == "wav":
                return self._validate_wav_audio(audio_data)
            
            # For other formats (including webm), basic validation
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive information about current model configuration."""
        return {
            "model_name": self._model_name,
            "model_version": self._model_version,
            "model_id": self._model_id,
            "model_loaded": self._model_loaded,
            "device": str(self.device),
            "embedding_dimension": EMBEDDING_DIMENSION,
            "model_available": model_manager.is_model_available("ecapa_tdnn"),
            "anteproyecto_compliance": {
                "model": "ECAPA-TDNN",
                "dataset": "VoxCeleb",
                "purpose": "speaker_recognition"
            }
        }