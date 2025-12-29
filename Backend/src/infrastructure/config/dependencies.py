"""Dependency injection configuration with async initialization."""

import asyncpg
import os
import logging
import asyncio
from typing import Optional
from functools import lru_cache
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..persistence.PostgresPhraseRepository import (
    PostgresPhraseRepository,
    PostgresPhraseUsageRepository
)
from ...application.phrase_service import PhraseService

# Security for admin authentication
security = HTTPBearer()

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
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'voice_biometrics')
    db_user = os.getenv('DB_USER', 'voice_user')
    db_password = os.getenv('DB_PASSWORD', 'voice_password')
    
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
            timeout=10
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
                    "hint": "Run 'docker-compose up -d' to start the database."
                }
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
    
    from ..biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
    from ..biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
    from ..biometrics.ASRAdapter import ASRAdapter
    from ..biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade

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
        "ready": _db_initialized and _models_loaded
    }


# Legacy function for backwards compatibility
@lru_cache()
def create_voice_biometric_engine():
    """Create biometric engine (legacy, prefer init_biometric_engine_async)."""
    global _biometric_engine
    if _biometric_engine is None:
        init_biometric_engine()
    return _biometric_engine


from ...application.services.BiometricValidator import BiometricValidator

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
    from ..persistence.PostgresUserRepository import PostgresUserRepository
    pool = await get_db_pool()
    return PostgresUserRepository(pool)


async def get_audit_log_repository():
    """Get audit log repository instance."""
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    pool = await get_db_pool()
    return PostgresAuditLogRepository(pool)


async def get_enrollment_service():
    """Get enrollment service instance with dependencies."""
    from ..persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    from ...application.enrollment_service import EnrollmentService
    
    pool = await get_db_pool()
    
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    challenge_service = await get_challenge_service()
    biometric_validator = get_biometric_validator()
    
    return EnrollmentService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator
    )


async def get_voice_signature_repository():
    """Get voice signature repository instance."""
    from ..persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    pool = await get_db_pool()
    return PostgresVoiceSignatureRepository(pool)


async def get_verification_service():
    """Get verification service instance with dependencies."""
    from ..persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    from ...application.verification_service import VerificationService
    
    pool = await get_db_pool()
    
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    challenge_service = await get_challenge_service()
    biometric_validator = get_biometric_validator()
    
    return VerificationService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator,
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.60")),
        anti_spoofing_threshold=float(os.getenv("ANTI_SPOOFING_THRESHOLD", "0.5"))
    )


async def get_phrase_quality_rules_service():
    """Get phrase quality rules service instance with dependencies."""
    from ..persistence.PostgresPhraseQualityRulesRepository import PostgresPhraseQualityRulesRepository
    from ...application.phrase_quality_rules_service import PhraseQualityRulesService
    
    pool = await get_db_pool()
    rules_repo = PostgresPhraseQualityRulesRepository(pool)
    
    return PhraseQualityRulesService(rules_repo)


async def get_challenge_service():
    """Get challenge service instance with dependencies."""
    from ..persistence.PostgresChallengeRepository import PostgresChallengeRepository
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    from ...application.challenge_service import ChallengeService
    
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
        rules_service=rules_service
    )


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Dependency to ensure current user is an admin.
    Validates JWT token and checks for admin/superadmin role.
    """
    from fastapi import HTTPException, status
    from ...api.auth_controller import SECRET_KEY, ALGORITHM
    import jwt
    
    user_repo = await get_user_repository()
    
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise auth_error
    except jwt.PyJWTError:
        raise auth_error
    
    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise auth_error
    
    user_role = user.get("role", "user")
    if user_role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user
