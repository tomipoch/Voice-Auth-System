"""Unit tests for VerificationService (rewritten in Fase 3)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from src.application.services.biometric_validator import BiometricValidator
from src.application.verification_service import VerificationService
from src.domain.repositories.audit_log_repository_port import AuditLogRepositoryPort
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.repositories.voice_signature_repository_port import VoiceSignatureRepositoryPort
from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION


def _make_service():
    voice_repo = MagicMock()
    user_repo = MagicMock()
    audit_repo = MagicMock()
    challenge_service = MagicMock()
    biometric_validator = MagicMock(spec=BiometricValidator)
    biometric_validator.is_valid_embedding = MagicMock(return_value=True)
    biometric_validator.calculate_similarity = MagicMock(return_value=0.85)
    # Pre-configure async methods on the repos so the service can await them.
    voice_repo.get_voiceprint_by_user = AsyncMock(return_value=None)
    user_repo.user_exists = AsyncMock(return_value=True)
    user_repo.get_user = AsyncMock(return_value={"id": uuid4(), "email": "u@e.com", "role": "user"})
    user_repo.get_user_policy = AsyncMock(return_value={"keep_audio": False})
    challenge_service.create_challenge = AsyncMock(return_value={
        "challenge_id": uuid4(),
        "phrase": "test phrase",
        "phrase_id": uuid4(),
        "expires_at": datetime.now(timezone.utc).isoformat(),
    })
    challenge_service.create_challenge_batch = AsyncMock(return_value=[
        {
            "challenge_id": uuid4(),
            "phrase": f"phrase {i}",
            "phrase_id": uuid4(),
            "expires_at": datetime.now(timezone.utc).isoformat(),
        }
        for i in range(3)
    ])
    challenge_service.validate_challenge_strict = AsyncMock(return_value=(True, "ok"))
    challenge_service.mark_challenge_used = AsyncMock(return_value=None)
    audit_repo.log_event = AsyncMock(return_value=None)
    audit_repo.get_user_activity = AsyncMock(return_value=[])
    attempt_repo = MagicMock()
    attempt_repo.save_audio_blob = AsyncMock(return_value=uuid4())
    attempt_repo.record_attempt = AsyncMock(return_value=uuid4())
    model_version_repo = MagicMock()
    model_version_repo.get_model_id = AsyncMock(return_value=1)

    service = VerificationService(
        voice_repo=voice_repo,
        user_repo=user_repo,
        audit_repo=audit_repo,
        challenge_service=challenge_service,
        biometric_validator=biometric_validator,
        attempt_repo=attempt_repo,
        model_version_repo=model_version_repo,
    )
    return service, voice_repo, user_repo, audit_repo, challenge_service, biometric_validator, attempt_repo, model_version_repo


def _embedding() -> np.ndarray:
    return np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)


class TestPhraseSimilarity:
    def test_identical(self):
        service, *_ = _make_service()
        assert service._calculate_phrase_similarity("hola mundo", "hola mundo") == 1.0

    def test_completely_different(self):
        service, *_ = _make_service()
        assert service._calculate_phrase_similarity("aaa", "bbb") == 0.0

    def test_partial(self):
        service, *_ = _make_service()
        score = service._calculate_phrase_similarity("hola mundo", "hola")
        assert 0.0 < score < 1.0


class TestPhraseMatchResult:
    def test_returns_zero_when_missing(self):
        service, *_ = _make_service()
        score, ok = service._get_phrase_match_result(None, "expected")
        assert score == 0.0
        assert ok is True

    def test_above_threshold_passes(self):
        service, *_ = _make_service()
        score, ok = service._get_phrase_match_result("hola mundo", "hola mundo")
        assert ok is True
        assert score > 0.7

    def test_below_threshold_fails(self):
        service, *_ = _make_service()
        # Use strings with low similarity
        score, ok = service._get_phrase_match_result("xyz", "abc def ghi")
        assert ok is False


class TestCompositeScore:
    def test_with_anti_spoofing(self):
        service, *_ = _make_service()
        score = service._calculate_composite_score(0.8, 0.2, 0.9)
        # 0.8*0.6 + (1-0.2)*0.2 + 0.9*0.2 = 0.48 + 0.16 + 0.18 = 0.82
        assert 0.81 <= score <= 0.83

    def test_without_anti_spoofing(self):
        service, *_ = _make_service()
        score = service._calculate_composite_score(0.8, None, 0.9)
        assert score > 0.6


class TestIsVerificationPassed:
    def test_passes_all(self):
        service, *_ = _make_service()
        assert service._is_verification_passed(0.85, True, True) is True

    def test_fails_low_similarity(self):
        service, *_ = _make_service()
        assert service._is_verification_passed(0.5, True, True) is False

    def test_fails_spoofing(self):
        service, *_ = _make_service()
        assert service._is_verification_passed(0.85, False, True) is False

    def test_fails_phrase_mismatch(self):
        service, *_ = _make_service()
        assert service._is_verification_passed(0.85, True, False) is False


class TestParseLogMetadata:
    def test_dict_passthrough(self):
        service, *_ = _make_service()
        assert service._parse_log_metadata({"a": 1}) == {"a": 1}

    def test_json_string(self):
        service, *_ = _make_service()
        assert service._parse_log_metadata('{"a": 1}') == {"a": 1}

    def test_invalid_json(self):
        service, *_ = _make_service()
        assert service._parse_log_metadata("not json") == {}

    def test_none(self):
        service, *_ = _make_service()
        assert service._parse_log_metadata(None) == {}


@pytest.mark.asyncio
class TestStartVerification:
    async def test_raises_for_missing_user(self):
        service, _, user_repo, *_ = _make_service()
        user_repo.user_exists = AsyncMock(return_value=False)
        with pytest.raises(ValueError, match="does not exist"):
            await service.start_verification(user_id=uuid4())

    async def test_raises_for_user_without_voiceprint(self):
        service, _, user_repo, voice_repo, *_ = _make_service()
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="not enrolled"):
            await service.start_verification(user_id=user_id)

    async def test_creates_challenge_and_session(self):
        service, voice_repo, user_repo, audit_repo, challenge_service, *_ = _make_service()
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))
        result = await service.start_verification(user_id=user_id, difficulty="medium")
        assert result["user_id"] == str(user_id)
        assert "challenge_id" in result
        challenge_service.create_challenge.assert_awaited_once()


@pytest.mark.asyncio
class TestQuickVerify:
    async def test_raises_for_missing_user(self):
        service, _, user_repo, *_ = _make_service()
        user_repo.user_exists = AsyncMock(return_value=False)
        with pytest.raises(ValueError, match="does not exist"):
            await service.quick_verify(user_id=uuid4(), embedding=_embedding())

    async def test_returns_verified_for_good_match(self):
        service, voice_repo, _, _, _, biometric_validator, *_ = _make_service()
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))
        biometric_validator.calculate_similarity = MagicMock(return_value=0.9)

        result = await service.quick_verify(user_id=user_id, embedding=_embedding())
        assert result["is_verified"] is True
        assert result["similarity_score"] == 0.9


class TestGetMultiSession:
    def test_returns_session_if_exists(self):
        service, *_ = _make_service()
        vid = uuid4()
        from src.application.verification_service import MultiPhraseVerificationSession
        session = MultiPhraseVerificationSession(user_id=uuid4(), verification_id=vid, challenges=[])
        service._active_multi_sessions[vid] = session
        assert service.get_multi_session(vid) is session

    def test_returns_none_if_missing(self):
        service, *_ = _make_service()
        assert service.get_multi_session(uuid4()) is None


@pytest.mark.asyncio
class TestPersistAttempt:
    async def test_quick_verify_records_attempt(self):
        service, voice_repo, _, _, _, _, attempt_repo, _ = _make_service()
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))

        await service.quick_verify(user_id=user_id, embedding=_embedding())
        attempt_repo.record_attempt.assert_awaited_once()
        kwargs = attempt_repo.record_attempt.await_args.kwargs
        assert kwargs["accept"] is True
        assert kwargs["reason"] == "ok"
        assert kwargs["policy_id"] == "quick"

    async def test_verify_voice_records_attempt_with_policy_single(self):
        service, voice_repo, user_repo, _, challenge_service, biometric_validator, attempt_repo, _ = _make_service()
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))
        biometric_validator.calculate_similarity = MagicMock(return_value=0.9)

        from src.application.verification_service import VerificationSession
        vid = uuid4()
        cid = uuid4()
        service._active_sessions[vid] = VerificationSession(
            user_id=user_id, verification_id=vid,
            challenge={"challenge_id": cid, "phrase": "hola"},
        )

        await service.verify_voice(
            verification_id=vid, challenge_id=cid, embedding=_embedding(),
            transcribed_text="hola", expected_phrase="hola",
        )
        attempt_repo.record_attempt.assert_awaited_once()
        kwargs = attempt_repo.record_attempt.await_args.kwargs
        assert kwargs["policy_id"] == "single"
        assert kwargs["accept"] is True

    async def test_keep_audio_true_persists_audio_blob(self):
        service, voice_repo, user_repo, _, _, _, attempt_repo, _ = _make_service()
        user_repo.get_user_policy = AsyncMock(return_value={"keep_audio": True})
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))

        await service.quick_verify(user_id=user_id, embedding=_embedding(), audio_bytes=b"RIFF-wav")
        attempt_repo.save_audio_blob.assert_awaited_once()
        kwargs = attempt_repo.record_attempt.await_args.kwargs
        assert kwargs["audio_id"] is not None

    async def test_keep_audio_false_skips_audio_blob(self):
        service, voice_repo, user_repo, _, _, _, attempt_repo, _ = _make_service()
        user_repo.get_user_policy = AsyncMock(return_value={"keep_audio": False})
        user_id = uuid4()
        voice_repo.get_voiceprint_by_user = AsyncMock(return_value=AsyncMock(embedding=[0.1] * EMBEDDING_DIMENSION))

        await service.quick_verify(user_id=user_id, embedding=_embedding(), audio_bytes=b"RIFF-wav")
        attempt_repo.save_audio_blob.assert_not_awaited()
        assert attempt_repo.record_attempt.await_args.kwargs["audio_id"] is None
