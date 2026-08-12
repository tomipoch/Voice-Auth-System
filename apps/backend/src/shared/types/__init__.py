"""Common types for the voice biometrics system.

Re-exports all types from common_types.py for convenient importing.
Usage: from ...shared.types import UserId, AuditAction, etc.
"""

from .common_types import (
    # Type aliases
    UserId,
    ClientId,
    ChallengeId,
    AttemptId,
    AudioId,
    VoiceEmbedding,
    
    # Enums
    AuthReason,
    ModelKind,
    RiskLevel,
    AudioFormat,
    AuditAction,
)

__all__ = [
    # Type aliases
    "UserId",
    "ClientId",
    "ChallengeId",
    "AttemptId",
    "AudioId",
    "VoiceEmbedding",
    
    # Enums
    "AuthReason",
    "ModelKind",
    "RiskLevel",
    "AudioFormat",
    "AuditAction",
]