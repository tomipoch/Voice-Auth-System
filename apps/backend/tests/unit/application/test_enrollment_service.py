"""Unit tests for the EnrollmentService (rewritten in Fase 3 to match the
current constructor and behaviour)."""

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

from src.application.enrollment_service import EnrollmentService
from src.application.services.biometric_validator import BiometricValidator
from src.domain.repositories.voice_signature_repository_port import VoiceSignatureRepositoryPort
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.repositories.audit_log_repository_port import AuditLogRepositoryPort
from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION, MIN_ENROLLMENT_SAMPLES


def _make_service() -> tuple:
    voice_repo = MagicMock(spec=VoiceSignatureRepositoryPort)
    user_repo = MagicMock(spec=UserRepositoryPort)
    audit_repo = MagicMock(spec=AuditLogRepositoryPort)
    challenge_service = MagicMock()
    challenge_service.create_challenge_batch = AsyncMock(return_value=[
        {"challenge_id": uuid4(), "phrase": "hola mundo", "phrase_id": uuid4()}
        for _ in range(MIN_ENROLLMENT_SAMPLES)
    ])
    biometric_validator = MagicMock(spec=BiometricValidator)
    biometric_validator.is_valid_embedding = MagicMock(return_value=True)
    biometric_validator.validate_audio_quality = MagicMock(return_value={"is_valid": True, "snr_db": 20.0})
    session_repo = MagicMock()
    session_repo.upsert = AsyncMock()
    session_repo.mark_completed = AsyncMock()
    session_repo.get_by_id = AsyncMock(return_value=None)
    session_repo.get_by_user = AsyncMock(return_value=None)

    service = EnrollmentService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator,
        enrollment_session_repo=session_repo,
    )
    return service, voice_repo, user_repo, audit_repo, challenge_service, biometric_validator, session_repo


@pytest.mark.asyncio
async def test_start_enrollment_returns_challenges_for_existing_user():
    service, voice_repo, user_repo, audit_repo, challenge_service, _, session_repo = _make_service()
    user_id = uuid4()
    user_repo.user_exists = AsyncMock(return_value=True)
    user_repo.get_user = AsyncMock(return_value={"id": user_id, "email": "u@e.com", "role": "user"})
    voice_repo.get_voiceprint_by_user = AsyncMock(return_value=None)

    result = await service.start_enrollment(user_id=user_id, difficulty="medium")

    assert result["user_id"] == str(user_id)
    assert result["required_samples"] == MIN_ENROLLMENT_SAMPLES
    assert len(result["challenges"]) == MIN_ENROLLMENT_SAMPLES
    challenge_service.create_challenge_batch.assert_awaited_once()
    session_repo.upsert.assert_awaited_once()
    assert session_repo.upsert.await_args.kwargs["samples_collected"] == 0


@pytest.mark.asyncio
async def test_start_enrollment_raises_for_missing_user():
    service, _, user_repo, *_ = _make_service()
    user_repo.user_exists = AsyncMock(return_value=False)

    with pytest.raises(ValueError, match="does not exist"):
        await service.start_enrollment(user_id=uuid4())


@pytest.mark.asyncio
async def test_add_enrollment_sample_rejects_invalid_embedding():
    service, voice_repo, user_repo, audit_repo, challenge_service, biometric_validator, _ = _make_service()
    biometric_validator.is_valid_embedding = MagicMock(return_value=False)
    enrollment_id = uuid4()
    challenge_id = uuid4()
    from src.application.enrollment_service import EnrollmentSession
    session = EnrollmentSession(
        user_id=uuid4(),
        enrollment_id=enrollment_id,
        challenges=[{"challenge_id": str(challenge_id), "phrase": "x", "phrase_id": str(challenge_id)}],
    )
    service._active_sessions[enrollment_id] = session

    with pytest.raises(ValueError, match="Invalid voice embedding"):
        await service.add_enrollment_sample(
            enrollment_id=enrollment_id,
            challenge_id=challenge_id,
            embedding=np.random.rand(EMBEDDING_DIMENSION).astype(np.float32),
        )


@pytest.mark.asyncio
async def test_add_enrollment_sample_rejects_unknown_session():
    service, *_ = _make_service()
    with pytest.raises(ValueError, match="Invalid or expired"):
        await service.add_enrollment_sample(
            enrollment_id=uuid4(),
            challenge_id=uuid4(),
            embedding=np.random.rand(EMBEDDING_DIMENSION).astype(np.float32),
        )


@pytest.mark.asyncio
async def test_get_session_returns_active_session():
    service, *_ = _make_service()
    enrollment_id = uuid4()
    from src.application.enrollment_service import EnrollmentSession
    expected = EnrollmentSession(
        user_id=uuid4(),
        enrollment_id=enrollment_id,
        challenges=[{"challenge_id": str(uuid4())}],
    )
    service._active_sessions[enrollment_id] = expected
    assert await service.get_session(enrollment_id) is expected
    assert await service.get_session(uuid4()) is None


@pytest.mark.asyncio
async def test_get_session_recovers_from_repo():
    service, *_ = _make_service()
    enrollment_id = uuid4()
    service._session_repo.get_by_id = AsyncMock(return_value={
        "id": enrollment_id,
        "user_id": uuid4(),
        "challenges": [{"challenge_id": str(uuid4()), "phrase": "Frase de prueba"}],
        "samples_collected": 2,
        "challenge_index": 2,
    })
    session = await service.get_session(enrollment_id)
    assert session is not None
    assert session.samples_collected == 2
    assert await service.get_session(enrollment_id) is session


@pytest.mark.asyncio
async def test_complete_enrollment_marks_session_completed():
    service, voice_repo, _, _, _, _, session_repo = _make_service()
    user_id = uuid4()
    voice_repo.get_enrollment_samples = AsyncMock(return_value=[
        {"embedding": np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)}
        for _ in range(MIN_ENROLLMENT_SAMPLES)
    ])
    voice_repo.save_voiceprint = AsyncMock()
    voice_repo.save_voiceprint_history = AsyncMock()

    enrollment_id = uuid4()
    from src.application.enrollment_service import EnrollmentSession
    session = EnrollmentSession(
        user_id=user_id,
        enrollment_id=enrollment_id,
        challenges=[{"challenge_id": str(uuid4()), "phrase": "x", "phrase_id": str(uuid4())}
                    for _ in range(MIN_ENROLLMENT_SAMPLES)],
    )
    session.samples_collected = MIN_ENROLLMENT_SAMPLES
    service._active_sessions[enrollment_id] = session

    await service.complete_enrollment(enrollment_id=enrollment_id)
    session_repo.mark_completed.assert_awaited_once_with(enrollment_id)
