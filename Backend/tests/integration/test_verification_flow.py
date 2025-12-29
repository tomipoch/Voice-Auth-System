"""Integration tests for voice verification flow."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from datetime import datetime, timezone

from src.application.services.VerificationService import VerificationService
from src.application.services.ChallengeService import ChallengeService
from src.application.dtos.ResponseDTOs import VerificationResponseDTO
from src.domain.model.VoiceSignature import VoiceSignature
from src.domain.model.AuthAttemptResult import BiometricScores
from src.domain.model.ThresholdPolicy import PolicyTemplates
from src.shared.types.common_types import (
    VoiceFeatures,
    AuthReason,
    ProcessingResult
)


class TestVerificationFlow:
    """Integration tests for complete verification flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock repositories
        self.voice_signature_repo = Mock()
        self.auth_attempt_repo = Mock()
        self.audit_recorder = Mock()
        
        # Mock biometric engine facade
        self.biometric_engine = Mock()
        
        # Mock decision service
        self.decision_service = Mock()
        
        # Create services
        self.verification_service = VerificationService(
            voice_signature_repo=self.voice_signature_repo,
            auth_attempt_repo=self.auth_attempt_repo,
            biometric_engine=self.biometric_engine,
            decision_service=self.decision_service,
            audit_recorder=self.audit_recorder
        )
        
        self.challenge_service = ChallengeService()
    
    @pytest.mark.asyncio
    async def test_complete_verification_flow_success(self):
        """Test complete successful verification flow."""
        # 1. Generate challenge
        challenge = self.challenge_service.generate_challenge()
        assert challenge is not None
        assert len(challenge.phrase) > 0
        assert challenge.expires_at > datetime.now(timezone.utc)
        
        # 2. Mock existing voice signature
        user_id = "user123"
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        voice_signature = VoiceSignature(
            user_id=user_id,
            features=voice_features,
            created_at=datetime.now(timezone.utc)
        )
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=voice_signature
        )
        
        # 3. Mock biometric processing
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        biometric_scores = BiometricScores(
            similarity=0.92,
            spoof_probability=0.1,
            phrase_match=0.88,
            phrase_ok=True,
            inference_latency_ms=1500
        )
        self.biometric_engine.process_verification_audio = AsyncMock(
            return_value=biometric_scores
        )
        
        # 4. Mock decision service
        self.decision_service.decide = Mock(
            return_value=(True, AuthReason.OK)
        )
        
        # 5. Mock repository saves
        self.auth_attempt_repo.save = AsyncMock()
        self.audit_recorder.record_attempt = AsyncMock()
        
        # 6. Execute verification
        policy = PolicyTemplates.get_standard()
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase=challenge.phrase,
            policy=policy
        )
        
        # 7. Assertions
        assert isinstance(result, VerificationResponseDTO)
        assert result.success is True
        assert result.reason == AuthReason.OK
        assert result.confidence_score == pytest.approx(0.92)
        assert result.processing_time_ms == pytest.approx(1500)
        
        # 8. Verify service interactions
        self.voice_signature_repo.get_by_user_id.assert_called_once_with(user_id)
        self.biometric_engine.process_verification_audio.assert_called_once_with(
            audio_data, user_id, voice_features, challenge.phrase
        )
        self.decision_service.decide.assert_called_once_with(
            biometric_scores, policy
        )
        self.auth_attempt_repo.save.assert_called_once()
        self.audit_recorder.record_attempt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verification_flow_user_not_enrolled(self):
        """Test verification flow when user is not enrolled."""
        user_id = "non_existent_user"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock no voice signature found
        self.voice_signature_repo.get_by_user_id = AsyncMock(return_value=None)
        
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase="test phrase",
            policy=PolicyTemplates.get_standard()
        )
        
        assert result.success is False
        assert result.reason == AuthReason.NOT_ENROLLED
        
        # Should not process biometrics for non-enrolled user
        self.biometric_engine.process_verification_audio.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verification_flow_spoofing_detected(self):
        """Test verification flow with spoofing detection."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing user
        voice_signature = Mock()
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=voice_signature
        )
        
        # Mock spoofing detection
        biometric_scores = BiometricScores(
            similarity=0.85,
            spoof_probability=0.9,  # High spoof probability
            phrase_match=0.88,
            phrase_ok=True,
            inference_latency_ms=1200
        )
        self.biometric_engine.process_verification_audio = AsyncMock(
            return_value=biometric_scores
        )
        
        # Mock decision service rejection
        self.decision_service.decide = Mock(
            return_value=(False, AuthReason.SPOOF)
        )
        
        # Mock repository saves
        self.auth_attempt_repo.save = AsyncMock()
        self.audit_recorder.record_attempt = AsyncMock()
        
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase="test phrase",
            policy=PolicyTemplates.get_standard()
        )
        
        assert result.success is False
        assert result.reason == AuthReason.SPOOF
        
        # Should still record the attempt for security analysis
        self.auth_attempt_repo.save.assert_called_once()
        self.audit_recorder.record_attempt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verification_flow_low_similarity(self):
        """Test verification flow with low similarity score."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing user
        voice_signature = Mock()
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=voice_signature
        )
        
        # Mock low similarity
        biometric_scores = BiometricScores(
            similarity=0.65,  # Below threshold
            spoof_probability=0.1,
            phrase_match=0.88,
            phrase_ok=True,
            inference_latency_ms=1300
        )
        self.biometric_engine.process_verification_audio = AsyncMock(
            return_value=biometric_scores
        )
        
        # Mock decision service rejection
        self.decision_service.decide = Mock(
            return_value=(False, AuthReason.LOW_SIMILARITY)
        )
        
        # Mock repository saves
        self.auth_attempt_repo.save = AsyncMock()
        self.audit_recorder.record_attempt = AsyncMock()
        
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase="test phrase",
            policy=PolicyTemplates.get_standard()
        )
        
        assert result.success is False
        assert result.reason == AuthReason.LOW_SIMILARITY
        assert result.confidence_score == pytest.approx(0.65)
    
    @pytest.mark.asyncio
    async def test_verification_flow_phrase_mismatch(self):
        """Test verification flow with phrase mismatch."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing user
        voice_signature = Mock()
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=voice_signature
        )
        
        # Mock phrase mismatch
        biometric_scores = BiometricScores(
            similarity=0.90,
            spoof_probability=0.1,
            phrase_match=0.45,  # Low phrase match
            phrase_ok=False,    # Phrase not recognized correctly
            inference_latency_ms=1400
        )
        self.biometric_engine.process_verification_audio = AsyncMock(
            return_value=biometric_scores
        )
        
        # Mock decision service rejection
        self.decision_service.decide = Mock(
            return_value=(False, AuthReason.PHRASE_MISMATCH)
        )
        
        # Mock repository saves
        self.auth_attempt_repo.save = AsyncMock()
        self.audit_recorder.record_attempt = AsyncMock()
        
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase="expected phrase",
            policy=PolicyTemplates.get_standard()
        )
        
        assert result.success is False
        assert result.reason == AuthReason.PHRASE_MISMATCH
    
    @pytest.mark.asyncio
    async def test_verification_flow_with_banking_policy(self):
        """Test verification flow with stricter banking policy."""
        user_id = "user123"
        audio_data = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock existing user
        voice_signature = Mock()
        self.voice_signature_repo.get_by_user_id = AsyncMock(
            return_value=voice_signature
        )
        
        # Mock borderline scores that might pass standard but fail banking
        biometric_scores = BiometricScores(
            similarity=0.86,  # Might be borderline for banking
            spoof_probability=0.15,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=1100
        )
        self.biometric_engine.process_verification_audio = AsyncMock(
            return_value=biometric_scores
        )
        
        # Mock decision service with banking policy
        self.decision_service.decide = Mock(
            return_value=(False, AuthReason.LOW_SIMILARITY)
        )
        
        # Mock repository saves
        self.auth_attempt_repo.save = AsyncMock()
        self.audit_recorder.record_attempt = AsyncMock()
        
        # Use banking policy
        banking_policy = PolicyTemplates.get_bank_strict()
        result = await self.verification_service.verify_voice(
            user_id=user_id,
            audio_data=audio_data,
            challenge_phrase="test phrase",
            policy=banking_policy
        )
        
        assert result.success is False
        assert result.reason == AuthReason.LOW_SIMILARITY
        
        # Verify banking policy was used
        self.decision_service.decide.assert_called_once_with(
            biometric_scores, banking_policy
        )