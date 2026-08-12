"""Challenge repository port (interface)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...shared.types.common_types import UserId, ChallengeId


class ChallengeRepositoryPort(ABC):
    """Repository interface for dynamic challenges."""
    
    @abstractmethod
    async def create_challenge(
        self,
        user_id: UserId,
        phrase: str,
        expires_at: datetime
    ) -> ChallengeId:
        """Create a new challenge for a user."""
        pass
    
    @abstractmethod
    async def get_challenge(self, challenge_id: ChallengeId) -> Optional[dict]:
        """Get challenge details by ID."""
        pass
    
    @abstractmethod
    async def get_active_challenge(self, user_id: UserId) -> Optional[dict]:
        """Get the most recent active challenge for a user."""
        pass
    
    @abstractmethod
    async def mark_challenge_used(self, challenge_id: ChallengeId) -> None:
        """Mark a challenge as used."""
        pass
    
    @abstractmethod
    async def is_challenge_valid(self, challenge_id: ChallengeId) -> bool:
        """Check if a challenge is still valid (not expired, not used)."""
        pass
    
    @abstractmethod
    async def cleanup_expired_challenges(self) -> int:
        """Remove old/expired challenges. Returns count of deleted challenges."""
        pass
    
    @abstractmethod
    async def cleanup_unused_challenges(self, user_id: UserId) -> int:
        """Remove all unused challenges for a specific user. Returns count of deleted challenges."""
        pass