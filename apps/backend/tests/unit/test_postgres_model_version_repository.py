"""Tests de PostgresModelVersionRepository contra la BD de pruebas."""

import uuid

import pytest

from src.infrastructure.persistence.postgres_model_version_repository import (
    PostgresModelVersionRepository,
)


@pytest.fixture
def model_repo(db_pool):
    return PostgresModelVersionRepository(db_pool)


@pytest.mark.asyncio
async def test_register_models_is_idempotent_and_returns_kind_map(model_repo, db_pool):
    """Registrar dos veces no duplica y devuelve un id por kind."""
    suffix = uuid.uuid4().hex[:8]
    models = [
        {"kind": "speaker", "name": "ecapa_tdnn", "version": f"test-{suffix}"},
        {"kind": "antispoof", "name": "aasist", "version": f"test-{suffix}"},
        {"kind": "antispoof", "name": "rawnet2", "version": f"test-{suffix}"},
        {"kind": "asr", "name": "wav2vec2_asr_es", "version": f"test-{suffix}"},
    ]
    try:
        first = await model_repo.register_models(models)
        second = await model_repo.register_models(models)
        assert first == second
        assert first["speaker"] == second["speaker"]
        assert first["antispoof"] == second["antispoof"]
        assert first["asr"] == second["asr"]
        assert await model_repo.get_model_id("speaker") == first["speaker"]
        assert await model_repo.get_model_id("missing_kind") is None
    finally:
        await db_pool.execute(
            "DELETE FROM model_version WHERE version = $1", f"test-{suffix}"
        )
