"""Unit tests for the dependency injection module.

Covers the pool state machine and the small singletons/helpers in
``src.infrastructure.config.dependencies``: idempotent initialization,
503 fallback on prior init failure, ``is_ready`` reporting, and the
``@lru_cache``-wrapped factories.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.application.services.biometric_validator import BiometricValidator
from src.infrastructure.config import dependencies as deps


@pytest.fixture(autouse=True)
def _reset_pool_state():
    """Reset module-level pool/biometric state around each test."""
    deps._db_pool = None
    deps._db_initialized = False
    deps._biometric_engine = None
    deps._models_loaded = False
    deps._initialization_error = None
    yield
    deps._db_pool = None
    deps._db_initialized = False
    deps._biometric_engine = None
    deps._models_loaded = False
    deps._initialization_error = None


class TestDbPool:
    @pytest.mark.asyncio
    async def test_init_db_pool_creates_pool(self, monkeypatch):
        fake_pool = MagicMock(name="pool")
        monkeypatch.setattr(
            deps,
            "asyncpg",
            MagicMock(create_pool=AsyncMock(return_value=fake_pool)),
        )
        pool = await deps.init_db_pool()
        assert pool is fake_pool
        assert deps._db_pool is fake_pool
        assert deps._db_initialized is True
        assert deps._initialization_error is None

    @pytest.mark.asyncio
    async def test_init_db_pool_is_idempotent(self, monkeypatch):
        first_pool = MagicMock(name="first")
        create_pool = AsyncMock(return_value=first_pool)
        monkeypatch.setattr(deps, "asyncpg", MagicMock(create_pool=create_pool))
        first = await deps.init_db_pool()
        second = await deps.init_db_pool()
        assert first is second
        assert create_pool.await_count == 1

    @pytest.mark.asyncio
    async def test_init_db_pool_records_error_on_failure(self, monkeypatch):
        create_pool = AsyncMock(side_effect=RuntimeError("connection refused"))
        monkeypatch.setattr(deps, "asyncpg", MagicMock(create_pool=create_pool))
        with pytest.raises(RuntimeError):
            await deps.init_db_pool()
        assert deps._db_pool is None
        assert deps._initialization_error == "connection refused"
        assert deps._db_initialized is False

    @pytest.mark.asyncio
    async def test_get_db_pool_returns_existing_pool(self):
        cached = MagicMock(name="cached")
        deps._db_pool = cached
        deps._db_initialized = True
        assert await deps.get_db_pool() is cached

    @pytest.mark.asyncio
    async def test_get_db_pool_raises_503_on_prior_init_failure(self):
        deps._initialization_error = "boom"
        with pytest.raises(HTTPException) as exc:
            await deps.get_db_pool()
        assert exc.value.status_code == 503
        assert "boom" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_get_db_pool_falls_back_to_init_when_uninitialized(self, monkeypatch):
        fake_pool = MagicMock(name="pool")
        create_pool = AsyncMock(return_value=fake_pool)
        monkeypatch.setattr(deps, "asyncpg", MagicMock(create_pool=create_pool))
        pool = await deps.get_db_pool()
        assert pool is fake_pool
        create_pool.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_db_pool_releases_resources(self):
        from unittest.mock import AsyncMock

        pool = MagicMock(name="pool")
        pool.close = AsyncMock()
        deps._db_pool = pool
        deps._db_initialized = True
        await deps.close_db_pool()
        assert deps._db_pool is None
        assert deps._db_initialized is False
        pool.close.assert_awaited_once()


class TestBiometricEngine:
    def test_get_voice_biometric_engine_returns_none_when_unset(self):
        assert deps.get_voice_biometric_engine() is None

    def test_is_ready_reports_pool_and_models_independently(self):
        assert deps.is_ready() == {
            "database": False,
            "models": False,
            "ready": False,
        }
        deps._db_initialized = True
        assert deps.is_ready() == {
            "database": True,
            "models": False,
            "ready": False,
        }
        deps._models_loaded = True
        assert deps.is_ready()["ready"] is True

    def test_lru_cache_makes_biometric_validator_a_singleton(self):
        deps.get_biometric_validator.cache_clear()
        first = deps.get_biometric_validator()
        second = deps.get_biometric_validator()
        assert first is second
        assert isinstance(first, BiometricValidator)
        deps.get_biometric_validator.cache_clear()


class TestRepositoryFactories:
    @pytest.mark.asyncio
    async def test_get_user_repository_wires_pool(self, monkeypatch):
        from src.infrastructure.persistence import (
            postgres_user_repository as mod,
        )

        fake_pool = MagicMock(name="pool")
        deps._db_pool = fake_pool
        ctor = MagicMock(return_value="user-repo")
        monkeypatch.setattr(mod, "PostgresUserRepository", ctor)
        result = await deps.get_user_repository()
        assert result == "user-repo"
        ctor.assert_called_once_with(fake_pool)

    @pytest.mark.asyncio
    async def test_get_audit_log_repository_wires_pool(self, monkeypatch):
        from src.infrastructure.persistence import (
            postgres_audit_log_repository as mod,
        )

        fake_pool = MagicMock(name="pool")
        deps._db_pool = fake_pool
        ctor = MagicMock(return_value="audit-repo")
        monkeypatch.setattr(mod, "PostgresAuditLogRepository", ctor)
        result = await deps.get_audit_log_repository()
        assert result == "audit-repo"
        ctor.assert_called_once_with(fake_pool)
