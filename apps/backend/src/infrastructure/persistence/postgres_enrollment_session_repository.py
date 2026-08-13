"""PostgreSQL implementation of EnrollmentSessionRepositoryPort."""

import json
import asyncpg
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...domain.repositories.enrollment_session_repository_port import (
    EnrollmentSessionRepositoryPort,
)


class PostgresEnrollmentSessionRepository(EnrollmentSessionRepositoryPort):
    """Persistencia de enrollment_session en PostgreSQL."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def upsert(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        challenges: list,
        samples_collected: int,
        challenge_index: int,
        expires_at: datetime,
    ) -> None:
        """Crea o reemplaza la sesión activa del usuario (UNIQUE por user_id).

        El UNIQUE(user_id) del baseline es DEFERRABLE INITIALLY DEFERRED, lo
        que impide usarlo como árbitro de ON CONFLICT. Implementamos el upsert
        con SELECT FOR UPDATE + DELETE + INSERT en una transacción para
        reemplazar la fila por completo (nuevo id) manteniendo la invariante
        de "una sesión activa por usuario".
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchval(
                    "SELECT id FROM enrollment_session WHERE user_id = $1 FOR UPDATE",
                    user_id,
                )
                if existing is not None:
                    await conn.execute(
                        "DELETE FROM enrollment_session WHERE user_id = $1", user_id
                    )
                await conn.execute(
                    """
                    INSERT INTO enrollment_session (
                        id, user_id, challenges, samples_collected, challenge_index,
                        created_at, expires_at, completed_at
                    ) VALUES ($1, $2, $3, $4, $5, now(), $6, NULL)
                    """,
                    session_id, user_id, json.dumps(challenges, ensure_ascii=False),
                    samples_collected, challenge_index, expires_at,
                )

    async def get_by_id(self, session_id: UUID) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, challenges, samples_collected, challenge_index,
                       created_at, expires_at, completed_at
                FROM enrollment_session
                WHERE id = $1 AND completed_at IS NULL AND expires_at > now()
                """,
                session_id,
            )
            if not row:
                return None
            result = dict(row)
            result["challenges"] = json.loads(result["challenges"])
            return result

    async def get_by_user(self, user_id: UUID) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, challenges, samples_collected, challenge_index,
                       created_at, expires_at, completed_at
                FROM enrollment_session
                WHERE user_id = $1 AND completed_at IS NULL AND expires_at > now()
                """,
                user_id,
            )
            if not row:
                return None
            result = dict(row)
            result["challenges"] = json.loads(result["challenges"])
            return result

    async def mark_completed(self, session_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE enrollment_session SET completed_at = now() WHERE id = $1",
                session_id,
            )
