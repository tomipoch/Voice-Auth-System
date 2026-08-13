"""Tests de PostgresVerificationAttemptRepository contra la BD de pruebas."""

import uuid

import pytest

from src.infrastructure.persistence.postgres_verification_attempt_repository import (
    PostgresVerificationAttemptRepository,
)


@pytest.fixture
def attempt_repo(db_pool):
    return PostgresVerificationAttemptRepository(db_pool)


@pytest.fixture
async def user_in_pool(db_pool):
    user_id = await db_pool.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
        """,
        f"attempt-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Attempt", "Test", "user", "acme", "{}",
    )
    yield user_id
    await db_pool.execute(
        "DELETE FROM auth_attempt WHERE user_id = $1", user_id
    )
    await db_pool.execute('DELETE FROM "user" WHERE id = $1', user_id)


@pytest.mark.asyncio
async def test_save_audio_blob_roundtrip(attempt_repo, db_pool):
    """Guardar un blob de audio devuelve un UUID persistido."""
    audio_id = await attempt_repo.save_audio_blob(b"RIFF-dummy-wav", "audio/wav")
    row = await db_pool.fetchrow("SELECT content, mime FROM audio_blob WHERE id = $1", audio_id)
    assert row is not None
    assert row["content"] == b"RIFF-dummy-wav"
    assert row["mime"] == "audio/wav"
    await db_pool.execute("DELETE FROM audio_blob WHERE id = $1", audio_id)


@pytest.mark.asyncio
async def test_record_attempt_persists_auth_attempt_and_scores(attempt_repo, user_in_pool, db_pool):
    """record_attempt escribe auth_attempt + scores y devuelve el id."""
    attempt_id = await attempt_repo.record_attempt(
        user_id=user_in_pool,
        accept=True,
        reason="ok",
        similarity=0.85,
        spoof_prob=0.02,
        phrase_match=0.95,
        phrase_ok=True,
        policy_id="single",
        total_latency_ms=120,
        speaker_model_id=None,
        antispoof_model_id=None,
        asr_model_id=None,
    )
    attempt = await db_pool.fetchrow(
        "SELECT decided, accept, reason, policy_id, total_latency_ms FROM auth_attempt WHERE id = $1",
        attempt_id,
    )
    assert attempt["decided"] is True
    assert attempt["accept"] is True
    assert attempt["reason"] == "ok"
    assert attempt["policy_id"] == "single"
    assert attempt["total_latency_ms"] == 120

    scores = await db_pool.fetchrow(
        "SELECT similarity, spoof_prob, phrase_match, phrase_ok FROM scores WHERE attempt_id = $1",
        attempt_id,
    )
    assert scores["similarity"] == pytest.approx(0.85)
    assert scores["spoof_prob"] == pytest.approx(0.02)
    assert scores["phrase_match"] == pytest.approx(0.95)
    assert scores["phrase_ok"] is True


@pytest.mark.asyncio
async def test_record_attempt_links_audio_and_challenge(attempt_repo, user_in_pool, db_pool):
    """audio_id y challenge_id quedan enlazados en auth_attempt."""
    audio_id = await attempt_repo.save_audio_blob(b"wav", "audio/wav")
    phrase_id = await db_pool.fetchval(
        """
        INSERT INTO phrase (text, source, word_count, char_count, language, difficulty, is_active, created_at)
        VALUES ($1, 'test', 5, 33, 'es', 'medium', TRUE, now()) RETURNING id
        """,
        "Frase de prueba para challenge del intento",
    )
    challenge = await db_pool.fetchval(
        "INSERT INTO challenge (user_id, phrase, phrase_id, expires_at) VALUES ($1, $2, $3, now() + interval '1 hour') RETURNING id",
        user_in_pool, "Frase de prueba para challenge del intento", phrase_id,
    )
    try:
        attempt_id = await attempt_repo.record_attempt(
            user_id=user_in_pool,
            accept=False,
            reason="low_similarity",
            similarity=0.3,
            spoof_prob=0.1,
            phrase_match=0.4,
            phrase_ok=False,
            audio_id=audio_id,
            challenge_id=challenge,
        )
        row = await db_pool.fetchrow(
            "SELECT audio_id, challenge_id FROM auth_attempt WHERE id = $1", attempt_id
        )
        assert row["audio_id"] == audio_id
        assert row["challenge_id"] == challenge
    finally:
        await db_pool.execute("DELETE FROM challenge WHERE id = $1", challenge)
        await db_pool.execute("DELETE FROM phrase WHERE id = $1", phrase_id)
        await db_pool.execute("DELETE FROM audio_blob WHERE id = $1", audio_id)


@pytest.mark.asyncio
async def test_get_history_and_count(attempt_repo, user_in_pool):
    """get_history ordena por recencia y count_by_user cuenta los intentos."""
    for i in range(3):
        await attempt_repo.record_attempt(
            user_id=user_in_pool,
            accept=(i % 2 == 0),
            reason="ok" if i % 2 == 0 else "low_similarity",
            similarity=0.9 - i * 0.1,
            spoof_prob=0.01,
            phrase_match=0.9,
            phrase_ok=True,
            policy_id="single",
        )
    history = await attempt_repo.get_history(user_in_pool, limit=10)
    assert len(history) == 3
    assert history[0]["accept"] is True
    assert history[0]["similarity"] == pytest.approx(0.7)
    assert await attempt_repo.count_by_user(user_in_pool) == 3
