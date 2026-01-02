"""Unit tests for the EnrollmentService."""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
import numpy as np

from src.application.enrollment_service import EnrollmentService
from src.application.services.BiometricValidator import BiometricValidator
from src.domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from src.domain.repositories.UserRepositoryPort import UserRepositoryPort
from src.domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from src.domain.repositories.PhraseRepositoryPort import PhraseRepositoryPort, PhraseUsageRepositoryPort
from src.shared.types.common_types import VoiceEmbedding


@pytest.fixture
def mock_voice_repo():
    """Fixture for the VoiceSignatureRepositoryPort mock."""
    return Mock(spec=VoiceSignatureRepositoryPort)


@pytest.fixture
def mock_user_repo():
    """Fixture for the UserRepositoryPort mock."""
    return Mock(spec=UserRepositoryPort)


@pytest.fixture
def mock_audit_repo():
    """Fixture for the AuditLogRepositoryPort mock."""
    return Mock(spec=AuditLogRepositoryPort)


@pytest.fixture
def mock_phrase_repo():
    """Fixture for the PhraseRepositoryPort mock."""
    return Mock(spec=PhraseRepositoryPort)


@pytest.fixture
def mock_phrase_usage_repo():
    """Fixture for the PhraseUsageRepositoryPort mock."""
    return Mock(spec=PhraseUsageRepositoryPort)


@pytest.fixture
def mock_biometric_validator():
    """Fixture for the BiometricValidator mock."""
    return Mock(spec=BiometricValidator)


@pytest.fixture
def enrollment_service(
    mock_voice_repo,
    mock_user_repo,
    mock_audit_repo,
    mock_phrase_repo,
    mock_phrase_usage_repo,
    mock_biometric_validator,
):
    """Fixture for the EnrollmentService."""
    return EnrollmentService(
        voice_repo=mock_voice_repo,
        user_repo=mock_user_repo,
        audit_repo=mock_audit_repo,
        phrase_repo=mock_phrase_repo,
        phrase_usage_repo=mock_phrase_usage_repo,
        biometric_validator=mock_biometric_validator,
    )


@pytest.mark.asyncio
async def test_start_enrollment_new_user(enrollment_service: EnrollmentService, mock_user_repo, mock_phrase_repo):
    """Test starting enrollment for a new user."""
    user_id = uuid4()
    mock_user_repo.get_user_by_external_ref.return_value = None
    mock_user_repo.create_user.return_value = user_id
    mock_user_repo.user_exists.return_value = True
    mock_phrase_repo.find_random.return_value = [Mock(id=uuid4(), text="test phrase", difficulty="medium", word_count=3)] * 3

    result = await enrollment_service.start_enrollment(external_ref="test_ref")

    assert result["user_id"] == str(user_id)
    assert len(result["phrases"]) == 3


@pytest.mark.asyncio
async def test_add_enrollment_sample_invalid_embedding(enrollment_service: EnrollmentService, mock_biometric_validator):
    """Test adding an enrollment sample with an invalid embedding."""
    enrollment_id = uuid4()
    phrase_id = uuid4()
    enrollment_service._active_sessions[enrollment_id] = Mock(phrases=[{"id": str(phrase_id)}])
    mock_biometric_validator.is_valid_embedding.return_value = False

    with pytest.raises(ValueError, match="Invalid voice embedding"):
        await enrollment_service.add_enrollment_sample(
            enrollment_id=enrollment_id,
            phrase_id=phrase_id,
            embedding=np.random.rand(256).astype(np.float32),
        )


@pytest.mark.asyncio
async def test_complete_enrollment_insufficient_samples(enrollment_service: EnrollmentService):
    """Test completing enrollment with insufficient samples."""
    enrollment_id = uuid4()
    enrollment_service._active_sessions[enrollment_id] = Mock(samples_collected=1)

    with pytest.raises(ValueError, match="Insufficient samples"):
        await enrollment_service.complete_enrollment(enrollment_id)
