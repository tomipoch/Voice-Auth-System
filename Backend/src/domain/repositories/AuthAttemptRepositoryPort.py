"""Authentication attempt repository port (interface)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..model.AuthAttemptResult import AuthAttemptResult
from ...shared.types.common_types import UserId, ClientId, AttemptId


class AuthAttemptRepositoryPort(ABC):
    """Repository interface for authentication attempts."""
    
    @abstractmethod
    async def save_attempt(self, attempt: AuthAttemptResult) -> AttemptId:
        """Save an authentication attempt."""
        pass
    
    @abstractmethod
    async def get_attempt(self, attempt_id: AttemptId) -> Optional[AuthAttemptResult]:
        """Get attempt by ID."""
        pass
    
    @abstractmethod
    async def update_attempt(self, attempt: AuthAttemptResult) -> None:
        """Update an existing attempt."""
        pass
    
    @abstractmethod
    async def get_recent_attempts(
        self,
        user_id: UserId,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuthAttemptResult]:
        """Get recent attempts for a user."""
        pass
    
    @abstractmethod
    async def get_failed_attempts_count(
        self,
        user_id: UserId,
        since: datetime
    ) -> int:
        """Count failed attempts for a user since a certain time."""
        pass
    
    @abstractmethod
    async def get_attempts_by_client(
        self,
        client_id: ClientId,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuthAttemptResult]:
        """Get recent attempts for a client."""
        pass
    
    @abstractmethod
    async def get_suspicious_attempts(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuthAttemptResult]:
        """Get attempts that might indicate fraud."""
        pass
    
    @abstractmethod
    async def store_audio_blob(self, audio_data: bytes, mime_type: str) -> UUID:
        """Store encrypted audio data and return blob ID."""
        pass
    
    @abstractmethod
    async def get_audio_blob(self, audio_id: UUID) -> Optional[tuple[bytes, str]]:
        """Retrieve audio data and mime type."""
        pass