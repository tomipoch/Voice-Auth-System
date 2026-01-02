"""PostgreSQL implementation of UserRepositoryPort."""

import json
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
        email: Optional[str] = None,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        rut: Optional[str] = None,
        role: str = "user",
        company: Optional[str] = None,
        external_ref: Optional[str] = None
    ) -> UserId:
        """Create a new user."""
        user_id = uuid4()
        
        # Generate defaults if missing
        if not email:
            email = f"anon_{user_id}@example.com"
        if not password:
            password = "temporary_password"
        if not first_name:
            first_name = "Anonymous"
        if not last_name:
            last_name = "User"
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "user" (id, email, password, first_name, last_name, rut, role, company, external_ref, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())
                """,
                user_id, email, password, first_name, last_name, rut, role, company, external_ref
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
                SELECT u.id, u.email, u.password, u.first_name, u.last_name, u.rut, u.role, u.company, u.external_ref, 
                       u.created_at, u.deleted_at, u.failed_auth_attempts, u.locked_until, u.last_login, u.settings,
                       (v.id IS NOT NULL) as has_voiceprint
                FROM "user" u
                LEFT JOIN voiceprint v ON u.id = v.user_id
                WHERE u.id = $1 AND u.deleted_at IS NULL
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
                SELECT id, email, password, first_name, last_name, rut, role, company, external_ref,
                       created_at, deleted_at, failed_auth_attempts, locked_until, last_login, settings
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
                SELECT id, email, password, first_name, last_name, rut, role, company, external_ref,
                       created_at, deleted_at, failed_auth_attempts, locked_until, last_login, settings
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
                SELECT u.id, u.email, u.first_name, u.last_name, u.rut, u.role, u.company, u.external_ref, u.created_at, u.deleted_at,
                       (v.id IS NOT NULL) as has_voiceprint
                FROM "user" u
                LEFT JOIN voiceprint v ON u.id = v.user_id
                WHERE u.company = $1 AND u.deleted_at IS NULL
                ORDER BY u.created_at DESC
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
                SELECT u.id, u.email, u.first_name, u.last_name, u.rut, u.role, u.company, u.external_ref, u.created_at, u.deleted_at,
                       (v.id IS NOT NULL) as has_voiceprint
                FROM "user" u
                LEFT JOIN voiceprint v ON u.id = v.user_id
                WHERE u.deleted_at IS NULL
                ORDER BY u.created_at DESC
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

    # Whitelist of allowed fields for user updates (security measure against SQL injection)
    ALLOWED_UPDATE_FIELDS = {
        'first_name', 'last_name', 'rut', 'company', 'role', 
        'password', 'settings', 'last_login', 'failed_auth_attempts', 'locked_until'
    }

    async def update_user(self, user_id: UserId, user_data: dict) -> None:
        """Update user data."""
        async with self._pool.acquire() as conn:
            # Build the update query dynamically with field validation
            updates = []
            values = []
            for key, value in user_data.items():
                # Validate that only allowed fields are updated (prevent SQL injection)
                if key not in self.ALLOWED_UPDATE_FIELDS:
                    raise ValueError(f"Field '{key}' is not allowed for update")
                
                # Convert settings dict to JSON string for JSONB field
                if key == 'settings' and isinstance(value, dict):
                    value = json.dumps(value)
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