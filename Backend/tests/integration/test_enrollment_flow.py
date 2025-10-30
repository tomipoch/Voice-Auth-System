"""Integration tests for enrollment flow."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import numpy as np
from datetime import datetime, timezone

from ...src.application.services.EnrollmentService import EnrollmentService
from ...src.application.dtos.ResponseDTOs import EnrollmentResponseDTO
from ...src.shared.types.common_types import (
    VoiceFeatures,
    ProcessingResult,
    AuthReason
)


class TestEnrollmentFlow:
    """Integration tests for complete enrollment flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock repositories
        self.voice_signature_repo = Mock()
        self.audit_recorder = Mock()
        
        # Mock biometric engine facade
        self.biometric_engine = Mock()
        
        # Create enrollment service
        self.enrollment_service = EnrollmentService(
            voice_signature_repo=self.voice_signature_repo,
            biometric_engine=self.biometric_engine,
            audit_recorder=self.audit_recorder
        )
    
    @pytest.mark.asyncio
    async def test_complete_enrollment_flow_success(self):
        """Test complete successful enrollment flow."""
        user_id = "new_user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # 1. Mock successful biometric processing
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        processing_result = ProcessingResult(
            success=True,
            features=voice_features,
            spoof_probability=0.1,
            processing_time_ms=1200,
            error_reason=None
        )
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            return_value=processing_result
        )
        
        # 2. Mock no existing enrollment
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        # 3. Mock successful save
        self.voice_signature_repo.save = AsyncMock()
        self.audit_recorder.record_enrollment = AsyncMock()
        
        # 4. Execute enrollment
        result = await self.enrollment_service.enroll_user(user_id, audio_data)
        
        # 5. Assertions
        assert isinstance(result, EnrollmentResponseDTO)
        assert result.success is True
        assert result.user_id == user_id
        assert result.processing_time_ms == pytest.approx(1200)
        assert result.spoof_probability == pytest.approx(0.1)
        
        # 6. Verify service interactions
        self.voice_signature_repo.get_by_user_id.assert_called_once_with(user_id)
        self.biometric_engine.process_enrollment_audio.assert_called_once_with(
            audio_data, user_id
        )
        self.voice_signature_repo.save.assert_called_once()
        self.audit_recorder.record_enrollment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_user_already_enrolled(self):
        """Test enrollment flow when user is already enrolled."""
        user_id = "existing_user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing voice signature
        existing_signature = Mock()
        existing_signature.user_id = user_id
        existing_signature.created_at = datetime.now(timezone.utc)
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=existing_signature
        )
        
        result = await self.enrollment_service.enroll_user(user_id, audio_data)
        
        assert result.success is False
        assert result.error_message == "User already enrolled"
        
        # Should not process biometrics for already enrolled user
        self.biometric_engine.process_enrollment_audio.assert_not_called()
        self.voice_signature_repo.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_spoofing_detected(self):
        """Test enrollment flow with spoofing detection."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock no existing enrollment
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        # Mock spoofing detection
        processing_result = ProcessingResult(
            success=False,
            features=None,
            spoof_probability=0.9,
            processing_time_ms=800,
            error_reason=AuthReason.SPOOF
        )
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            return_value=processing_result
        )
        
        # Mock audit recording
        self.audit_recorder.record_enrollment = AsyncMock()
        
        result = await self.enrollment_service.enroll_user(user_id, audio_data)
        
        assert result.success is False
        assert result.error_message == "Spoofed audio detected"
        assert result.spoof_probability == pytest.approx(0.9)
        
        # Should not save enrollment for spoofed audio
        self.voice_signature_repo.save.assert_not_called()
        
        # Should still record the failed attempt for security analysis
        self.audit_recorder.record_enrollment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_biometric_processing_failure(self):
        """Test enrollment flow with biometric processing failure."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock no existing enrollment
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        # Mock biometric processing failure
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            side_effect=Exception("Audio processing failed")
        )
        
        # Mock audit recording
        self.audit_recorder.record_enrollment = AsyncMock()
        
        with pytest.raises(Exception, match="Audio processing failed"):
            await self.enrollment_service.enroll_user(user_id, audio_data)
        
        # Should not save enrollment when processing fails
        self.voice_signature_repo.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_database_save_failure(self):
        """Test enrollment flow with database save failure."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock no existing enrollment
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        # Mock successful biometric processing
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        processing_result = ProcessingResult(
            success=True,
            features=voice_features,
            spoof_probability=0.1,
            processing_time_ms=1200,
            error_reason=None
        )
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            return_value=processing_result
        )
        
        # Mock database save failure
        self.voice_signature_repo.save = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        with pytest.raises(Exception, match="Database connection failed"):
            await self.enrollment_service.enroll_user(user_id, audio_data)
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_re_enrollment(self):
        """Test re-enrollment flow (overwriting existing enrollment)."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing voice signature
        existing_signature = Mock()
        existing_signature.user_id = user_id
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=existing_signature
        )
        
        # Mock successful biometric processing
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        processing_result = ProcessingResult(
            success=True,
            features=voice_features,
            spoof_probability=0.1,
            processing_time_ms=1300,
            error_reason=None
        )
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            return_value=processing_result
        )
        
        # Mock successful save and audit
        self.voice_signature_repo.save = AsyncMock()
        self.audit_recorder.record_enrollment = AsyncMock()
        
        # Execute re-enrollment (force flag)
        result = await self.enrollment_service.enroll_user(
            user_id, audio_data, force_re_enrollment=True
        )
        
        assert result.success is True
        assert result.user_id == user_id
        
        # Should process and save even for existing user when forced
        self.biometric_engine.process_enrollment_audio.assert_called_once()
        self.voice_signature_repo.save.assert_called_once()
        self.audit_recorder.record_enrollment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enrollment_flow_with_multiple_audio_samples(self):
        """Test enrollment flow with multiple audio samples for better accuracy."""
        user_id = "user123"
        audio_samples = [
            np.array([0.1, 0.2, 0.3, 0.4]),
            np.array([0.2, 0.3, 0.4, 0.5]),
            np.array([0.3, 0.4, 0.5, 0.6])
        ]
        
        # Mock no existing enrollment
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        # Mock successful processing for each sample
        voice_features_list = []
        for i, audio in enumerate(audio_samples):
            features = VoiceFeatures(
                mfcc_features=np.array([[i+1, i+2, i+3], [i+4, i+5, i+6]]),
                pitch_features=np.array([100+i*10, 200+i*10]),
                spectral_features=np.array([0.5+i*0.1, 0.6+i*0.1, 0.7+i*0.1])
            )
            voice_features_list.append(features)
        
        processing_results = [
            ProcessingResult(
                success=True,
                features=features,
                spoof_probability=0.1,
                processing_time_ms=1200 + i*100,
                error_reason=None
            )
            for i, features in enumerate(voice_features_list)
        ]
        
        self.biometric_engine.process_enrollment_audio = AsyncMock(
            side_effect=processing_results
        )
        
        # Mock repository operations
        self.voice_signature_repo.save = AsyncMock()
        self.audit_recorder.record_enrollment = AsyncMock()
        
        # Execute enrollment with multiple samples
        result = await self.enrollment_service.enroll_user_multiple_samples(
            user_id, audio_samples
        )
        
        assert result.success is True
        assert result.user_id == user_id
        
        # Should process all samples
        assert self.biometric_engine.process_enrollment_audio.call_count == 3
        
        # Should save consolidated features
        self.voice_signature_repo.save.assert_called_once()
        self.audit_recorder.record_enrollment.assert_called_once()