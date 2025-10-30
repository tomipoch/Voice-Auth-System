"""User repository port (interface)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...shared.types.common_types import UserId


class UserRepositoryPort(ABC):
    """Repository interface for users."""
    
    @abstractmethod
    async def create_user(self, external_ref: Optional[str] = None) -> UserId:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: UserId) -> Optional[dict]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_user_by_external_ref(self, external_ref: str) -> Optional[dict]:
        """Get user by external reference."""
        pass
    
    @abstractmethod
    async def user_exists(self, user_id: UserId) -> bool:
        """Check if user exists."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: UserId) -> None:
        """Soft delete a user (mark as deleted)."""
        pass
    
    @abstractmethod
    async def get_user_policy(self, user_id: UserId) -> Optional[dict]:
        """Get user's privacy/retention policy."""
        pass
    
    @abstractmethod
    async def set_user_policy(
        self,
        user_id: UserId,
        keep_audio: bool = False,
        retention_days: int = 7
    ) -> None:
        """Set user's privacy/retention policy."""
        pass