"""Tests de PostgresVoiceSignatureRepository contra la BD de pruebas.

Siguen el patrón de test_postgres_phrase_repository.py: usan el pool real
(voice_biometrics_test) y cada test corre en una transacción que se revierte.
"""

import uuid
from datetime import datetime, timezone

import numpy as np
import pytest

from src.domain.model.voice_signature import VoiceSignature
from src.infrastructure.persistence.postgres_voice_signature_repository import (
    PostgresVoiceSignatureRepository,
)
from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION


@pytest.fixture
def voice_repo(db_pool):
    return PostgresVoiceSignatureRepository(db_pool)


@pytest.fixture
async def user_in_tx(db_pool):
    """Crea un usuario en una conexión separada (visible para voice_repo) y lo limpia al final."""
    user_id = await db_pool.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        f"voice-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Voice", "Test", "user", "acme", "{}",
    )
    yield user_id
    # Limpieza: borrar voiceprints y voiceprint_history antes que el user (FK)
    await db_pool.execute("DELETE FROM voiceprint_history WHERE user_id = $1", user_id)
    await db_pool.execute("DELETE FROM voiceprint WHERE user_id = $1", user_id)
    await db_pool.execute('DELETE FROM "user" WHERE id = $1', user_id)


def _make_signature(user_id, speaker_model_id=None) -> VoiceSignature:
    embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    return VoiceSignature(
        id=uuid.uuid4(),
        user_id=user_id,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        speaker_model_id=speaker_model_id,
    )


@pytest.mark.asyncio
async def test_save_and_get_voiceprint_roundtrip(voice_repo, user_in_tx):
    """Guardar y recuperar un voiceprint preserva el embedding."""
    signature = _make_signature(user_in_tx, speaker_model_id=None)
    await voice_repo.save_voiceprint(signature)

    found = await voice_repo.get_voiceprint_by_user(user_in_tx)
    assert found is not None
    assert found.id == signature.id
    np.testing.assert_allclose(found.embedding, signature.embedding, atol=1e-6)


@pytest.mark.asyncio
async def test_update_voiceprint_persists_speaker_model_id(voice_repo, user_in_tx, db_pool):
    """El UPDATE de un voiceprint existente persiste speaker_model_id (bug corregido)."""
    # model_version es requisito de la FK de speaker_model_id
    model_version_tag = f"test-{uuid.uuid4().hex[:8]}"
    model_id = await db_pool.fetchval(
        "INSERT INTO model_version (kind, name, version) VALUES ('speaker', 'ecapa', $1) RETURNING id",
        model_version_tag,
    )
    try:
        original = _make_signature(user_in_tx)
        await voice_repo.save_voiceprint(original)

        updated = _make_signature(user_in_tx, speaker_model_id=model_id)
        await voice_repo.update_voiceprint(updated)

        found = await voice_repo.get_voiceprint_by_user(user_in_tx)
        assert found is not None
        assert found.speaker_model_id == model_id
        np.testing.assert_allclose(found.embedding, updated.embedding, atol=1e-6)
    finally:
        # Primero el voiceprint (FK) antes que model_version
        await db_pool.execute(
            "UPDATE voiceprint SET speaker_model_id = NULL WHERE speaker_model_id = $1", model_id
        )
        await db_pool.execute("DELETE FROM model_version WHERE id = $1", model_id)


@pytest.mark.asyncio
async def test_save_voiceprint_history_and_delete(voice_repo, user_in_tx):
    """Guardar historial y borrar el voiceprint activo."""
    signature = _make_signature(user_in_tx)
    await voice_repo.save_voiceprint(signature)
    await voice_repo.save_voiceprint_history(signature)

    history = await voice_repo.get_voiceprint_history(user_in_tx)
    assert len(history) == 1

    await voice_repo.delete_voiceprint(user_in_tx)
    assert await voice_repo.get_voiceprint_by_user(user_in_tx) is None
