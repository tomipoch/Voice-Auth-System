"""User repository port (interface)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from datetime import timedelta

from ...shared.types.common_types import UserId


class UserRepositoryPort(ABC):
    """Repository interface for users."""
    
    @abstractmethod
    async def create_user(
        self, 
        email: Optional[str] = None, 
        password: Optional[str] = None, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "user",
        company: Optional[str] = None,
        external_ref: Optional[str] = None
    ) -> UserId:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: UserId) -> Optional[dict]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
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

    @abstractmethod
    async def get_users_by_company(self, company: str, page: int, limit: int) -> tuple[list[dict], int]:
        """Get users by company."""
        pass

    @abstractmethod
    async def get_all_users(self, page: int, limit: int) -> tuple[list[dict], int]:
        """Get all users."""
        pass

    @abstractmethod
    async def update_user(self, user_id: UserId, user_data: dict) -> None:
        """Update user data."""
        pass

    @abstractmethod
    async def increment_failed_auth_attempts(self, user_id: UserId) -> None:
        """Increment failed authentication attempts."""
        pass

    @abstractmethod
    async def lock_user_account(self, user_id: UserId, duration: timedelta) -> None:
        """Lock user account."""
        pass

    @abstractmethod
    async def reset_failed_auth_attempts(self, user_id: UserId) -> None:
        """Reset failed authentication attempts."""
        pass