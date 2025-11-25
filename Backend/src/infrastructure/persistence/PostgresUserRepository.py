"""PostgreSQL implementation of UserRepositoryPort."""

import asyncpg
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import timedelta

from src.domain.repositories.UserRepositoryPort import UserRepositoryPort
from ...shared.types.common_types import UserId


class PostgresUserRepository(UserRepositoryPort):
    """PostgreSQL implementation of user repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create_user(
        self,
        name: str,
        email: str,
        password: str,
        external_ref: Optional[str] = None
    ) -> UserId:
        """Create a new user."""
        user_id = uuid4()
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "user" (id, name, email, password, external_ref, created_at)
                VALUES ($1, $2, $3, $4, $5, now())
                """,
                user_id, name, email, password, external_ref
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
                SELECT id, name, email, password, external_ref, created_at, deleted_at, failed_auth_attempts, locked_until
                FROM "user"
                WHERE id = $1 AND deleted_at IS NULL
                """,
                user_id
            )
            
            if row:
                return dict(row)
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, email, password, external_ref, created_at, deleted_at, failed_auth_attempts, locked_until
                FROM "user"
                WHERE email = $1 AND deleted_at IS NULL
                """,
                email
            )
            
            if row:
                return dict(row)
            return None
    
    async def get_user_by_external_ref(self, external_ref: str) -> Optional[Dict[str, Any]]:
        """Get user by external reference."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, email, password, external_ref, created_at, deleted_at, failed_auth_attempts, locked_until
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

    async def get_users_by_company(self, company: str, page: int, limit: int) -> tuple[list[dict], int]:
        """Get users by company."""
        async with self._pool.acquire() as conn:
            offset = (page - 1) * limit
            rows = await conn.fetch(
                """
                SELECT id, name, email, role, company, created_at, deleted_at
                FROM "user"
                WHERE company = $1 AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                company, limit, offset
            )
            total = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM "user"
                WHERE company = $1 AND deleted_at IS NULL
                """,
                company
            )
            return [dict(row) for row in rows], total

    async def get_all_users(self, page: int, limit: int) -> tuple[list[dict], int]:
        """Get all users."""
        async with self._pool.acquire() as conn:
            offset = (page - 1) * limit
            rows = await conn.fetch(
                """
                SELECT id, name, email, role, company, created_at, deleted_at
                FROM "user"
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            total = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM "user"
                WHERE deleted_at IS NULL
                """
            )
            return [dict(row) for row in rows], total

    async def update_user(self, user_id: UserId, user_data: dict) -> None:
        """Update user data."""
        async with self._pool.acquire() as conn:
            # Build the update query dynamically
            # This is not ideal, but it's a simple way to handle partial updates
            # In a real application, you would probably want to use a more robust solution
            # like a query builder or an ORM.
            updates = []
            values = []
            for key, value in user_data.items():
                updates.append(f"{key} = ${len(values) + 2}")
                values.append(value)
            
            if not updates:
                return

            query = f"""
                UPDATE "user"
                SET {', '.join(updates)}
                WHERE id = $1
            """
            await conn.execute(query, user_id, *values)

    async def increment_failed_auth_attempts(self, user_id: UserId) -> None:
        """Increment failed authentication attempts."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "user"
                SET failed_auth_attempts = failed_auth_attempts + 1
                WHERE id = $1
                """,
                user_id
            )

    async def lock_user_account(self, user_id: UserId, duration: timedelta) -> None:
        """Lock user account."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "user"
                SET locked_until = now() + $1
                WHERE id = $2
                """,
                duration, user_id
            )

    async def reset_failed_auth_attempts(self, user_id: UserId) -> None:
        """Reset failed authentication attempts."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "user"
                SET failed_auth_attempts = 0, locked_until = NULL
                WHERE id = $1
                """,
                user_id
            )