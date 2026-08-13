"""PostgreSQL implementation of VerificationAttemptRepositoryPort."""

import asyncpg
from typing import Optional
from uuid import UUID, uuid4

from ...domain.repositories.verification_attempt_repository_port import (
    VerificationAttemptRepositoryPort,
)


class PostgresVerificationAttemptRepository(VerificationAttemptRepositoryPort):
    """Persistencia de auth_attempt, scores y audio_blob en PostgreSQL."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def save_audio_blob(self, content: bytes, mime: str = "audio/wav") -> UUID:
        audio_id = uuid4()
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO audio_blob (id, content, mime, created_at) VALUES ($1, $2, $3, now())",
                audio_id,
                content,
                mime,
            )
        return audio_id

    async def record_attempt(
        self,
        *,
        user_id: UUID,
        accept: bool,
        reason: str,
        similarity: float,
        spoof_prob: float,
        phrase_match: float,
        phrase_ok: bool,
        client_id: Optional[UUID] = None,
        challenge_id: Optional[UUID] = None,
        audio_id: Optional[UUID] = None,
        policy_id: Optional[str] = None,
        total_latency_ms: Optional[int] = None,
        inference_ms: Optional[int] = None,
        speaker_model_id: Optional[int] = None,
        antispoof_model_id: Optional[int] = None,
        asr_model_id: Optional[int] = None,
    ) -> UUID:
        attempt_id = uuid4()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO auth_attempt (
                        id, user_id, client_id, challenge_id, audio_id,
                        decided, accept, reason, policy_id, total_latency_ms, created_at, decided_at
                    ) VALUES ($1, $2, $3, $4, $5, TRUE, $6, $7, $8, $9, now(), now())
                    """,
                    attempt_id,
                    user_id,
                    client_id,
                    challenge_id,
                    audio_id,
                    accept,
                    reason,
                    policy_id,
                    total_latency_ms,
                )
                await conn.execute(
                    """
                    INSERT INTO scores (
                        attempt_id, similarity, spoof_prob, phrase_match, phrase_ok,
                        inference_ms, speaker_model_id, antispoof_model_id, asr_model_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    attempt_id,
                    similarity,
                    spoof_prob,
                    phrase_match,
                    phrase_ok,
                    inference_ms,
                    speaker_model_id,
                    antispoof_model_id,
                    asr_model_id,
                )
        return attempt_id

    async def get_history(self, user_id: UUID, limit: int = 50) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, a.created_at, a.accept, a.reason, a.policy_id, a.total_latency_ms,
                       s.similarity, s.spoof_prob, s.phrase_match, s.phrase_ok
                FROM auth_attempt a
                JOIN scores s ON s.attempt_id = a.id
                WHERE a.user_id = $1
                ORDER BY a.created_at DESC
                LIMIT $2
                """,
                user_id,
                limit,
            )
            return [dict(row) for row in rows]

    async def count_by_user(self, user_id: UUID) -> int:
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM auth_attempt WHERE user_id = $1", user_id
            )
            return int(count or 0)
