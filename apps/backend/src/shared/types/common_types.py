"""Common data types for the voice biometrics system."""

from enum import Enum
from typing import List, Optional
from uuid import UUID
import numpy as np

# Type aliases
UserId = UUID
ClientId = UUID
ChallengeId = UUID
AttemptId = UUID
AudioId = UUID
VoiceEmbedding = np.ndarray  # Shape: (256,)


class AuthReason(Enum):
    """Reasons for authentication decisions."""
    OK = "ok"
    LOW_SIMILARITY = "low_similarity"
    SPOOF = "spoof"
    BAD_PHRASE = "bad_phrase"
    EXPIRED_CHALLENGE = "expired_challenge"
    ERROR = "error"


class ModelKind(Enum):
    """Types of ML models in the system."""
    SPEAKER = "speaker"
    ANTISPOOF = "antispoof"
    ASR = "asr"


class RiskLevel(Enum):
    """Risk levels for authentication policies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"


class AuditAction(Enum):
    """Actions that can be audited."""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    
    # Enrollment
    ENROLLMENT_START = "ENROLLMENT_START"
    ENROLLMENT_COMPLETE = "ENROLLMENT_COMPLETE"
    ENROLLMENT_DELETED = "ENROLLMENT_DELETED"
    ENROLL = "ENROLL"  # Legacy, keep for compatibility
    
    # Verification
    VERIFICATION = "VERIFICATION"
    VERIFY = "VERIFY"  # Legacy, keep for compatibility
    
    # Admin actions
    DELETE_USER = "DELETE_USER"
    ROTATE_KEY = "ROTATE_KEY"
    CREATE_CHALLENGE = "CREATE_CHALLENGE"
    UPDATE_POLICY = "UPDATE_POLICY"