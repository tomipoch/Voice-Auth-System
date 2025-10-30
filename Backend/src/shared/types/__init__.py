"""Common types for the voice biometrics system."""

from enum import Enum
from typing import NewType
from uuid import UUID
import numpy as np

# Type aliases for better type safety
UserId = NewType('UserId', UUID)
ClientId = NewType('ClientId', UUID)
ChallengeId = NewType('ChallengeId', UUID)
AudioId = NewType('AudioId', UUID)
AttemptId = NewType('AttemptId', UUID)
VoiceEmbedding = NewType('VoiceEmbedding', np.ndarray)


class AuthReason(Enum):
    """Reasons for authentication decisions."""
    OK = "ok"
    LOW_SIMILARITY = "low_similarity"
    SPOOF = "spoof"
    BAD_PHRASE = "bad_phrase"
    EXPIRED_CHALLENGE = "expired_challenge"
    ERROR = "error"


class AuditAction(Enum):
    """Types of auditable actions."""
    ENROLL = "ENROLL"
    VERIFY = "VERIFY"
    DELETE_USER = "DELETE_USER"
    ROTATE_KEY = "ROTATE_KEY"
    CREATE_CHALLENGE = "CREATE_CHALLENGE"
    UPDATE_POLICY = "UPDATE_POLICY"


class RiskLevel(Enum):
    """Risk levels for policies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"