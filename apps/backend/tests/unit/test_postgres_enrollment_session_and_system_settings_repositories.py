"""Tests de PostgresEnrollmentSessionRepository y PostgresSystemSettingsRepository."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.persistence.postgres_enrollment_session_repository import (
    PostgresEnrollmentSessionRepository,
)
from src.infrastructure.persistence.postgres_system_settings_repository import (
    PostgresSystemSettingsRepository,
)


@pytest.fixture
async def user_in_pool(db_pool):
    user_id = await db_pool.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
        """,
        f"session-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Session", "Test", "user", "acme", "{}",
    )
    yield user_id
    await db_pool.execute("DELETE FROM enrollment_session WHERE user_id = $1", user_id)
    await db_pool.execute('DELETE FROM "user" WHERE id = $1', user_id)


@pytest.mark.asyncio
async def test_enrollment_session_upsert_get_and_complete(db_pool, user_in_pool):
    repo = PostgresEnrollmentSessionRepository(db_pool)
    session_id = uuid.uuid4()
    challenges = [{"challenge_id": str(uuid.uuid4()), "phrase": "Frase de prueba"}]
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    await repo.upsert(session_id=session_id, user_id=user_in_pool, challenges=challenges,
                      samples_collected=1, challenge_index=1, expires_at=expires)

    stored = await repo.get_by_id(session_id)
    assert stored is not None
    assert stored["samples_collected"] == 1
    assert stored["challenges"] == challenges

    session_id2 = uuid.uuid4()
    await repo.upsert(session_id=session_id2, user_id=user_in_pool, challenges=[],
                      samples_collected=2, challenge_index=2, expires_at=expires)
    stored2 = await repo.get_by_user(user_in_pool)
    assert stored2["id"] == session_id2
    assert stored2["samples_collected"] == 2

    await repo.mark_completed(session_id2)
    assert await repo.get_by_id(session_id2) is None


@pytest.mark.asyncio
async def test_system_settings_get_set_roundtrip(db_pool):
    repo = PostgresSystemSettingsRepository(db_pool)
    key = f"test_key_{uuid.uuid4().hex[:8]}"
    await repo.set(key, {"enabled": True, "session_id": "abc"})
    value = await repo.get(key)
    assert value == {"enabled": True, "session_id": "abc"}
    await repo.set(key, {"enabled": False})
    assert (await repo.get(key)) == {"enabled": False}
    assert await repo.get("clave_inexistente") is None
    await db_pool.execute("DELETE FROM system_settings WHERE key = $1", key)
