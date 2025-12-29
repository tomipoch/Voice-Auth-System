"""Unit tests for Facade Pattern in biometric engine."""

import pytest
from unittest.mock import Mock, AsyncMock
import numpy as np

from src.infrastructure.facades.VoiceBiometricEngineFacade import (
    VoiceBiometricEngineFacade
)
from src.domain.model.AuthAttemptResult import BiometricScores
from src.shared.types.common_types import (
    ProcessingResult,
    VoiceFeatures,
    AuthReason
)


class TestVoiceBiometricEngineFacade:
    """Test suite for voice biometric engine facade."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock adapters
        self.speaker_adapter = Mock()
        self.spoofing_adapter = Mock()
        self.asr_adapter = Mock()
        
        # Create facade with mocked adapters
        self.facade = VoiceBiometricEngineFacade(
            speaker_recognition_adapter=self.speaker_adapter,
            anti_spoofing_adapter=self.spoofing_adapter,
            asr_adapter=self.asr_adapter
        )
    
    @pytest.mark.asyncio
    async def test_process_enrollment_audio_success(self):
        """Test successful enrollment audio processing."""
        # Mock audio data
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        
        # Mock adapter responses
        features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        self.speaker_adapter.extract_features = AsyncMock(return_value=features)
        
        spoofing_score = 0.1  # Low spoof probability
        self.spoofing_adapter.detect_spoofing = AsyncMock(return_value=spoofing_score)
        
        # Execute
        result = await self.facade.process_enrollment_audio(audio_data, user_id)
        
        # Assertions
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.features == features
        assert result.spoof_probability == pytest.approx(spoofing_score)
        
        # Verify adapter calls
        self.speaker_adapter.extract_features.assert_called_once_with(audio_data)
        self.spoofing_adapter.detect_spoofing.assert_called_once_with(audio_data)
    
    @pytest.mark.asyncio
    async def test_process_enrollment_audio_spoofing_detected(self):
        """Test enrollment audio processing with spoofing detected."""
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        
        # Mock high spoof probability
        spoofing_score = 0.9
        self.spoofing_adapter.detect_spoofing = AsyncMock(return_value=spoofing_score)
        
        result = await self.facade.process_enrollment_audio(audio_data, user_id)
        
        assert result.success is False
        assert result.error_reason == AuthReason.SPOOF
        assert result.spoof_probability == pytest.approx(spoofing_score)
    
    @pytest.mark.asyncio
    async def test_process_verification_audio_success(self):
        """Test successful verification audio processing."""
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        expected_phrase = "hello world"
        stored_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        
        # Mock adapter responses
        current_features = VoiceFeatures(
            mfcc_features=np.array([[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]),
            pitch_features=np.array([105, 205]),
            spectral_features=np.array([0.52, 0.62, 0.72])
        )
        self.speaker_adapter.extract_features = AsyncMock(return_value=current_features)
        
        similarity_score = 0.92
        self.speaker_adapter.compare_features = AsyncMock(return_value=similarity_score)
        
        spoofing_score = 0.15
        self.spoofing_adapter.detect_spoofing = AsyncMock(return_value=spoofing_score)
        
        phrase_match_score = 0.88
        recognized_phrase = "hello world"
        self.asr_adapter.recognize_speech = AsyncMock(
            return_value=(recognized_phrase, phrase_match_score)
        )
        
        # Execute
        scores = await self.facade.process_verification_audio(
            audio_data, user_id, stored_features, expected_phrase
        )
        
        # Assertions
        assert isinstance(scores, BiometricScores)
        assert scores.similarity == pytest.approx(similarity_score)
        assert scores.spoof_probability == pytest.approx(spoofing_score)
        assert scores.phrase_match == pytest.approx(phrase_match_score)
        assert scores.phrase_ok is True
        assert scores.inference_latency_ms > 0
        
        # Verify adapter calls
        self.speaker_adapter.extract_features.assert_called_once_with(audio_data)
        self.speaker_adapter.compare_features.assert_called_once_with(
            stored_features, current_features
        )
        self.spoofing_adapter.detect_spoofing.assert_called_once_with(audio_data)
        self.asr_adapter.recognize_speech.assert_called_once_with(
            audio_data, expected_phrase
        )
    
    @pytest.mark.asyncio
    async def test_process_verification_audio_phrase_mismatch(self):
        """Test verification with phrase mismatch."""
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        expected_phrase = "hello world"
        stored_features = Mock()
        
        # Mock phrase recognition with low match score
        self.asr_adapter.recognize_speech = AsyncMock(
            return_value=("goodbye world", 0.3)
        )
        
        # Mock other adapters
        self.speaker_adapter.extract_features = AsyncMock(return_value=Mock())
        self.speaker_adapter.compare_features = AsyncMock(return_value=0.9)
        self.spoofing_adapter.detect_spoofing = AsyncMock(return_value=0.1)
        
        scores = await self.facade.process_verification_audio(
            audio_data, user_id, stored_features, expected_phrase
        )
        
        assert scores.phrase_ok is False
        assert scores.phrase_match == pytest.approx(0.3)
    
    @pytest.mark.asyncio
    async def test_process_verification_audio_adapter_failure(self):
        """Test verification when adapter fails."""
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        expected_phrase = "hello world"
        stored_features = Mock()
        
        # Mock adapter failure
        self.speaker_adapter.extract_features = AsyncMock(
            side_effect=Exception("Feature extraction failed")
        )
        
        with pytest.raises(Exception, match="Feature extraction failed"):
            await self.facade.process_verification_audio(
                audio_data, user_id, stored_features, expected_phrase
            )
    
    def test_facade_initialization(self):
        """Test facade proper initialization."""
        facade = VoiceBiometricEngineFacade(
            speaker_recognition_adapter=self.speaker_adapter,
            anti_spoofing_adapter=self.spoofing_adapter,
            asr_adapter=self.asr_adapter
        )
        
        assert facade.speaker_recognition_adapter == self.speaker_adapter
        assert facade.anti_spoofing_adapter == self.spoofing_adapter
        assert facade.asr_adapter == self.asr_adapter
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self):
        """Test that facade tracks performance metrics."""
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        user_id = "user123"
        
        # Mock delayed responses to test timing
        import asyncio
        
        async def delayed_extract_features(audio):
            await asyncio.sleep(0.1)  # 100ms delay
            return Mock()
        
        self.speaker_adapter.extract_features = delayed_extract_features
        self.spoofing_adapter.detect_spoofing = AsyncMock(return_value=0.1)
        
        result = await self.facade.process_enrollment_audio(audio_data, user_id)
        
        # Verify timing was captured (should be at least 100ms)
        assert result.processing_time_ms >= 100