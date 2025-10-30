"""Data Transfer Objects for verification responses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from ...shared.types.common_types import AuthReason


@dataclass
class BiometricScoresDTO:
    """DTO for biometric analysis scores."""
    similarity: float
    spoof_probability: float
    phrase_match: float
    phrase_ok: bool
    inference_latency_ms: int


@dataclass
class VerificationResponseDTO:
    """Response DTO for voice verification."""
    
    # Core result
    request_id: UUID
    success: bool
    reason: AuthReason
    
    # Performance metrics
    total_latency_ms: int
    processed_at: datetime
    
    # Biometric details (optional, based on client permissions)
    scores: Optional[BiometricScoresDTO] = None
    
    # Policy information
    policy_used: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_auth_result(cls, auth_result, include_scores: bool = False):
        """Create response DTO from domain AuthAttemptResult."""
        scores_dto = None
        if include_scores and auth_result.scores:
            scores_dto = BiometricScoresDTO(
                similarity=auth_result.scores.similarity,
                spoof_probability=auth_result.scores.spoof_probability,
                phrase_match=auth_result.scores.phrase_match,
                phrase_ok=auth_result.scores.phrase_ok,
                inference_latency_ms=auth_result.scores.inference_latency_ms
            )
        
        return cls(
            request_id=auth_result.id,
            success=auth_result.is_successful(),
            reason=auth_result.reason,
            total_latency_ms=auth_result.total_latency_ms or 0,
            processed_at=auth_result.decided_at or auth_result.created_at,
            scores=scores_dto,
            policy_used=auth_result.policy_id
        )