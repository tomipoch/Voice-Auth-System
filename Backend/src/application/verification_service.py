"""Verification service - main business logic for voice authentication."""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .dto.VerificationRequestDTO import VerificationRequestDTO
from .dto.VerificationResponseDTO import VerificationResponseDTO
from .policies.PolicySelector import PolicySelector
from ..domain.services.DecisionService import DecisionService
from ..domain.services.ResultBuilder import ResultBuilder
from ..domain.repositories.VoiceTemplateRepositoryPort import VoiceTemplateRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.ChallengeRepositoryPort import ChallengeRepositoryPort
from ..domain.repositories.AuthAttemptRepositoryPort import AuthAttemptRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import AuthReason, AuditAction


class VerificationService:
    """
    Main verification service that orchestrates the complete authentication flow.
    Uses Builder Pattern for result construction and Strategy Pattern for decisions.
    """
    
    def __init__(
        self,
        voice_repo: VoiceTemplateRepositoryPort,
        user_repo: UserRepositoryPort,
        challenge_repo: ChallengeRepositoryPort,
        auth_repo: AuthAttemptRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        policy_selector: PolicySelector,
        decision_service: DecisionService,
        biometric_engine  # VoiceBiometricEngineFacade - will define in infrastructure
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._challenge_repo = challenge_repo
        self._auth_repo = auth_repo
        self._audit_repo = audit_repo
        self._policy_selector = policy_selector
        self._decision_service = decision_service
        self._biometric_engine = biometric_engine
    
    async def verify_voice(
        self,
        request: VerificationRequestDTO,
        include_scores_in_response: bool = False
    ) -> VerificationResponseDTO:
        """
        Main verification method that orchestrates the complete flow.
        
        This method implements the core business logic described in the proposal,
        using Builder Pattern for result construction and Facade Pattern for
        biometric processing.
        """
        start_time = time.time()
        builder = ResultBuilder().with_client(request.client_id)
        
        try:
            # Validate request and user
            early_result = await self._validate_request_and_user(request, builder, start_time)
            if early_result:
                return early_result
            
            user_id = await self._resolve_user(request)
            builder.with_user(user_id)
            
            # Validate challenge
            challenge_result = await self._validate_and_process_challenge(request, user_id, builder, start_time)
            if challenge_result:
                return challenge_result
                
            # Get voiceprint and perform verification
            verification_result = await self._perform_voice_verification(
                request, user_id, builder, start_time, include_scores_in_response
            )
            return verification_result
            
        except Exception as e:
            return await self._handle_verification_error(e, request, builder, start_time, include_scores_in_response)
    
    async def _validate_request_and_user(
        self, 
        request: VerificationRequestDTO, 
        builder: ResultBuilder, 
        start_time: float
    ) -> Optional[VerificationResponseDTO]:
        """Validate request and check if user exists."""
        # Validate request
        validation_errors = request.validate()
        if validation_errors:
            result = (builder
                     .reject_with_reason(AuthReason.ERROR)
                     .with_total_latency(int((time.time() - start_time) * 1000))
                     .build())
            await self._auth_repo.save_attempt(result)
            return VerificationResponseDTO.from_auth_result(result, False)
        
        # Check user exists
        user_id = await self._resolve_user(request)
        if not user_id:
            result = (builder
                     .reject_with_reason(AuthReason.ERROR)
                     .with_total_latency(int((time.time() - start_time) * 1000))
                     .build())
            await self._auth_repo.save_attempt(result)
            return VerificationResponseDTO.from_auth_result(result, False)
        
        return None
    
    async def _validate_and_process_challenge(
        self,
        request: VerificationRequestDTO,
        user_id: str,
        builder: ResultBuilder,
        start_time: float
    ) -> Optional[VerificationResponseDTO]:
        """Validate challenge and return error if invalid."""
        challenge_valid, challenge_reason, challenge_id = await self._validate_challenge(request, user_id)
        if challenge_id:
            builder.with_challenge(challenge_id)
        
        if not challenge_valid:
            reason = AuthReason.EXPIRED_CHALLENGE if "expired" in challenge_reason else AuthReason.ERROR
            result = (builder
                     .reject_with_reason(reason)
                     .with_total_latency(int((time.time() - start_time) * 1000))
                     .build())
            await self._auth_repo.save_attempt(result)
            return VerificationResponseDTO.from_auth_result(result, False)
        
        return None
    
    async def _perform_voice_verification(
        self,
        request: VerificationRequestDTO,
        user_id: str,
        builder: ResultBuilder,
        start_time: float,
        include_scores_in_response: bool
    ) -> VerificationResponseDTO:
        """Perform the actual voice verification process."""
        # Get user's voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if not voiceprint:
            result = (builder
                     .reject_with_reason(AuthReason.ERROR)
                     .with_total_latency(int((time.time() - start_time) * 1000))
                     .build())
            await self._auth_repo.save_attempt(result)
            return VerificationResponseDTO.from_auth_result(result, include_scores_in_response)
        
        # Store audio if policy allows
        await self._handle_audio_storage(request, user_id, builder)
        
        # Select policy and analyze voice
        context = self._build_context(request, user_id)
        policy = self._policy_selector.select_policy(
            user_id=user_id,
            client_id=request.client_id,
            context=context
        )
        builder.with_policy(policy.name)
        
        # Perform biometric analysis
        scores, inference_time = await self._analyze_voice_biometrics(request, voiceprint)
        builder.with_biometric_scores(
            similarity=scores.similarity,
            spoof_probability=scores.spoof_probability,
            phrase_match=scores.phrase_match,
            phrase_ok=scores.phrase_ok,
            inference_latency_ms=inference_time,
            speaker_model_id=scores.speaker_model_id,
            antispoof_model_id=scores.antispoof_model_id,
            asr_model_id=scores.asr_model_id
        )
        
        # Make decision and build result
        return await self._make_decision_and_finalize(
            request, user_id, builder, scores, policy, context, start_time, include_scores_in_response
        )
    
    async def _handle_audio_storage(self, request: VerificationRequestDTO, user_id: str, builder: ResultBuilder) -> None:
        """Handle audio storage if user policy allows."""
        user_policy = await self._user_repo.get_user_policy(user_id)
        if user_policy and user_policy.get('keep_audio', False):
            audio_id = await self._auth_repo.store_audio_blob(
                request.audio_data, 
                request.audio_format
            )
            builder.with_audio(audio_id)
    
    async def _analyze_voice_biometrics(self, request: VerificationRequestDTO, voiceprint) -> tuple:
        """Perform biometric analysis and return scores with timing."""
        inference_start = time.time()
        scores = await self._biometric_engine.analyze_voice(
            audio_data=request.audio_data,
            audio_format=request.audio_format,
            reference_embedding=voiceprint.embedding,
            expected_phrase=self._get_expected_phrase(request)
        )
        inference_time = int((time.time() - inference_start) * 1000)
        return scores, inference_time
    
    async def _make_decision_and_finalize(
        self,
        request: VerificationRequestDTO,
        user_id: str,
        builder: ResultBuilder,
        scores,
        policy,
        context: Dict[str, Any],
        start_time: float,
        include_scores_in_response: bool
    ) -> VerificationResponseDTO:
        """Make final decision and complete verification process."""
        # Make decision using Strategy Pattern
        accept, reason = self._decision_service.decide(
            scores=scores,
            policy=policy,
            context=context
        )
        
        # Build final result
        total_latency = int((time.time() - start_time) * 1000)
        if accept:
            result = (builder
                     .accept_with_reason(reason)
                     .with_total_latency(total_latency)
                     .build())
        else:
            result = (builder
                     .reject_with_reason(reason)
                     .with_total_latency(total_latency)
                     .build())
        
        # Save attempt and mark challenge as used
        await self._auth_repo.save_attempt(result)
        challenge_id = getattr(builder, '_challenge_id', None)
        if challenge_id and accept:
            await self._challenge_repo.mark_challenge_used(challenge_id)
        
        # Log the attempt
        await self._audit_repo.log_event(
            actor=f"client:{request.client_id}" if request.client_id else "unknown",
            action=AuditAction.VERIFY,
            entity_type="auth_attempt",
            entity_id=str(result.id),
            success=result.is_successful(),
            metadata={
                "user_id": str(user_id),
                "similarity": scores.similarity,
                "spoof_prob": scores.spoof_probability,
                "policy": policy.name,
                "total_latency_ms": total_latency
            }
        )
        
        # Check for suspicious activity
        await self._check_suspicious_activity(result, context)
        
        return VerificationResponseDTO.from_auth_result(result, include_scores_in_response)
    
    async def _handle_verification_error(
        self,
        error: Exception,
        request: VerificationRequestDTO,
        builder: ResultBuilder,
        start_time: float,
        include_scores_in_response: bool
    ) -> VerificationResponseDTO:
        """Handle unexpected errors during verification."""
        total_latency = int((time.time() - start_time) * 1000)
        result = (builder
                 .reject_with_reason(AuthReason.ERROR)
                 .with_total_latency(total_latency)
                 .build())
        
        await self._auth_repo.save_attempt(result)
        
        await self._audit_repo.log_event(
            actor=f"client:{request.client_id}" if request.client_id else "unknown",
            action=AuditAction.VERIFY,
            entity_type="auth_attempt",
            entity_id=str(result.id),
            success=False,
            error_message=str(error)
        )
        
        return VerificationResponseDTO.from_auth_result(result, include_scores_in_response)
    
    async def _resolve_user(self, request: VerificationRequestDTO) -> Optional[str]:
        """Resolve user ID from request."""
        if request.user_id:
            if await self._user_repo.user_exists(request.user_id):
                return request.user_id
        
        if request.external_user_ref:
            user = await self._user_repo.get_user_by_external_ref(request.external_user_ref)
            if user:
                return user['id']
        
        return None
    
    async def _validate_challenge(
        self, 
        request: VerificationRequestDTO, 
        user_id: str
    ) -> tuple[bool, str, Optional[str]]:
        """Validate challenge from request."""
        if request.challenge_id:
            challenge = await self._challenge_repo.get_challenge(request.challenge_id)
            if not challenge:
                return False, "Challenge not found", None
            
            if challenge.get('user_id') != user_id:
                return False, "Challenge does not belong to user", None
            
            if challenge.get('used_at'):
                return False, "Challenge already used", None
            
            if challenge.get('expires_at') and datetime.now() > challenge['expires_at']:
                return False, "Challenge expired", None
            
            return True, "Valid", request.challenge_id
        
        # If no challenge_id but expected_phrase, that's also valid for some clients
        if request.expected_phrase:
            return True, "Valid phrase", None
        
        return False, "No challenge or phrase provided", None
    
    def _get_expected_phrase(self, request: VerificationRequestDTO) -> Optional[str]:
        """Get the expected phrase for verification."""
        if request.expected_phrase:
            return request.expected_phrase
        
        # In real implementation, would fetch phrase from challenge
        return None
    
    def _build_context(self, request: VerificationRequestDTO, user_id: str) -> Dict[str, Any]:
        """Build context for policy selection and decision making."""
        context = request.context or {}
        
        # Add time-based context
        now = datetime.now()
        context.update({
            "hour_of_day": now.hour,
            "day_of_week": now.weekday() + 1,
            "timestamp": now.isoformat(),
            "user_id": str(user_id)
        })
        
        return context
    
    async def _check_suspicious_activity(self, result, context: Dict[str, Any]) -> None:
        """Check for suspicious activity patterns."""
        if result.is_fraud_attempt():
            # In a real implementation, this would trigger alerts
            # to the fraud detection system
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.VERIFY,
                entity_type="fraud_alert",
                entity_id=str(result.id),
                metadata={
                    "risk_indicators": result.get_risk_indicators(),
                    "severity": "high" if result.reason == AuthReason.SPOOF else "medium"
                }
            )