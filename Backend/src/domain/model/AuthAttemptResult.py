"""Authentication attempt result using Builder Pattern."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from ...shared.types.common_types import AuthReason, UserId, ClientId, ChallengeId, AudioId


@dataclass
class BiometricScores:
    """Raw biometric analysis scores."""
    similarity: float
    spoof_probability: float
    phrase_match: float
    phrase_ok: bool
    inference_latency_ms: int
    speaker_model_id: Optional[int] = None
    antispoof_model_id: Optional[int] = None
    asr_model_id: Optional[int] = None


@dataclass
class AuthAttemptResult:
    """Final authentication attempt result - built using Builder Pattern."""
    
    # Core identification
    id: UUID
    user_id: Optional[UserId] = None
    client_id: Optional[ClientId] = None
    challenge_id: Optional[ChallengeId] = None
    audio_id: Optional[AudioId] = None
    
    # Decision outcome
    decided: bool = False
    accept: Optional[bool] = None
    reason: Optional[AuthReason] = None
    policy_id: Optional[str] = None
    
    # Performance metrics
    total_latency_ms: Optional[int] = None
    
    # Biometric analysis
    scores: Optional[BiometricScores] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None
    
    def is_successful(self) -> bool:
        """Check if authentication was successful."""
        return self.decided and self.accept is True and self.reason == AuthReason.OK
    
    def is_fraud_attempt(self) -> bool:
        """Check if this looks like a fraud attempt."""
        if not self.scores:
            return False
        
        return (
            self.reason == AuthReason.SPOOF or
            (self.scores.spoof_probability > 0.7) or
            (self.scores.similarity < 0.3 and self.scores.phrase_ok)
        )
    
    def get_risk_indicators(self) -> dict:
        """Get risk indicators for fraud analysis."""
        indicators = {}
        
        if self.scores:
            indicators.update({
                "low_similarity": self.scores.similarity < 0.5,
                "high_spoof_prob": self.scores.spoof_probability > 0.5,
                "phrase_mismatch": not self.scores.phrase_ok,
                "high_latency": self.scores.inference_latency_ms > 3000,
            })
        
        indicators.update({
            "multiple_failures": False,  # Would need context from repository
            "suspicious_timing": False,  # Would need context from repository
        })
        
        return indicators