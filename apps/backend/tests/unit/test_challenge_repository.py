"""Unit tests for PostgresChallengeRepository."""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4

from src.infrastructure.persistence.PostgresChallengeRepository import PostgresChallengeRepository


@pytest.fixture
async def db_pool():
    """Create a test database connection pool."""
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='voice_biometrics_test',
        user='voice_user',
        password='voice_password',
        min_size=1,
        max_size=5
    )
    yield pool
    await pool.close()


@pytest.fixture
async def challenge_repo(db_pool):
    """Create a ChallengeRepository instance."""
    return PostgresChallengeRepository(db_pool)


@pytest.fixture
async def test_user_id(db_pool):
    """Create a test user and return its ID."""
    user_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO "user" (id, external_ref) VALUES ($1, $2)',
            user_id, f'test_user_{user_id}'
        )
    yield user_id
    # Cleanup
    async with db_pool.acquire() as conn:
        await conn.execute('DELETE FROM "user" WHERE id = $1', user_id)


@pytest.fixture
async def test_phrase_id(db_pool):
    """Create a test phrase and return its ID."""
    phrase_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute(
            '''
            INSERT INTO phrase (id, text, source, word_count, char_count, language, difficulty)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
            phrase_id, 'Test phrase', 'test', 2, 11, 'es', 'medium'
        )
    yield phrase_id
    # Cleanup
    async with db_pool.acquire() as conn:
        await conn.execute('DELETE FROM phrase WHERE id = $1', phrase_id)


class TestPostgresChallengeRepository:
    """Test suite for PostgresChallengeRepository."""
    
    @pytest.mark.asyncio
    async def test_create_challenge_with_phrase_id(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test creating a challenge with phrase reference."""
        phrase = "Test phrase"
        expires_at = datetime.now() + timedelta(minutes=5)
        
        challenge_id = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase=phrase,
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        assert challenge_id is not None
        
        # Verify challenge was created
        challenge = await challenge_repo.get_challenge(challenge_id)
        assert challenge is not None
        assert challenge['user_id'] == test_user_id
        assert challenge['phrase'] == phrase
        assert challenge['phrase_id'] == test_phrase_id
        assert challenge['used_at'] is None
        
        # Cleanup
        await challenge_repo._pool.execute('DELETE FROM challenge WHERE id = $1', challenge_id)
    
    @pytest.mark.asyncio
    async def test_get_active_challenge(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test getting the most recent active challenge for a user."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        # Create two challenges
        challenge_id_1 = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="First phrase",
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        challenge_id_2 = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="Second phrase",
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        # Get active challenge (should be the most recent)
        active = await challenge_repo.get_active_challenge(test_user_id)
        
        assert active is not None
        assert active['id'] == challenge_id_2
        assert active['phrase'] == "Second phrase"
        
        # Cleanup
        await challenge_repo._pool.execute(
            'DELETE FROM challenge WHERE id IN ($1, $2)',
            challenge_id_1, challenge_id_2
        )
    
    @pytest.mark.asyncio
    async def test_mark_challenge_used(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test marking a challenge as used."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        challenge_id = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="Test phrase",
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        # Mark as used
        await challenge_repo.mark_challenge_used(challenge_id)
        
        # Verify it was marked
        challenge = await challenge_repo.get_challenge(challenge_id)
        assert challenge['used_at'] is not None
        
        # Should no longer be active
        active = await challenge_repo.get_active_challenge(test_user_id)
        assert active is None
        
        # Cleanup
        await challenge_repo._pool.execute('DELETE FROM challenge WHERE id = $1', challenge_id)
    
    @pytest.mark.asyncio
    async def test_is_challenge_valid(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test challenge validity check."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        challenge_id = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="Test phrase",
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        # Should be valid
        is_valid = await challenge_repo.is_challenge_valid(challenge_id)
        assert is_valid is True
        
        # Mark as used
        await challenge_repo.mark_challenge_used(challenge_id)
        
        # Should no longer be valid
        is_valid = await challenge_repo.is_challenge_valid(challenge_id)
        assert is_valid is False
        
        # Cleanup
        await challenge_repo._pool.execute('DELETE FROM challenge WHERE id = $1', challenge_id)
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_challenges(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test cleanup of expired challenges."""
        # Create an expired challenge
        expired_time = datetime.now() - timedelta(hours=2)
        
        challenge_id = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="Expired phrase",
            phrase_id=test_phrase_id,
            expires_at=expired_time
        )
        
        # Run cleanup
        deleted_count = await challenge_repo.cleanup_expired_challenges(older_than_hours=1)
        
        assert deleted_count >= 1
        
        # Verify challenge was deleted
        challenge = await challenge_repo.get_challenge(challenge_id)
        assert challenge is None
    
    @pytest.mark.asyncio
    async def test_cleanup_used_challenges(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test cleanup of used challenges."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        challenge_id = await challenge_repo.create_challenge(
            user_id=test_user_id,
            phrase="Test phrase",
            phrase_id=test_phrase_id,
            expires_at=expires_at
        )
        
        # Mark as used
        await challenge_repo.mark_challenge_used(challenge_id)
        
        # Manually set used_at to 25 hours ago
        async with challenge_repo._pool.acquire() as conn:
            await conn.execute(
                'UPDATE challenge SET used_at = $1 WHERE id = $2',
                datetime.now() - timedelta(hours=25),
                challenge_id
            )
        
        # Run cleanup
        deleted_count = await challenge_repo.cleanup_used_challenges(older_than_hours=24)
        
        assert deleted_count >= 1
        
        # Verify challenge was deleted
        challenge = await challenge_repo.get_challenge(challenge_id)
        assert challenge is None
    
    @pytest.mark.asyncio
    async def test_count_active_challenges(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test counting active challenges for a user."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        # Create 3 challenges
        challenge_ids = []
        for i in range(3):
            challenge_id = await challenge_repo.create_challenge(
                user_id=test_user_id,
                phrase=f"Phrase {i}",
                phrase_id=test_phrase_id,
                expires_at=expires_at
            )
            challenge_ids.append(challenge_id)
        
        # Count should be 3
        count = await challenge_repo.count_active_challenges(test_user_id)
        assert count == 3
        
        # Mark one as used
        await challenge_repo.mark_challenge_used(challenge_ids[0])
        
        # Count should be 2
        count = await challenge_repo.count_active_challenges(test_user_id)
        assert count == 2
        
        # Cleanup
        await challenge_repo._pool.execute(
            'DELETE FROM challenge WHERE user_id = $1',
            test_user_id
        )
    
    @pytest.mark.asyncio
    async def test_count_recent_challenges(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test counting recent challenges for rate limiting."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        # Create 5 challenges
        for i in range(5):
            await challenge_repo.create_challenge(
                user_id=test_user_id,
                phrase=f"Phrase {i}",
                phrase_id=test_phrase_id,
                expires_at=expires_at
            )
        
        # Count challenges created in last hour
        count = await challenge_repo.count_recent_challenges(test_user_id, since_hours=1)
        assert count == 5
        
        # Cleanup
        await challenge_repo._pool.execute(
            'DELETE FROM challenge WHERE user_id = $1',
            test_user_id
        )
    
    @pytest.mark.asyncio
    async def test_get_challenges_batch(
        self, challenge_repo, test_user_id, test_phrase_id
    ):
        """Test getting multiple active challenges."""
        expires_at = datetime.now() + timedelta(minutes=5)
        
        # Create 5 challenges
        for i in range(5):
            await challenge_repo.create_challenge(
                user_id=test_user_id,
                phrase=f"Phrase {i}",
                phrase_id=test_phrase_id,
                expires_at=expires_at
            )
        
        # Get batch of 3
        challenges = await challenge_repo.get_challenges_batch(test_user_id, limit=3)
        
        assert len(challenges) == 3
        assert all(c['user_id'] == test_user_id for c in challenges)
        
        # Cleanup
        await challenge_repo._pool.execute(
            'DELETE FROM challenge WHERE user_id = $1',
            test_user_id
        )
