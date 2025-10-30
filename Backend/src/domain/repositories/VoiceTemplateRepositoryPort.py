"""Voice template repository port (interface)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
import numpy as np

from ..model.VoiceSignature import VoiceSignature
from ...shared.types.common_types import UserId, VoiceEmbedding


class VoiceTemplateRepositoryPort(ABC):
    """Repository interface for voice templates (voiceprints)."""
    
    @abstractmethod
    async def save_voiceprint(self, voiceprint: VoiceSignature) -> None:
        """Save a user's voiceprint."""
        pass
    
    @abstractmethod
    async def get_voiceprint_by_user(self, user_id: UserId) -> Optional[VoiceSignature]:
        """Get the current voiceprint for a user."""
        pass
    
    @abstractmethod
    async def update_voiceprint(self, voiceprint: VoiceSignature) -> None:
        """Update an existing voiceprint."""
        pass
    
    @abstractmethod
    async def delete_voiceprint(self, user_id: UserId) -> None:
        """Delete a user's voiceprint."""
        pass
    
    @abstractmethod
    async def save_enrollment_sample(
        self,
        user_id: UserId,
        embedding: VoiceEmbedding,
        snr_db: Optional[float] = None,
        duration_sec: Optional[float] = None
    ) -> UUID:
        """Save an individual enrollment sample."""
        pass
    
    @abstractmethod
    async def get_enrollment_samples(self, user_id: UserId) -> List[dict]:
        """Get all enrollment samples for a user."""
        pass
    
    @abstractmethod
    async def save_voiceprint_history(self, voiceprint: VoiceSignature) -> None:
        """Save voiceprint to history for audit trail."""
        pass
    
    @abstractmethod
    async def get_voiceprint_history(self, user_id: UserId) -> List[VoiceSignature]:
        """Get voiceprint history for a user."""
        pass