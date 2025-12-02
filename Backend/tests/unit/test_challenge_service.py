"""Unit tests for ChallengeService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from src.application.challenge_service import ChallengeService
from src.domain.model.Phrase import Phrase


@pytest.fixture
def mock_challenge_repo():
    """Create a mock ChallengeRepository."""
    repo = AsyncMock()
    repo.create_challenge = AsyncMock(return_value=uuid4())
    repo.get_challenge = AsyncMock()
    repo.mark_challenge_used = AsyncMock()
    repo.is_challenge_valid = AsyncMock(return_value=True)
    repo.count_active_challenges = AsyncMock(return_value=0)
    repo.count_recent_challenges = AsyncMock(return_value=0)
    repo.cleanup_expired_challenges = AsyncMock(return_value=5)
    repo.cleanup_used_challenges = AsyncMock(return_value=10)
    return repo


@pytest.fixture
def mock_phrase_repo():
    """Create a mock PhraseRepository."""
    repo = AsyncMock()
    
    # Create mock phrases
    phrases = [
        Phrase(
            id=uuid4(),
            text=f"Test phrase {i}",
            source="test",
            word_count=3,
            char_count=15,
            language="es",
            difficulty="medium",
            is_active=True,
            created_at=datetime.now()
        )
        for i in range(5)
    ]
    
    repo.get_random_phrases = AsyncMock(return_value=phrases[:3])
    repo.record_phrase_usage = AsyncMock()
    repo.get_recent_phrase_ids = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_user_repo():
    """Create a mock UserRepository."""
    repo = AsyncMock()
    repo.user_exists = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_audit_repo():
    """Create a mock AuditLogRepository."""
    repo = AsyncMock()
    repo.log_event = AsyncMock()
    return repo


@pytest.fixture
def mock_rules_service():
    """Create a mock PhraseQualityRulesService."""
    service = AsyncMock()
    service.get_rule_value = AsyncMock(side_effect=lambda rule, default: {
        'challenge_expiry_minutes': 5.0,
        'exclude_recent_phrases': 50.0,
        'max_challenges_per_user': 3.0,
        'max_challenges_per_hour': 20.0,
        'cleanup_expired_after_hours': 1.0,
        'cleanup_used_after_hours': 24.0,
        'min_success_rate': 0.70,
        'min_asr_score': 0.80,
        'min_phrase_ok_rate': 0.75,
        'min_attempts_for_analysis': 10.0
    }.get(rule, default))
    return service


@pytest.fixture
def challenge_service(
    mock_challenge_repo,
    mock_phrase_repo,
    mock_user_repo,
    mock_audit_repo,
    mock_rules_service
):
    """Create a ChallengeService instance with mocked dependencies."""
    return ChallengeService(
        challenge_repo=mock_challenge_repo,
        phrase_repo=mock_phrase_repo,
        user_repo=mock_user_repo,
        audit_repo=mock_audit_repo,
        rules_service=mock_rules_service
    )


class TestChallengeService:
    """Test suite for ChallengeService."""
    
    @pytest.mark.asyncio
    async def test_create_challenge(
        self, challenge_service, mock_challenge_repo, mock_phrase_repo
    ):
        """Test creating a single challenge."""
        user_id = uuid4()
        
        result = await challenge_service.create_challenge(
            user_id=user_id,
            difficulty="medium"
        )
        
        assert result is not None
        assert "challenge_id" in result
        assert "phrase" in result
        assert "phrase_id" in result
        assert "expires_at" in result
        
        # Verify challenge was created
        mock_challenge_repo.create_challenge.assert_called_once()
        mock_phrase_repo.record_phrase_usage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_challenge_batch(
        self, challenge_service, mock_challenge_repo, mock_phrase_repo
    ):
        """Test creating multiple challenges in batch."""
        user_id = uuid4()
        
        results = await challenge_service.create_challenge_batch(
            user_id=user_id,
            count=3,
            difficulty="medium"
        )
        
        assert len(results) == 3
        assert all("challenge_id" in r for r in results)
        assert all("phrase" in r for r in results)
        
        # Verify 3 challenges were created
        assert mock_challenge_repo.create_challenge.call_count == 3
        assert mock_phrase_repo.record_phrase_usage.call_count == 3
    
    @pytest.mark.asyncio
    async def test_validate_challenge_strict_success(
        self, challenge_service, mock_challenge_repo
    ):
        """Test strict challenge validation with valid challenge."""
        challenge_id = uuid4()
        user_id = uuid4()
        
        # Mock challenge data
        mock_challenge_repo.get_challenge.return_value = {
            'id': challenge_id,
            'user_id': user_id,
            'used_at': None,
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        assert is_valid is True
        assert reason == "Valid"
    
    @pytest.mark.asyncio
    async def test_validate_challenge_strict_not_found(
        self, challenge_service, mock_challenge_repo
    ):
        """Test strict validation with non-existent challenge."""
        challenge_id = uuid4()
        user_id = uuid4()
        
        mock_challenge_repo.get_challenge.return_value = None
        
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        assert is_valid is False
        assert reason == "Challenge not found"
    
    @pytest.mark.asyncio
    async def test_validate_challenge_strict_wrong_user(
        self, challenge_service, mock_challenge_repo
    ):
        """Test strict validation with wrong user."""
        challenge_id = uuid4()
        user_id = uuid4()
        wrong_user_id = uuid4()
        
        mock_challenge_repo.get_challenge.return_value = {
            'id': challenge_id,
            'user_id': wrong_user_id,
            'used_at': None,
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        assert is_valid is False
        assert reason == "Challenge does not belong to user"
    
    @pytest.mark.asyncio
    async def test_validate_challenge_strict_already_used(
        self, challenge_service, mock_challenge_repo
    ):
        """Test strict validation with already used challenge."""
        challenge_id = uuid4()
        user_id = uuid4()
        
        mock_challenge_repo.get_challenge.return_value = {
            'id': challenge_id,
            'user_id': user_id,
            'used_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        assert is_valid is False
        assert reason == "Challenge already used"
    
    @pytest.mark.asyncio
    async def test_validate_challenge_strict_expired(
        self, challenge_service, mock_challenge_repo
    ):
        """Test strict validation with expired challenge."""
        challenge_id = uuid4()
        user_id = uuid4()
        
        mock_challenge_repo.get_challenge.return_value = {
            'id': challenge_id,
            'user_id': user_id,
            'used_at': None,
            'expires_at': datetime.now() - timedelta(minutes=1)
        }
        
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        assert is_valid is False
        assert reason == "Challenge expired"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_max_active(
        self, challenge_service, mock_challenge_repo
    ):
        """Test rate limiting for max active challenges."""
        user_id = uuid4()
        
        # Mock 3 active challenges (at the limit)
        mock_challenge_repo.count_active_challenges.return_value = 3
        
        with pytest.raises(ValueError, match="too many active challenges"):
            await challenge_service.create_challenge(user_id=user_id)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_max_per_hour(
        self, challenge_service, mock_challenge_repo
    ):
        """Test rate limiting for challenges per hour."""
        user_id = uuid4()
        
        # Mock 20 challenges in last hour (at the limit)
        mock_challenge_repo.count_recent_challenges.return_value = 20
        
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            await challenge_service.create_challenge(user_id=user_id)
    
    @pytest.mark.asyncio
    async def test_mark_challenge_used(
        self, challenge_service, mock_challenge_repo
    ):
        """Test marking a challenge as used."""
        challenge_id = uuid4()
        
        await challenge_service.mark_challenge_used(challenge_id)
        
        mock_challenge_repo.mark_challenge_used.assert_called_once_with(challenge_id)
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_challenges(
        self, challenge_service, mock_challenge_repo, mock_audit_repo
    ):
        """Test cleanup of expired challenges."""
        deleted_count = await challenge_service.cleanup_expired_challenges()
        
        assert deleted_count == 5
        mock_challenge_repo.cleanup_expired_challenges.assert_called_once()
        mock_audit_repo.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_used_challenges(
        self, challenge_service, mock_challenge_repo, mock_audit_repo
    ):
        """Test cleanup of used challenges."""
        deleted_count = await challenge_service.cleanup_used_challenges()
        
        assert deleted_count == 10
        mock_challenge_repo.cleanup_used_challenges.assert_called_once()
        mock_audit_repo.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_phrase_performance(
        self, challenge_service, mock_rules_service
    ):
        """Test phrase performance analysis."""
        result = await challenge_service.analyze_phrase_performance()
        
        assert "analyzed" in result
        assert "disabled" in result
        assert "thresholds" in result
        assert result["thresholds"]["min_success_rate"] == 0.70
        assert result["thresholds"]["min_asr_score"] == 0.80
    
    @pytest.mark.asyncio
    async def test_create_challenge_batch_insufficient_phrases(
        self, challenge_service, mock_phrase_repo
    ):
        """Test batch creation with insufficient phrases."""
        user_id = uuid4()
        
        # Mock only 1 phrase available
        mock_phrase_repo.get_random_phrases.return_value = [
            Phrase(
                id=uuid4(),
                text="Only phrase",
                source="test",
                word_count=2,
                char_count=11,
                language="es",
                difficulty="medium",
                is_active=True,
                created_at=datetime.now()
            )
        ]
        
        # Should still work with fallback (allowing repetition)
        results = await challenge_service.create_challenge_batch(
            user_id=user_id,
            count=3
        )
        
        # Should have called get_random_phrases twice (once failed, once with fallback)
        assert mock_phrase_repo.get_random_phrases.call_count == 2
