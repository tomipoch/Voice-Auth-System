"""Pytest configuration for integration tests."""

import asyncio

import pytest
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

# Import the FastAPI app
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.main import create_app

# Load environment variables from test.env
env_path = Path(__file__).parent.parent.parent / "test.env"
load_dotenv(env_path)


@pytest.fixture(autouse=True)
def reset_global_db_pool():
    """Cierra el pool global de asyncpg antes de cada test para evitar que
    conexiones abiertas en loops anteriores contaminen el siguiente test."""
    from src.infrastructure.config import dependencies as deps

    deps._db_pool = None
    deps._db_initialized = False
    deps._initialization_error = None

    yield


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client(event_loop) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.

    Function-scoped on purpose: pytest-asyncio gives every test
    its own event loop, and a session-scoped AsyncClient would
    pin the first file's loop for the rest of the session
    ("Future attached to a different loop" / asyncpg interface
    errors in files that run later). Fresh app + pool + singleton
    services per test also removes cross-test state.

    ASGITransport does not run the FastAPI lifespan by default,
    so the lifespan's TESTING branch (which wires the mock
    biometric engine into app.state and the module global) does
    not fire. Replicate that wire-up here so controllers that
    depend on get_voice_biometric_engine() receive the mock.

    EnrollmentService keeps active sessions in an in-memory dict
    that does not survive a fresh service instance per request;
    the dependency override below returns a singleton so the
    in-memory state is preserved across calls within one test.
    (Long-term the service should use its persistent
    enrollment_session_repo for the lookup, but that is a
    refactor outside Fase 8's scope.)
    """
    from src.main import MockVoiceBiometricEngineFacade
    from src.infrastructure.config import dependencies as deps
    from src.infrastructure.persistence.postgres_voice_signature_repository import (
        PostgresVoiceSignatureRepository,
    )
    from src.infrastructure.persistence.postgres_audit_log_repository import (
        PostgresAuditLogRepository,
    )
    from src.infrastructure.persistence.postgres_enrollment_session_repository import (
        PostgresEnrollmentSessionRepository,
    )
    from src.infrastructure.persistence.postgres_model_version_repository import (
        PostgresModelVersionRepository,
    )
    from src.application.enrollment_service import EnrollmentService
    from src.application.services.biometric_validator import BiometricValidator
    from src.application.challenge_service import ChallengeService

    app = create_app()
    mock_engine = MockVoiceBiometricEngineFacade()
    app.state.biometric_engine = mock_engine
    deps._biometric_engine = mock_engine
    deps._models_loaded = True

    # Session-scoped EnrollmentService singleton that preserves
    # in-memory session state across requests inside one test.
    pool = await deps.get_db_pool()
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await deps.get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    model_version_repo = PostgresModelVersionRepository(pool)
    enrollment_session_repo = PostgresEnrollmentSessionRepository(pool)
    challenge_service = ChallengeService(
        challenge_repo=deps._db_pool and None,  # placeholder; patched below
        phrase_repo=None,
        user_repo=user_repo,
        audit_repo=audit_repo,
        rules_service=None,
    )
    # Build the proper ChallengeService the same way the
    # production dependency does.
    from src.application.challenge_service import ChallengeService
    from src.infrastructure.persistence.postgres_challenge_repository import (
        PostgresChallengeRepository,
    )
    from src.infrastructure.persistence.postgres_phrase_repository import (
        PostgresPhraseRepository,
    )
    from src.application.phrase_quality_rules_service import (
        PhraseQualityRulesService,
    )
    from src.infrastructure.persistence.postgres_phrase_quality_rules_repository import (
        PostgresPhraseQualityRulesRepository,
    )

    challenge_service = ChallengeService(
        challenge_repo=PostgresChallengeRepository(pool),
        phrase_repo=PostgresPhraseRepository(pool),
        user_repo=user_repo,
        audit_repo=audit_repo,
        rules_service=PhraseQualityRulesService(
            PostgresPhraseQualityRulesRepository(pool)
        ),
    )
    singleton_enrollment = EnrollmentService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=BiometricValidator(),
        enrollment_session_repo=enrollment_session_repo,
    )

    def _override_get_enrollment_service():
        return singleton_enrollment

    app.dependency_overrides[deps.get_enrollment_service] = (
        _override_get_enrollment_service
    )

    # Same treatment for VerificationService (singleton across
    # requests in the smoke E2E; see note above on the
    # in-memory session-dict design).
    from src.application.verification_service import VerificationService

    singleton_verification = VerificationService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=BiometricValidator(),
        attempt_repo=None,
        model_version_repo=model_version_repo,
        phrase_repo=PostgresPhraseRepository(pool),
    )

    def _override_get_verification_service():
        return singleton_verification

    app.dependency_overrides[deps.get_verification_service] = (
        _override_get_verification_service
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def db_pool():
    """Fixture for a test database connection pool."""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "voice_biometrics_test")
    db_user = os.getenv("DB_USER", "voice_user")
    db_password = os.getenv("DB_PASSWORD", "voice_password")

    pool = await asyncpg.create_pool(
        host=db_host,
        port=int(db_port),
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5,
        timeout=5,
    )
    yield pool
    await pool.close()
