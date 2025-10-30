"""Domain events for the voice biometrics system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from ...shared.types.common_types import UserId, ClientId, AuditAction


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    event_id: UUID
    occurred_at: datetime
    event_type: str
    aggregate_id: UUID
    metadata: Dict[str, Any]


@dataclass
class UserEnrolledEvent(DomainEvent):
    """Event fired when a user completes enrollment."""
    user_id: UserId
    sample_count: int
    enrollment_quality: float


@dataclass
class AuthenticationAttemptedEvent(DomainEvent):
    """Event fired when authentication is attempted."""
    user_id: Optional[UserId]
    client_id: Optional[ClientId]
    success: bool
    reason: str
    similarity_score: Optional[float]
    spoof_probability: Optional[float]


@dataclass
class SuspiciousActivityDetectedEvent(DomainEvent):
    """Event fired when suspicious activity is detected."""
    user_id: Optional[UserId]
    client_id: Optional[ClientId]
    risk_indicators: Dict[str, bool]
    severity: str  # low, medium, high, critical


@dataclass
class AuditEvent(DomainEvent):
    """Event for audit logging."""
    actor: str
    action: AuditAction
    entity_type: str
    entity_id: str
    success: bool
    error_message: Optional[str] = None