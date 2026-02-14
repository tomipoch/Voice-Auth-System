"""Voice Biometric Engine Facade - main interface for biometric processing."""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from .SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
from .SpoofDetectorAdapter import SpoofDetectorAdapter
from .ASRAdapter import ASRAdapter
from ...shared.types.common_types import VoiceEmbedding


@dataclass
class BiometricAnalysisResult:
    """Result of complete biometric analysis."""
    similarity: float
    spoof_probability: float
    phrase_match: float
    phrase_ok: bool
    speaker_model_id: Optional[int] = None
    antispoof_model_id: Optional[int] = None
    asr_model_id: Optional[int] = None


class VoiceBiometricEngineFacade:
    """
    Facade that coordinates all biometric processing components.
    Provides a unified interface for voice analysis, hiding the complexity
    of individual adapters.
    """
    
    def __init__(
        self,
        speaker_adapter: SpeakerEmbeddingAdapter,
        spoof_adapter: SpoofDetectorAdapter,
        asr_adapter: ASRAdapter
    ):
        self._speaker_adapter = speaker_adapter
        self._spoof_adapter = spoof_adapter
        self._asr_adapter = asr_adapter
    
    def analyze_voice(
        self,
        audio_data: bytes,
        audio_format: str,
        reference_embedding: VoiceEmbedding,
        expected_phrase: Optional[str] = None
    ) -> BiometricAnalysisResult:
        """
        Perform complete voice biometric analysis.
        
        This method orchestrates all biometric components to provide
        a comprehensive analysis of the voice sample.
        """
        
        # 1. Extract speaker embedding
        current_embedding = self._speaker_adapter.extract_embedding(
            audio_data, audio_format
        )
        
        # 2. Calculate similarity with reference
        similarity = self._calculate_similarity(current_embedding, reference_embedding)
        
        # 3. Detect spoofing/deepfake
        spoof_probability = self._spoof_adapter.detect_spoof(audio_data)
        
        # 4. Perform speech recognition and phrase matching
        phrase_match = 0.0
        phrase_ok = True
        
        if expected_phrase:
            recognized_text = self._asr_adapter.transcribe(audio_data)
            phrase_match = self._calculate_phrase_similarity(expected_phrase, recognized_text)
            phrase_ok = phrase_match >= 0.7  # Threshold for phrase acceptance
        
        return BiometricAnalysisResult(
            similarity=similarity,
            spoof_probability=spoof_probability,
            phrase_match=phrase_match,
            phrase_ok=phrase_ok,
            speaker_model_id=self._speaker_adapter.get_model_id(),
            antispoof_model_id=self._spoof_adapter.get_model_id(),
            asr_model_id=self._asr_adapter.get_model_id()
        )
    
    def extract_embedding_only(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> VoiceEmbedding:
        """Extract only speaker embedding (for enrollment)."""
        return self._speaker_adapter.extract_embedding(audio_data, audio_format)
    
    def extract_features(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> dict:
        """
        Extract biometric features (embedding and anti-spoofing score).
        """
        # 1. Extract speaker embedding
        embedding = self._speaker_adapter.extract_embedding(audio_data, audio_format)
        
        # 2. Detect spoofing
        spoof_prob = self._spoof_adapter.detect_spoof(audio_data)
        
        # 3. Transcribe audio (ASR)
        transcribed_text = self._asr_adapter.transcribe(audio_data)
        
        return {
            "embedding": embedding,
            "anti_spoofing_score": spoof_prob,
            "transcribed_text": transcribed_text
        }  
    
    def validate_audio_quality(
        self,
        audio_data: bytes,
        audio_format: str
    ) -> dict:
        """Validate audio quality for enrollment/verification."""
        return self._speaker_adapter.validate_audio_quality(audio_data, audio_format)
    
    def _calculate_similarity(
        self,
        embedding1: VoiceEmbedding,
        embedding2: VoiceEmbedding
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        # Normalize embeddings
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(norm1, norm2)
        
        # Clamp to [0, 1] and return
        return max(0.0, min(1.0, similarity))
    
    def _calculate_phrase_similarity(self, expected: str, recognized: str) -> float:
        """Calculate similarity between expected and recognized phrases."""
        # Simple word-based similarity (in production, use more sophisticated NLP)
        expected_words = set(expected.lower().split())
        recognized_words = set(recognized.lower().split())
        
        if not expected_words:
            return 1.0 if not recognized_words else 0.0
        
        intersection = expected_words.intersection(recognized_words)
        union = expected_words.union(recognized_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_engine_info(self) -> dict:
        """Get information about loaded models."""
        return {
            "speaker_model": {
                "id": self._speaker_adapter.get_model_id(),
                "name": self._speaker_adapter.get_model_name(),
                "version": self._speaker_adapter.get_model_version()
            },
            "antispoof_model": {
                "id": self._spoof_adapter.get_model_id(),
                "name": self._spoof_adapter.get_model_name(),
                "version": self._spoof_adapter.get_model_version()
            },
            "asr_model": {
                "id": self._asr_adapter.get_model_id(),
                "name": self._asr_adapter.get_model_name(),
                "version": self._asr_adapter.get_model_version()
            }
        }