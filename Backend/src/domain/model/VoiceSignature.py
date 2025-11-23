"""Voice signature domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
import numpy as np

from ...shared.types.common_types import VoiceEmbedding, UserId


@dataclass
class VoiceSignature:
    """Represents a user's voice biometric signature (voiceprint)."""
    
    id: UUID
    user_id: UserId
    embedding: VoiceEmbedding
    created_at: datetime
    speaker_model_id: Optional[int] = None