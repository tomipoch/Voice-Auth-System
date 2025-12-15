"""PostgreSQL implementation of PhraseRepositoryPort."""

import asyncpg
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from ...domain.repositories.PhraseRepositoryPort import (
    PhraseRepositoryPort, 
    PhraseUsageRepositoryPort
)
from ...domain.model.Phrase import Phrase, PhraseUsage


class PostgresPhraseRepository(PhraseRepositoryPort):
    """PostgreSQL implementation of phrase repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def save(self, phrase: Phrase) -> None:
        """Save a phrase to the repository."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO phrase (
                    id, text, source, word_count, char_count, 
                    language, difficulty, is_active, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    source = EXCLUDED.source,
                    word_count = EXCLUDED.word_count,
                    char_count = EXCLUDED.char_count,
                    language = EXCLUDED.language,
                    difficulty = EXCLUDED.difficulty,
                    is_active = EXCLUDED.is_active
                """,
                phrase.id,
                phrase.text,
                phrase.source,
                phrase.word_count,
                phrase.char_count,
                phrase.language,
                phrase.difficulty,
                phrase.is_active,
                phrase.created_at
            )
    
    async def find_by_id(self, phrase_id: UUID) -> Optional[Phrase]:
        """Find a phrase by its ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, text, source, word_count, char_count, 
                       language, difficulty, is_active, created_at
                FROM phrase
                WHERE id = $1
                """,
                phrase_id
            )
            
            if row:
                return Phrase(**dict(row))
            return None
    
    async def find_all_active(
        self, 
        difficulty: Optional[str] = None,
        language: str = 'es',
        limit: Optional[int] = None
    ) -> List[Phrase]:
        """Find all active phrases with optional filters."""
        query = """
            SELECT id, text, source, word_count, char_count, 
                   language, difficulty, is_active, created_at
            FROM phrase
            WHERE is_active = TRUE AND language = $1
        """
        params = [language]
        
        if difficulty:
            query += " AND difficulty = $2"
            params.append(difficulty)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [Phrase(**dict(row)) for row in rows]
    
    async def find_random(
        self,
        user_id: Optional[UUID] = None,
        exclude_recent: bool = True,
        difficulty: Optional[str] = None,
        language: str = 'es',
        count: int = 1
    ) -> List[Phrase]:
        """Find random phrases for a user."""
        query = """
            SELECT p.id, p.text, p.source, p.word_count, p.char_count, 
                   p.language, p.difficulty, p.is_active, p.created_at
            FROM phrase p
            WHERE p.is_active = TRUE AND p.language = $1
        """
        params = [language]
        param_idx = 2
        
        # Exclude recently used phrases if requested
        if exclude_recent and user_id:
            query += f"""
                AND p.id NOT IN (
                    SELECT phrase_id 
                    FROM phrase_usage 
                    WHERE user_id = ${param_idx}
                    AND used_at > NOW() - INTERVAL '30 days'
                )
            """
            params.append(user_id)
            param_idx += 1
        
        # Filter by difficulty
        if difficulty:
            query += f" AND p.difficulty = ${param_idx}"
            params.append(difficulty)
            param_idx += 1
        
        # Random selection
        query += f" ORDER BY RANDOM() LIMIT ${param_idx}"
        params.append(count)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [Phrase(**dict(row)) for row in rows]
    
    async def get_recent_phrase_ids(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[UUID]:
        """Get IDs of recently used phrases for a user.
        
        Args:
            user_id: User ID to get recent phrases for
            limit: Maximum number of phrase IDs to return
            
        Returns:
            List of phrase UUIDs, ordered by most recent first
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (phrase_id) phrase_id, used_at
                FROM phrase_usage
                WHERE user_id = $1 AND phrase_id IS NOT NULL
                ORDER BY phrase_id, used_at DESC
                LIMIT $2
                """,
                user_id,
                limit
            )
            
            return [row['phrase_id'] for row in rows]


    
    async def count_by_difficulty(self, language: str = 'es') -> dict:
        """Count phrases grouped by difficulty."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT difficulty, COUNT(*) as count
                FROM phrase
                WHERE is_active = TRUE AND language = $1
                GROUP BY difficulty
                """,
                language
            )
            return {row['difficulty']: row['count'] for row in rows}
    
    async def update_active_status(self, phrase_id: UUID, is_active: bool) -> bool:
        """Update the active status of a phrase."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE phrase
                SET is_active = $2
                WHERE id = $1
                """,
                phrase_id, is_active
            )
            return result == "UPDATE 1"
    
    async def delete(self, phrase_id: UUID) -> bool:
        """Delete a phrase from the repository."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM phrase
                WHERE id = $1
                """,
                phrase_id
            )
            return result == "DELETE 1"


class PostgresPhraseUsageRepository(PhraseUsageRepositoryPort):
    """PostgreSQL implementation of phrase usage repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def record_usage(
        self, 
        phrase_id: UUID, 
        user_id: UUID, 
        used_for: str
    ) -> PhraseUsage:
        """Record that a user used a phrase."""
        now = datetime.now(timezone.utc)
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO phrase_usage (phrase_id, user_id, used_for, used_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, phrase_id, user_id, used_for, used_at
                """,
                phrase_id, user_id, used_for, now
            )
            return PhraseUsage(**dict(row))
    
    async def find_recent_by_user(
        self, 
        user_id: UUID, 
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[PhraseUsage]:
        """Find recent phrase usages for a user."""
        query = """
            SELECT id, phrase_id, user_id, used_for, used_at
            FROM phrase_usage
            WHERE user_id = $1 
            AND used_at > $2
            ORDER BY used_at DESC
        """
        params = [user_id, datetime.now(timezone.utc) - timedelta(days=days)]
        
        if limit:
            query += " LIMIT $3"
            params.append(limit)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [PhraseUsage(**dict(row)) for row in rows]
    
    async def get_user_phrase_ids(
        self, 
        user_id: UUID, 
        days: int = 30
    ) -> List[UUID]:
        """Get phrase IDs that a user has recently used."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT phrase_id
                FROM phrase_usage
                WHERE user_id = $1 
                AND used_at > $2
                """,
                user_id, 
                datetime.now(timezone.utc) - timedelta(days=days)
            )
            return [row['phrase_id'] for row in rows]
    
    async def count_by_phrase(self, phrase_id: UUID) -> int:
        """Count how many times a phrase has been used."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM phrase_usage
                WHERE phrase_id = $1
                """,
                phrase_id
            )
            return count or 0
