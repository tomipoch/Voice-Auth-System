"""Dependency injection configuration with async initialization."""

import asyncio
import logging
import os
from functools import lru_cache
from typing import Optional

import asyncpg
from fastapi import HTTPException

from ...application.phrase_service import PhraseService
from ...config import ANTI_SPOOFING_THRESHOLD, SIMILARITY_THRESHOLD
from ..persistence.postgres_phrase_repository import (
    PostgresPhraseRepository,
    PostgresPhraseUsageRepository,
)

logger = logging.getLogger(__name__)

# Global connection pool and state
_db_pool: Optional[asyncpg.Pool] = None
_db_initialized: bool = False
_biometric_engine = None
_models_loaded: bool = False
_initialization_error: Optional[str] = None


async def init_db_pool() -> asyncpg.Pool:
    """Initialize database connection pool during startup. Call this from lifespan."""
    global _db_pool, _db_initialized, _initialization_error

    if _db_pool is not None:
        return _db_pool

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "voice_biometrics")
    db_user = os.getenv("DB_USER", "voice_user")
    db_password = os.getenv("DB_PASSWORD", "voice_password")

    try:
        logger.info(f"Initializing database pool: {db_host}:{db_port}/{db_name}")
        _db_pool = await asyncpg.create_pool(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password,
            min_size=2,
            max_size=10,
            timeout=10,
        )
        _db_initialized = True
        _initialization_error = None
        logger.info("✅ Database pool initialized successfully")
        return _db_pool
    except Exception as e:
        _initialization_error = str(e)
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool. Raises if not initialized."""
    global _db_pool, _initialization_error

    if _db_pool is None:
        if _initialization_error:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Service Unavailable",
                    "message": f"Database not available: {_initialization_error}",
                    "hint": "Run 'docker-compose up -d' to start the database.",
                },
            )
        # Fallback: try to initialize (for backwards compatibility)
        return await init_db_pool()

    return _db_pool


async def close_db_pool():
    """Close database connection pool."""
    global _db_pool, _db_initialized
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        _db_initialized = False
        logger.info("Database pool closed")


def init_biometric_engine():
    """Initialize biometric engine synchronously (called in background task)."""
    global _biometric_engine, _models_loaded

    from ..biometrics.asr_adapter import ASRAdapter
    from ..biometrics.speaker_embedding_adapter import SpeakerEmbeddingAdapter
    from ..biometrics.spoof_detector_adapter import SpoofDetectorAdapter
    from ..biometrics.voice_biometric_engine_facade import VoiceBiometricEngineFacade

    logger.info("Loading ML models (this may take a moment)...")

    speaker_adapter = SpeakerEmbeddingAdapter()
    spoof_adapter = SpoofDetectorAdapter()
    asr_adapter = ASRAdapter()

    _biometric_engine = VoiceBiometricEngineFacade(
        speaker_adapter=speaker_adapter,
        spoof_adapter=spoof_adapter,
        asr_adapter=asr_adapter,
    )
    _models_loaded = True
    logger.info("✅ ML models loaded successfully")
    return _biometric_engine


async def init_biometric_engine_async():
    """Initialize biometric engine in background thread to not block startup."""
    global _biometric_engine, _models_loaded

    loop = asyncio.get_event_loop()
    _biometric_engine = await loop.run_in_executor(None, init_biometric_engine)
    return _biometric_engine


def get_voice_biometric_engine():
    """Get biometric engine instance. May return None if still loading."""
    global _biometric_engine
    return _biometric_engine


def is_ready() -> dict:
    """Check if all services are initialized and ready."""
    return {
        "database": _db_initialized,
        "models": _models_loaded,
        "ready": _db_initialized and _models_loaded,
    }


# Legacy function for backwards compatibility
@lru_cache()
def create_voice_biometric_engine():
    """Create biometric engine (legacy, prefer init_biometric_engine_async)."""
    global _biometric_engine
    if _biometric_engine is None:
        init_biometric_engine()
    return _biometric_engine


from ...application.services.biometric_validator import BiometricValidator


@lru_cache()
def get_biometric_validator() -> BiometricValidator:
    """Get a singleton instance of the BiometricValidator."""
    return BiometricValidator()


async def get_phrase_service() -> PhraseService:
    """Get phrase service instance with dependencies."""
    pool = await get_db_pool()
    phrase_repo = PostgresPhraseRepository(pool)
    usage_repo = PostgresPhraseUsageRepository(pool)
    return PhraseService(phrase_repo, usage_repo)


async def get_user_repository():
    """Get user repository instance."""
    from ..persistence.postgres_user_repository import PostgresUserRepository

    pool = await get_db_pool()
    return PostgresUserRepository(pool)


async def get_audit_log_repository():
    """Get audit log repository instance."""
    from ..persistence.postgres_audit_log_repository import PostgresAuditLogRepository

    pool = await get_db_pool()
    return PostgresAuditLogRepository(pool)


async def get_enrollment_service():
    """Get enrollment service instance with dependencies."""
    from ...application.enrollment_service import EnrollmentService
    from ..persistence.postgres_audit_log_repository import PostgresAuditLogRepository
    from ..persistence.postgres_enrollment_session_repository import (
        PostgresEnrollmentSessionRepository,
    )
    from ..persistence.postgres_voice_signature_repository import (
        PostgresVoiceSignatureRepository,
    )

    pool = await get_db_pool()

    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    enrollment_session_repo = PostgresEnrollmentSessionRepository(pool)
    challenge_service = await get_challenge_service()
    biometric_validator = get_biometric_validator()

    return EnrollmentService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator,
        enrollment_session_repo=enrollment_session_repo,
    )


async def get_voice_signature_repository():
    """Get voice signature repository instance."""
    from ..persistence.postgres_voice_signature_repository import (
        PostgresVoiceSignatureRepository,
    )

    pool = await get_db_pool()
    return PostgresVoiceSignatureRepository(pool)


async def get_verification_service():
    """Get verification service instance with dependencies."""
    from ...application.verification_service import VerificationService
    from ..persistence.postgres_audit_log_repository import PostgresAuditLogRepository
    from ..persistence.postgres_model_version_repository import (
        PostgresModelVersionRepository,
    )
    from ..persistence.postgres_phrase_repository import PostgresPhraseRepository
    from ..persistence.postgres_verification_attempt_repository import (
        PostgresVerificationAttemptRepository,
    )
    from ..persistence.postgres_voice_signature_repository import (
        PostgresVoiceSignatureRepository,
    )

    pool = await get_db_pool()

    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    attempt_repo = PostgresVerificationAttemptRepository(pool)
    model_version_repo = PostgresModelVersionRepository(pool)
    phrase_repo = PostgresPhraseRepository(pool)
    challenge_service = await get_challenge_service()
    biometric_validator = get_biometric_validator()

    return VerificationService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator,
        attempt_repo=attempt_repo,
        model_version_repo=model_version_repo,
        phrase_repo=phrase_repo,
        similarity_threshold=SIMILARITY_THRESHOLD,
        anti_spoofing_threshold=ANTI_SPOOFING_THRESHOLD,
    )


async def get_phrase_quality_rules_service():
    """Get phrase quality rules service instance with dependencies."""
    from ...application.phrase_quality_rules_service import PhraseQualityRulesService
    from ..persistence.postgres_phrase_quality_rules_repository import (
        PostgresPhraseQualityRulesRepository,
    )

    pool = await get_db_pool()
    rules_repo = PostgresPhraseQualityRulesRepository(pool)

    return PhraseQualityRulesService(rules_repo)


async def get_system_settings_repository():
    """Get system settings repository instance."""
    from ..persistence.postgres_system_settings_repository import (
        PostgresSystemSettingsRepository,
    )

    pool = await get_db_pool()
    return PostgresSystemSettingsRepository(pool)


async def get_client_app_repository():
    """Get client app repository instance."""
    from ..persistence.postgres_client_app_repository import PostgresClientAppRepository

    pool = await get_db_pool()
    return PostgresClientAppRepository(pool)


async def get_challenge_service():
    """Get challenge service instance with dependencies."""
    from ...application.challenge_service import ChallengeService
    from ..persistence.postgres_audit_log_repository import PostgresAuditLogRepository
    from ..persistence.postgres_challenge_repository import PostgresChallengeRepository

    pool = await get_db_pool()

    challenge_repo = PostgresChallengeRepository(pool)
    phrase_repo = PostgresPhraseRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    rules_service = await get_phrase_quality_rules_service()

    return ChallengeService(
        challenge_repo=challenge_repo,
        phrase_repo=phrase_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        rules_service=rules_service,
    )
