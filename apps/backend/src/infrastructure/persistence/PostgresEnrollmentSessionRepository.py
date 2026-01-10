"""PostgreSQL repository for enrollment sessions."""

import asyncpg
import json
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID objects."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class PostgresEnrollmentSessionRepository:
    """Repository for persistent enrollment sessions."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create_session(
        self,
        session_id: UUID,
        user_id: UUID,
        challenges: List[Dict],
        expires_in_hours: int = 1
    ) -> None:
        """Create a new enrollment session."""
        async with self._pool.acquire() as conn:
            # Delete any existing session for this user first
            await conn.execute(
                "DELETE FROM enrollment_session WHERE user_id = $1",
                user_id
            )
            
            # Create new session with custom encoder for UUIDs
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
            await conn.execute(
                """
                INSERT INTO enrollment_session (id, user_id, challenges, expires_at)
                VALUES ($1, $2, $3, $4)
                """,
                session_id,
                user_id,
                json.dumps(challenges, cls=UUIDEncoder),
                expires_at
            )
            logger.info(f"Created enrollment session {session_id} for user {user_id}")
    
    async def get_session(self, session_id: UUID) -> Optional[Dict]:
        """Get an enrollment session by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, challenges, samples_collected, challenge_index, 
                       created_at, expires_at, completed_at
                FROM enrollment_session
                WHERE id = $1 AND expires_at > NOW() AND completed_at IS NULL
                """,
                session_id
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "challenges": json.loads(row["challenges"]),
                "samples_collected": row["samples_collected"],
                "challenge_index": row["challenge_index"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }
    
    async def get_session_by_user(self, user_id: UUID) -> Optional[Dict]:
        """Get active enrollment session for a user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, challenges, samples_collected, challenge_index,
                       created_at, expires_at, completed_at
                FROM enrollment_session
                WHERE user_id = $1 AND expires_at > NOW() AND completed_at IS NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id
            )
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "challenges": json.loads(row["challenges"]),
                "samples_collected": row["samples_collected"],
                "challenge_index": row["challenge_index"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }
    
    async def update_session(
        self,
        session_id: UUID,
        samples_collected: int,
        challenge_index: int
    ) -> None:
        """Update session progress."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE enrollment_session 
                SET samples_collected = $2, challenge_index = $3
                WHERE id = $1
                """,
                session_id,
                samples_collected,
                challenge_index
            )
    
    async def complete_session(self, session_id: UUID) -> None:
        """Mark session as completed."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE enrollment_session 
                SET completed_at = NOW()
                WHERE id = $1
                """,
                session_id
            )
            logger.info(f"Completed enrollment session {session_id}")
    
    async def delete_session(self, session_id: UUID) -> None:
        """Delete a session."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM enrollment_session WHERE id = $1",
                session_id
            )
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions. Returns count of deleted sessions."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM enrollment_session WHERE expires_at < NOW()"
            )
            count = int(result.split()[-1]) if result else 0
            if count > 0:
                logger.info(f"Cleaned up {count} expired enrollment sessions")
            return count
    
    async def ensure_table_exists(self) -> None:
        """Create the enrollment_session table if it doesn't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS enrollment_session (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    challenges JSONB NOT NULL,
                    samples_collected INTEGER DEFAULT 0,
                    challenge_index INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour'),
                    completed_at TIMESTAMPTZ
                );
                
                CREATE INDEX IF NOT EXISTS idx_enrollment_session_user 
                ON enrollment_session(user_id);
                
                CREATE INDEX IF NOT EXISTS idx_enrollment_session_expires 
                ON enrollment_session(expires_at);
            """)
            logger.info("Ensured enrollment_session table exists")
