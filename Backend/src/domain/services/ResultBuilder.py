"""Builder Pattern for constructing AuthAttemptResult step by step."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from ..model.AuthAttemptResult import AuthAttemptResult, BiometricScores
from ...shared.types.common_types import AuthReason, UserId, ClientId, ChallengeId, AudioId


class ResultBuilder:
    """Builder for constructing authentication results step by step."""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> 'ResultBuilder':
        """Reset the builder to construct a new result."""
        self._result = AuthAttemptResult(id=uuid4())
        return self
    
    def with_user(self, user_id: UserId) -> 'ResultBuilder':
        """Set the user ID."""
        self._result.user_id = user_id
        return self
    
    def with_client(self, client_id: ClientId) -> 'ResultBuilder':
        """Set the client ID."""
        self._result.client_id = client_id
        return self
    
    def with_challenge(self, challenge_id: ChallengeId) -> 'ResultBuilder':
        """Set the challenge ID."""
        self._result.challenge_id = challenge_id
        return self
    
    def with_audio(self, audio_id: AudioId) -> 'ResultBuilder':
        """Set the audio ID."""
        self._result.audio_id = audio_id
        return self
    
    def with_policy(self, policy_id: str) -> 'ResultBuilder':
        """Set the policy used for decision."""
        self._result.policy_id = policy_id
        return self
    
    def with_biometric_scores(
        self,
        similarity: float,
        spoof_probability: float,
        phrase_match: float,
        phrase_ok: bool,
        inference_latency_ms: int,
        speaker_model_id: Optional[int] = None,
        antispoof_model_id: Optional[int] = None,
        asr_model_id: Optional[int] = None
    ) -> 'ResultBuilder':
        """Set biometric analysis scores."""
        self._result.scores = BiometricScores(
            similarity=similarity,
            spoof_probability=spoof_probability,
            phrase_match=phrase_match,
            phrase_ok=phrase_ok,
            inference_latency_ms=inference_latency_ms,
            speaker_model_id=speaker_model_id,
            antispoof_model_id=antispoof_model_id,
            asr_model_id=asr_model_id
        )
        return self
    
    def with_total_latency(self, latency_ms: int) -> 'ResultBuilder':
        """Set total request latency."""
        self._result.total_latency_ms = latency_ms
        return self
    
    def accept_with_reason(self, reason: AuthReason = AuthReason.OK) -> 'ResultBuilder':
        """Accept the authentication with a reason."""
        self._result.decided = True
        self._result.accept = True
        self._result.reason = reason
        self._result.decided_at = datetime.now(timezone.utc)
        return self
    
    def reject_with_reason(self, reason: AuthReason) -> 'ResultBuilder':
        """Reject the authentication with a reason."""
        self._result.decided = True
        self._result.accept = False
        self._result.reason = reason
        self._result.decided_at = datetime.now(timezone.utc)
        return self
    
    def build(self) -> AuthAttemptResult:
        """Build and return the final result."""
        # Validate that we have a decision
        if not self._result.decided:
            raise ValueError("Result must be decided before building")
        
        if self._result.accept is None:
            raise ValueError("Result must have an accept/reject decision")
        
        if self._result.reason is None:
            raise ValueError("Result must have a reason")
        
        # Return a copy to prevent further modification
        result = AuthAttemptResult(
            id=self._result.id,
            user_id=self._result.user_id,
            client_id=self._result.client_id,
            challenge_id=self._result.challenge_id,
            audio_id=self._result.audio_id,
            decided=self._result.decided,
            accept=self._result.accept,
            reason=self._result.reason,
            policy_id=self._result.policy_id,
            total_latency_ms=self._result.total_latency_ms,
            scores=self._result.scores,
            created_at=self._result.created_at,
            decided_at=self._result.decided_at
        )
        
        return result