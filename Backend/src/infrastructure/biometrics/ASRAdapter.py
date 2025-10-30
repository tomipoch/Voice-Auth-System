"""ASR adapter for speech recognition and phrase verification."""

import difflib
from typing import Dict, Any

from ...shared.constants.biometric_constants import DEFAULT_PHRASE_MATCH_THRESHOLD


class ASRAdapter:
    """
    Adapter for Automatic Speech Recognition.
    In production, this would integrate with ASR systems like:
    - Whisper, Wav2Vec2, or commercial ASR APIs
    """
    
    def __init__(self, model_id: int = 3, model_name: str = "whisper_base_v1"):
        self._model_id = model_id
        self._model_name = model_name
        self._model_version = "1.0.0"
        
        # In production, load actual ASR model
        # self._model = whisper.load_model("base")
    
    def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text.
        
        Returns:
            str: Recognized text
        """
        
        # Mock implementation - in production, use actual ASR
        transcribed_text = self._mock_transcription(audio_data)
        
        return transcribed_text
    
    def verify_phrase(self, audio_data: bytes, expected_phrase: str) -> Dict[str, Any]:
        """
        Verify that audio contains the expected phrase.
        
        Returns:
            dict: Verification results with similarity score and match status
        """
        
        # Transcribe audio
        recognized_text = self.transcribe(audio_data)
        
        # Calculate similarity
        similarity = self.calculate_phrase_similarity(expected_phrase, recognized_text)
        
        # Determine if phrase matches
        phrase_matches = similarity >= DEFAULT_PHRASE_MATCH_THRESHOLD
        
        return {
            "recognized_text": recognized_text,
            "expected_phrase": expected_phrase,
            "similarity": similarity,
            "phrase_matches": phrase_matches,
            "confidence": 0.85,  # Mock confidence score
            "details": {
                "word_accuracy": self._calculate_word_accuracy(expected_phrase, recognized_text),
                "length_ratio": len(recognized_text) / max(len(expected_phrase), 1),
                "common_words": self._get_common_words(expected_phrase, recognized_text)
            }
        }
    
    def calculate_phrase_similarity(self, expected: str, recognized: str) -> float:
        """Calculate similarity between expected and recognized phrases."""
        
        # Normalize text
        expected_norm = expected.lower().strip()
        recognized_norm = recognized.lower().strip()
        
        if not expected_norm or not recognized_norm:
            return 0.0
        
        # Use difflib for sequence matching
        similarity = difflib.SequenceMatcher(None, expected_norm, recognized_norm).ratio()
        
        return similarity
    
    def _mock_transcription(self, audio_data: bytes) -> str:
        """
        Mock speech recognition for demonstration.
        In production, replace with actual ASR model.
        """
        
        # Generate pseudo-random but deterministic transcription
        hash_value = hash(audio_data) % 1000
        
        # Mock phrases based on hash
        mock_phrases = [
            "hello world how are you today",
            "the quick brown fox jumps over",
            "voice authentication is working well",
            "please verify my identity now",
            "banking security is very important",
            "machine learning models are powerful",
            "speech recognition technology advances",
            "biometric systems provide security",
            "artificial intelligence helps us",
            "voice prints are unique identifiers"
        ]
        
        base_phrase = mock_phrases[hash_value % len(mock_phrases)]
        
        # Add some "recognition errors" for realism
        if hash_value % 10 < 2:  # 20% chance of errors
            # Simulate transcription errors
            words = base_phrase.split()
            if len(words) > 1:
                # Drop a word occasionally
                words.pop(hash_value % len(words))
            base_phrase = " ".join(words)
        
        return base_phrase.title()
    
    def _calculate_word_accuracy(self, expected: str, recognized: str) -> float:
        """Calculate word-level accuracy."""
        expected_words = set(expected.lower().split())
        recognized_words = set(recognized.lower().split())
        
        if not expected_words:
            return 1.0 if not recognized_words else 0.0
        
        correct_words = expected_words.intersection(recognized_words)
        return len(correct_words) / len(expected_words)
    
    def _get_common_words(self, expected: str, recognized: str) -> list:
        """Get list of common words between expected and recognized."""
        expected_words = set(expected.lower().split())
        recognized_words = set(recognized.lower().split())
        
        return list(expected_words.intersection(recognized_words))
    
    def get_model_id(self) -> int:
        """Get model ID for audit trail."""
        return self._model_id
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    def get_model_version(self) -> str:
        """Get model version."""
        return self._model_version