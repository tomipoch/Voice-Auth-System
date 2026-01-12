"""Phrase repository port definition."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..model.Phrase import Phrase, PhraseUsage


class PhraseRepositoryPort(ABC):
    """Port for phrase repository operations."""
    
    @abstractmethod
    async def save(self, phrase: Phrase) -> None:
        """Save a phrase to the repository."""
        pass
    
    @abstractmethod
    async def find_by_id(self, phrase_id: UUID) -> Optional[Phrase]:
        """Find a phrase by its ID."""
        pass
    
    @abstractmethod
    async def find_all_active(
        self, 
        difficulty: Optional[str] = None,
        language: str = 'es',
        limit: Optional[int] = None
    ) -> List[Phrase]:
        """Find all active phrases with optional filters."""
        pass
    
    @abstractmethod
    async def find_random(
        self,
        user_id: Optional[UUID] = None,
        exclude_recent: bool = True,
        difficulty: Optional[str] = None,
        language: str = 'es',
        count: int = 1
    ) -> List[Phrase]:
        """
        Find random phrases for a user.
        
        Args:
            user_id: User ID to get phrases for
            exclude_recent: If True, exclude recently used phrases
            difficulty: Filter by difficulty level
            language: Filter by language
            count: Number of phrases to return
        """
        pass
    
    @abstractmethod
    async def count_by_difficulty(self, language: str = 'es') -> dict:
        """Count phrases grouped by difficulty."""
        pass
    
    @abstractmethod
    async def update_active_status(self, phrase_id: UUID, is_active: bool) -> bool:
        """Update the active status of a phrase."""
        pass
    
    @abstractmethod
    async def delete(self, phrase_id: UUID) -> bool:
        """Delete a phrase from the repository."""
        pass
    
    @abstractmethod
    async def get_phrase_statistics(
        self,
        min_attempts: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get performance statistics for all phrases with minimum attempts.
        
        Args:
            min_attempts: Minimum number of attempts required for analysis
            days: Number of days to look back for statistics
            
        Returns:
            List of dictionaries with phrase stats:
            - phrase_id: UUID of the phrase
            - text: Phrase text (truncated)
            - difficulty: Phrase difficulty level
            - total_attempts: Number of verification attempts
            - success_rate: Ratio of successful verifications
            - avg_asr_score: Average ASR phrase match score
            - phrase_ok_rate: Ratio of phrase_ok=True
        """
        pass


class PhraseUsageRepositoryPort(ABC):
    """Port for phrase usage repository operations."""
    
    @abstractmethod
    async def record_usage(
        self, 
        phrase_id: UUID, 
        user_id: UUID, 
        used_for: str
    ) -> PhraseUsage:
        """Record that a user used a phrase."""
        pass
    
    @abstractmethod
    async def find_recent_by_user(
        self, 
        user_id: UUID, 
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[PhraseUsage]:
        """Find recent phrase usages for a user."""
        pass
    
    @abstractmethod
    async def get_user_phrase_ids(
        self, 
        user_id: UUID, 
        days: int = 30
    ) -> List[UUID]:
        """Get phrase IDs that a user has recently used."""
        pass
    
    @abstractmethod
    async def count_by_phrase(self, phrase_id: UUID) -> int:
        """Count how many times a phrase has been used."""
        pass
