"""PostgreSQL implementation of ChallengeRepositoryPort."""

import asyncpg
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from ...domain.repositories.ChallengeRepositoryPort import ChallengeRepositoryPort
from ...shared.types.common_types import UserId, ChallengeId

logger = logging.getLogger(__name__)


class PostgresChallengeRepository(ChallengeRepositoryPort):
    """PostgreSQL implementation of challenge repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create_challenge(
        self,
        user_id: UserId,
        phrase: str,
        phrase_id: UUID,
        expires_at: datetime
    ) -> ChallengeId:
        """Create a new challenge for a user with phrase reference."""
        async with self._pool.acquire() as conn:
            challenge_id = await conn.fetchval(
                """
                INSERT INTO challenge (user_id, phrase, phrase_id, expires_at, created_at)
                VALUES ($1, $2, $3, $4, now())
                RETURNING id
                """,
                user_id,
                phrase,
                phrase_id,
                expires_at
            )
            
            logger.info(f"Created challenge {challenge_id} for user {user_id} with phrase {phrase_id}")
            return challenge_id
    
    async def get_challenge(self, challenge_id: ChallengeId) -> Optional[Dict[str, Any]]:
        """Get challenge details by ID with phrase information."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    c.id,
                    c.user_id,
                    c.phrase,
                    c.phrase_id,
                    c.expires_at,
                    c.used_at,
                    c.created_at,
                    p.difficulty,
                    p.language,
                    p.source
                FROM challenge c
                LEFT JOIN phrase p ON p.id = c.phrase_id
                WHERE c.id = $1
                """,
                challenge_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def get_active_challenge(self, user_id: UserId) -> Optional[Dict[str, Any]]:
        """Get the most recent active challenge for a user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    c.id,
                    c.user_id,
                    c.phrase,
                    c.phrase_id,
                    c.expires_at,
                    c.used_at,
                    c.created_at,
                    p.difficulty,
                    p.language
                FROM challenge c
                LEFT JOIN phrase p ON p.id = c.phrase_id
                WHERE c.user_id = $1
                  AND c.used_at IS NULL
                  AND c.expires_at > now()
                ORDER BY c.created_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def mark_challenge_used(self, challenge_id: ChallengeId) -> None:
        """Mark a challenge as used."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE challenge
                SET used_at = now()
                WHERE id = $1 AND used_at IS NULL
                """,
                challenge_id
            )
            
            if result == "UPDATE 1":
                logger.info(f"Challenge {challenge_id} marked as used")
            else:
                logger.warning(f"Challenge {challenge_id} not found or already used")
    
    async def is_challenge_valid(self, challenge_id: ChallengeId) -> bool:
        """Check if a challenge is still valid (not expired, not used)."""
        async with self._pool.acquire() as conn:
            is_valid = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM challenge
                    WHERE id = $1
                      AND used_at IS NULL
                      AND expires_at > now()
                )
                """,
                challenge_id
            )
            
            return bool(is_valid)
    
    async def cleanup_expired_challenges(self, older_than_hours: int = 1) -> int:
        """
        Remove expired challenges older than specified hours.
        
        Args:
            older_than_hours: Delete challenges expired more than N hours ago
            
        Returns:
            Number of deleted challenges
        """
        async with self._pool.acquire() as conn:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            result = await conn.execute(
                """
                DELETE FROM challenge
                WHERE expires_at < $1
                  AND expires_at < now()
                """,
                cutoff_time
            )
            
            # Extract count from result string "DELETE N"
            count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired challenges older than {older_than_hours}h")
            
            return count
    
    async def mark_expired_challenges(self) -> int:
        """
        Mark challenges as expired (without deleting them).
        This is used by the cleanup job to track expired challenges.
        
        Returns:
            Number of challenges marked as expired
        """
        async with self._pool.acquire() as conn:
            # Note: We don't have an 'expired' status in the current schema
            # Expired challenges are identified by expires_at < now()
            # This method can be used to count them
            count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM challenge
                WHERE expires_at < now()
                  AND used_at IS NULL
                """
            )
            
            if count > 0:
                logger.debug(f"Found {count} expired challenges")
            
            return int(count)
    
    async def cleanup_used_challenges(self, older_than_hours: int = 24) -> int:
        """
        Remove used challenges older than specified hours.
        
        Args:
            older_than_hours: Delete challenges used more than N hours ago
            
        Returns:
            Number of deleted challenges
        """
        async with self._pool.acquire() as conn:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            result = await conn.execute(
                """
                DELETE FROM challenge
                WHERE used_at IS NOT NULL
                  AND used_at < $1
                """,
                cutoff_time
            )
            
            count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            
            if count > 0:
                logger.info(f"Cleaned up {count} used challenges older than {older_than_hours}h")
            
            return count
    
    async def cleanup_unused_challenges(self, user_id: UserId) -> int:
        """
        Remove all unused challenges for a specific user.
        Used before creating new challenge batches to prevent accumulation.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of deleted challenges
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM challenge
                WHERE user_id = $1
                  AND used_at IS NULL
                """,
                user_id
            )
            
            count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            
            if count > 0:
                logger.debug(f"Cleaned up {count} unused challenges for user {user_id}")
            
            return count
    
    async def count_active_challenges(self, user_id: UserId) -> int:
        """Count active challenges for a user (not used, not expired)."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM challenge
                WHERE user_id = $1
                  AND used_at IS NULL
                  AND expires_at > now()
                """,
                user_id
            )
            
            return int(count)
    
    async def count_recent_challenges(
        self, 
        user_id: UserId, 
        since_hours: int = 1
    ) -> int:
        """
        Count challenges created by user in the last N hours.
        Used for rate limiting.
        
        Args:
            user_id: User UUID
            since_hours: Count challenges created in last N hours
            
        Returns:
            Number of challenges created
        """
        async with self._pool.acquire() as conn:
            cutoff_time = datetime.now() - timedelta(hours=since_hours)
            
            count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM challenge
                WHERE user_id = $1
                  AND created_at > $2
                """,
                user_id,
                cutoff_time
            )
            
            return int(count)
    
    async def get_challenges_batch(
        self,
        user_id: UserId,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Get multiple active challenges for a user.
        Useful for batch operations.
        
        Args:
            user_id: User UUID
            limit: Maximum number of challenges to return
            
        Returns:
            List of challenge dictionaries
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    c.id,
                    c.user_id,
                    c.phrase,
                    c.phrase_id,
                    c.expires_at,
                    c.used_at,
                    c.created_at,
                    p.difficulty,
                    p.language
                FROM challenge c
                LEFT JOIN phrase p ON p.id = c.phrase_id
                WHERE c.user_id = $1
                  AND c.used_at IS NULL
                  AND c.expires_at > now()
                ORDER BY c.created_at DESC
                LIMIT $2
                """,
                user_id,
                limit
            )
            
            return [dict(row) for row in rows]
