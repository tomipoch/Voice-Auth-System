"""PostgreSQL implementation of UserRepositoryPort."""

import asyncpg
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ...shared.types.common_types import UserId


class PostgresUserRepository(UserRepositoryPort):
    """PostgreSQL implementation of user repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create_user(self, external_ref: Optional[str] = None) -> UserId:
        """Create a new user."""
        user_id = uuid4()
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "user" (id, external_ref, created_at)
                VALUES ($1, $2, now())
                """,
                user_id, external_ref
            )
            
            # Create default user policy
            await conn.execute(
                """
                INSERT INTO user_policy (user_id, keep_audio, retention_days, consent_at)
                VALUES ($1, $2, $3, now())
                """,
                user_id, False, 7
            )
        
        return user_id
    
    async def get_user(self, user_id: UserId) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, external_ref, created_at, deleted_at
                FROM "user"
                WHERE id = $1 AND deleted_at IS NULL
                """,
                user_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def get_user_by_external_ref(self, external_ref: str) -> Optional[Dict[str, Any]]:
        """Get user by external reference."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, external_ref, created_at, deleted_at
                FROM "user"
                WHERE external_ref = $1 AND deleted_at IS NULL
                """,
                external_ref
            )
            
            if row:
                return dict(row)
            return None
    
    async def user_exists(self, user_id: UserId) -> bool:
        """Check if user exists."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM "user"
                WHERE id = $1 AND deleted_at IS NULL
                """,
                user_id
            )
            return count > 0
    
    async def delete_user(self, user_id: UserId) -> None:
        """Soft delete a user (mark as deleted)."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "user"
                SET deleted_at = now()
                WHERE id = $1
                """,
                user_id
            )
    
    async def get_user_policy(self, user_id: UserId) -> Optional[Dict[str, Any]]:
        """Get user's privacy/retention policy."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, keep_audio, retention_days, consent_at
                FROM user_policy
                WHERE user_id = $1
                """,
                user_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def set_user_policy(
        self,
        user_id: UserId,
        keep_audio: bool = False,
        retention_days: int = 7
    ) -> None:
        """Set user's privacy/retention policy."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_policy (user_id, keep_audio, retention_days, consent_at)
                VALUES ($1, $2, $3, now())
                ON CONFLICT (user_id)
                DO UPDATE SET
                    keep_audio = EXCLUDED.keep_audio,
                    retention_days = EXCLUDED.retention_days,
                    consent_at = now()
                """,
                user_id, keep_audio, retention_days
            )