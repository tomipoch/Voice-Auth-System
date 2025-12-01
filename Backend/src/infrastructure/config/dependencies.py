"""Dependency injection configuration for the application."""

import asyncpg
import os
import logging
from typing import Optional
from functools import lru_cache
from fastapi import HTTPException

from ..persistence.PostgresPhraseRepository import (
    PostgresPhraseRepository,
    PostgresPhraseUsageRepository
)
from ...application.phrase_service import PhraseService

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None
_connection_error: Optional[str] = None

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _db_pool, _connection_error
    
    if _db_pool is None:
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'voice_biometrics')
        db_user = os.getenv('DB_USER', 'voice_user')
        db_password = os.getenv('DB_PASSWORD', 'voice_password')
        
        try:
            logger.info(f"Attempting to connect to database at {db_host}:{db_port}")
            _db_pool = await asyncpg.create_pool(
                host=db_host,
                port=int(db_port),
                database=db_name,
                user=db_user,
                password=db_password,
                min_size=2,
                max_size=10,
                timeout=5
            )
            _connection_error = None
            logger.info("Database connection pool created successfully")
        except Exception as e:
            error_msg = f"Database unavailable: {str(e)}"
            logger.error(error_msg)
            _connection_error = error_msg
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Service Unavailable",
                    "message": "Database connection failed. Please ensure Docker is running and PostgreSQL is accessible.",
                    "hint": "Run 'docker-compose up -d' to start the database."
                }
            )
    
    return _db_pool


async def close_db_pool():
    """Close database connection pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


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


async def get_enrollment_service():
    """Get enrollment service instance with dependencies."""
    from ..persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    from ...application.enrollment_service import EnrollmentService
    
    pool = await get_db_pool()
    
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    phrase_repo = PostgresPhraseRepository(pool)
    phrase_usage_repo = PostgresPhraseUsageRepository(pool)
    biometric_validator = get_biometric_validator()
    
    return EnrollmentService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        phrase_repo=phrase_repo,
        phrase_usage_repo=phrase_usage_repo,
        biometric_validator=biometric_validator
    )


@lru_cache()
def create_voice_biometric_engine():
    """Create a singleton instance of the VoiceBiometricEngineFacade."""
    from ..biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
    from ..biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
    from ..biometrics.ASRAdapter import ASRAdapter
    from ..biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade

    speaker_adapter = SpeakerEmbeddingAdapter()
    spoof_adapter = SpoofDetectorAdapter()
    asr_adapter = ASRAdapter()

    return VoiceBiometricEngineFacade(
        speaker_adapter=speaker_adapter,
        spoof_adapter=spoof_adapter,
        asr_adapter=asr_adapter,
    )


def get_voice_biometric_engine():
    """Get voice biometric engine instance."""
    return create_voice_biometric_engine()


async def get_verification_service_v2():
    """Get verification service V2 instance with dependencies."""
    from ..persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    from ..persistence.PostgresAuditLogRepository import PostgresAuditLogRepository
    from ...application.verification_service_v2 import VerificationServiceV2
    
    pool = await get_db_pool()
    
    voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = await get_user_repository()
    audit_repo = PostgresAuditLogRepository(pool)
    phrase_repo = PostgresPhraseRepository(pool)
    phrase_usage_repo = PostgresPhraseUsageRepository(pool)
    biometric_validator = get_biometric_validator()
    
    return VerificationServiceV2(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        phrase_repo=phrase_repo,
        phrase_usage_repo=phrase_usage_repo,
        biometric_validator=biometric_validator,
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.60")),
        anti_spoofing_threshold=float(os.getenv("ANTI_SPOOFING_THRESHOLD", "0.5"))
    )
