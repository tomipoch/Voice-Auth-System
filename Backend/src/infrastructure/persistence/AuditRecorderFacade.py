"""Facade for audit recording - implements Facade Pattern."""

from typing import Dict, Any, Optional
from uuid import UUID

from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ...shared.types.common_types import AuditAction


class AuditRecorderFacade:
    """
    Facade that simplifies audit recording across the system.
    Provides a unified interface for logging different types of events.
    """
    
    def __init__(self, audit_repo: AuditLogRepositoryPort):
        self._audit_repo = audit_repo
    
    async def log_enrollment_started(self, user_id: UUID, actor: str = "system") -> None:
        """Log enrollment process started."""
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.ENROLL,
            entity_type="enrollment",
            entity_id=str(user_id),
            metadata={"stage": "started"}
        )
    
    async def log_enrollment_completed(
        self, 
        user_id: UUID, 
        voiceprint_id: UUID, 
        sample_count: int,
        quality_score: float,
        actor: str = "system"
    ) -> None:
        """Log enrollment completion."""
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.ENROLL,
            entity_type="voiceprint",
            entity_id=str(voiceprint_id),
            metadata={
                "user_id": str(user_id),
                "sample_count": sample_count,
                "quality_score": quality_score
            }
        )
    
    async def log_verification_attempt(
        self,
        attempt_id: UUID,
        user_id: UUID,
        client_id: Optional[UUID],
        success: bool,
        reason: str,
        similarity_score: Optional[float] = None,
        spoof_probability: Optional[float] = None,
        total_latency_ms: Optional[int] = None,
        policy_used: Optional[str] = None
    ) -> None:
        """Log verification attempt."""
        actor = f"client:{client_id}" if client_id else "unknown"
        
        metadata = {
            "user_id": str(user_id),
            "reason": reason,
            "success": success
        }
        
        if similarity_score is not None:
            metadata["similarity_score"] = similarity_score
        if spoof_probability is not None:
            metadata["spoof_probability"] = spoof_probability
        if total_latency_ms is not None:
            metadata["total_latency_ms"] = total_latency_ms
        if policy_used:
            metadata["policy_used"] = policy_used
        
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.VERIFY,
            entity_type="auth_attempt",
            entity_id=str(attempt_id),
            success=success,
            metadata=metadata
        )
    
    async def log_challenge_created(
        self,
        challenge_id: UUID,
        user_id: UUID,
        phrase_length: int,
        expires_at: str
    ) -> None:
        """Log challenge creation."""
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.CREATE_CHALLENGE,
            entity_type="challenge",
            entity_id=str(challenge_id),
            metadata={
                "user_id": str(user_id),
                "phrase_length": phrase_length,
                "expires_at": expires_at
            }
        )
    
    async def log_suspicious_activity(
        self,
        attempt_id: UUID,
        user_id: Optional[UUID],
        client_id: Optional[UUID],
        risk_indicators: Dict[str, bool],
        severity: str = "medium"
    ) -> None:
        """Log suspicious activity detection."""
        actor = f"client:{client_id}" if client_id else "unknown"
        
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.VERIFY,
            entity_type="fraud_alert",
            entity_id=str(attempt_id),
            metadata={
                "user_id": str(user_id) if user_id else None,
                "risk_indicators": risk_indicators,
                "severity": severity
            }
        )
    
    async def log_user_deletion(self, user_id: UUID, actor: str) -> None:
        """Log user deletion (GDPR compliance)."""
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.DELETE_USER,
            entity_type="user",
            entity_id=str(user_id),
            metadata={"reason": "user_requested_deletion"}
        )
    
    async def log_api_key_rotation(self, client_id: UUID, actor: str) -> None:
        """Log API key rotation."""
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.ROTATE_KEY,
            entity_type="api_key",
            entity_id=str(client_id),
            metadata={"reason": "scheduled_rotation"}
        )
    
    async def log_policy_update(
        self,
        user_id: UUID,
        policy_changes: Dict[str, Any],
        actor: str
    ) -> None:
        """Log policy updates."""
        await self._audit_repo.log_event(
            actor=actor,
            action=AuditAction.UPDATE_POLICY,
            entity_type="user_policy",
            entity_id=str(user_id),
            metadata={"changes": policy_changes}
        )