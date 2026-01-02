"""Application service for managing phrases."""

from typing import List, Optional
from uuid import UUID

from ..domain.repositories.PhraseRepositoryPort import (
    PhraseRepositoryPort,
    PhraseUsageRepositoryPort
)
from ..domain.model.Phrase import Phrase
from .dto.phrase_dto import PhraseDTO, PhraseStatsDTO


class PhraseService:
    """Service for phrase operations."""
    
    def __init__(
        self,
        phrase_repository: PhraseRepositoryPort,
        usage_repository: PhraseUsageRepositoryPort
    ):
        self._phrase_repo = phrase_repository
        self._usage_repo = usage_repository
    
    async def get_random_phrases(
        self,
        user_id: Optional[UUID] = None,
        count: int = 1,
        difficulty: Optional[str] = None,
        language: str = 'es'
    ) -> List[PhraseDTO]:
        """
        Get random phrases for a user to use in enrollment or verification.
        Excludes recently used phrases if user_id is provided.
        """
        phrases = await self._phrase_repo.find_random(
            user_id=user_id,
            exclude_recent=user_id is not None,
            difficulty=difficulty,
            language=language,
            count=count
        )
        
        return [self._to_dto(phrase) for phrase in phrases]
    
    async def get_phrase_by_id(self, phrase_id: UUID) -> Optional[PhraseDTO]:
        """Get a specific phrase by ID."""
        phrase = await self._phrase_repo.find_by_id(phrase_id)
        return self._to_dto(phrase) if phrase else None
    
    async def list_active_phrases(
        self,
        difficulty: Optional[str] = None,
        language: str = 'es',
        limit: Optional[int] = None
    ) -> List[PhraseDTO]:
        """List all active phrases with optional filters."""
        phrases = await self._phrase_repo.find_all_active(
            difficulty=difficulty,
            language=language,
            limit=limit
        )
        return [self._to_dto(phrase) for phrase in phrases]
    
    async def record_phrase_usage(
        self,
        phrase_id: UUID,
        user_id: UUID,
        used_for: str
    ) -> None:
        """
        Record that a user used a phrase.
        
        Args:
            phrase_id: ID of the phrase used
            user_id: ID of the user
            used_for: 'enrollment' or 'verification'
        """
        await self._usage_repo.record_usage(phrase_id, user_id, used_for)
    
    async def get_phrase_stats(self, language: str = 'es') -> PhraseStatsDTO:
        """Get statistics about available phrases."""
        counts_by_difficulty = await self._phrase_repo.count_by_difficulty(language)
        
        total = sum(counts_by_difficulty.values())
        
        return PhraseStatsDTO(
            total=total,
            easy=counts_by_difficulty.get('easy', 0),
            medium=counts_by_difficulty.get('medium', 0),
            hard=counts_by_difficulty.get('hard', 0),
            language=language
        )
    
    async def update_phrase_status(
        self,
        phrase_id: UUID,
        is_active: bool
    ) -> bool:
        """Enable or disable a phrase."""
        return await self._phrase_repo.update_active_status(phrase_id, is_active)
    
    async def delete_phrase(self, phrase_id: UUID) -> bool:
        """Delete a phrase from the system."""
        return await self._phrase_repo.delete(phrase_id)
    
    async def get_recent_phrase_ids(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[UUID]:
        """
        Get IDs of phrases recently used by a user.
        Used to exclude recent phrases when creating challenges.
        
        Args:
            user_id: User UUID
            limit: Maximum number of recent phrase IDs to return
            
        Returns:
            List of phrase UUIDs
        """
        return await self._usage_repo.get_user_phrase_ids(user_id, days=30)
    
    def _to_dto(self, phrase: Phrase) -> PhraseDTO:
        """Convert domain model to DTO."""
        return PhraseDTO(
            id=str(phrase.id),
            text=phrase.text,
            source=phrase.source,
            word_count=phrase.word_count,
            char_count=phrase.char_count,
            language=phrase.language,
            difficulty=phrase.difficulty,
            is_active=phrase.is_active,
            created_at=phrase.created_at.isoformat()
        )

