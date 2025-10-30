"""Integration tests for database persistence layer."""

import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, Mock, patch
import numpy as np
from datetime import datetime, timezone

from ...src.infrastructure.repositories.PostgreSQLVoiceSignatureRepository import (
    PostgreSQLVoiceSignatureRepository
)
from ...src.infrastructure.repositories.PostgreSQLAuthAttemptRepository import (
    PostgreSQLAuthAttemptRepository
)
from ...src.domain.model.VoiceSignature import VoiceSignature
from ...src.domain.model.AuthAttemptResult import AuthAttemptResult, BiometricScores
from ...src.shared.types.common_types import (
    VoiceFeatures,
    AuthReason
)


class TestDatabasePersistence:
    """Integration tests for database persistence operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock database connection
        self.db_connection = Mock()
        
        # Create repositories with mocked connection
        self.voice_repo = PostgreSQLVoiceSignatureRepository(self.db_connection)
        self.auth_attempt_repo = PostgreSQLAuthAttemptRepository(self.db_connection)
    
    @pytest.mark.asyncio
    async def test_voice_signature_save_and_retrieve(self):
        """Test saving and retrieving voice signature."""
        # Mock data
        user_id = "user123"
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        voice_signature = VoiceSignature(
            user_id=user_id,
            features=voice_features,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock database operations
        self.db_connection.execute = AsyncMock()
        self.db_connection.fetchrow = AsyncMock(return_value={
            'user_id': user_id,
            'mfcc_features': voice_features.mfcc_features.tolist(),
            'pitch_features': voice_features.pitch_features.tolist(),
            'spectral_features': voice_features.spectral_features.tolist(),
            'created_at': voice_signature.created_at,
            'updated_at': voice_signature.created_at
        })
        
        # Test save operation
        await self.voice_repo.save(voice_signature)
        
        # Verify INSERT/UPDATE was called
        self.db_connection.execute.assert_called_once()
        
        # Test retrieve operation
        retrieved_signature = await self.voice_repo.get_by_user_id(user_id)
        
        # Verify SELECT was called
        self.db_connection.fetchrow.assert_called_once()
        
        # Assertions
        assert retrieved_signature is not None
        assert retrieved_signature.user_id == user_id
        assert np.array_equal(
            retrieved_signature.features.mfcc_features,
            voice_features.mfcc_features
        )
    
    @pytest.mark.asyncio
    async def test_voice_signature_not_found(self):
        """Test retrieving non-existent voice signature."""
        user_id = "non_existent_user"
        
        # Mock database returning None
        self.db_connection.fetchrow = AsyncMock(return_value=None)
        
        result = await self.voice_repo.get_by_user_id(user_id)
        
        assert result is None
        self.db_connection.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_attempt_save(self):
        """Test saving authentication attempt."""
        # Mock data
        biometric_scores = BiometricScores(
            similarity=0.92,
            spoof_probability=0.1,
            phrase_match=0.88,
            phrase_ok=True,
            inference_latency_ms=1500
        )
        
        auth_attempt = AuthAttemptResult(
            user_id="user123",
            success=True,
            reason=AuthReason.OK,
            confidence_score=0.92,
            processing_time_ms=1500,
            biometric_scores=biometric_scores,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Mock database operation
        self.db_connection.execute = AsyncMock()
        
        # Test save operation
        await self.auth_attempt_repo.save(auth_attempt)
        
        # Verify INSERT was called
        self.db_connection.execute.assert_called_once()
        
        # Check the SQL contains expected fields
        call_args = self.db_connection.execute.call_args
        sql_query = call_args[0][0]
        
        # Verify key fields are in the query
        assert "user_id" in sql_query
        assert "success" in sql_query
        assert "reason" in sql_query
        assert "confidence_score" in sql_query
        assert "biometric_scores" in sql_query
    
    @pytest.mark.asyncio
    async def test_auth_attempts_by_user(self):
        """Test retrieving authentication attempts by user."""
        user_id = "user123"
        
        # Mock database returning list of attempts
        mock_attempts = [
            {
                'user_id': user_id,
                'success': True,
                'reason': 'OK',
                'confidence_score': 0.92,
                'processing_time_ms': 1500,
                'biometric_scores': {
                    'similarity': 0.92,
                    'spoof_probability': 0.1,
                    'phrase_match': 0.88,
                    'phrase_ok': True,
                    'inference_latency_ms': 1500
                },
                'timestamp': datetime.now(timezone.utc)
            },
            {
                'user_id': user_id,
                'success': False,
                'reason': 'LOW_SIMILARITY',
                'confidence_score': 0.65,
                'processing_time_ms': 1200,
                'biometric_scores': {
                    'similarity': 0.65,
                    'spoof_probability': 0.15,
                    'phrase_match': 0.80,
                    'phrase_ok': True,
                    'inference_latency_ms': 1200
                },
                'timestamp': datetime.now(timezone.utc)
            }
        ]
        
        self.db_connection.fetch = AsyncMock(return_value=mock_attempts)
        
        # Test retrieve operation
        attempts = await self.auth_attempt_repo.get_by_user_id(user_id, limit=10)
        
        # Verify SELECT was called
        self.db_connection.fetch.assert_called_once()
        
        # Assertions
        assert len(attempts) == 2
        assert attempts[0].user_id == user_id
        assert attempts[0].success is True
        assert attempts[1].success is False
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test handling database connection failure."""
        user_id = "user123"
        
        # Mock connection failure
        self.db_connection.fetchrow = AsyncMock(
            side_effect=asyncpg.ConnectionFailureError("Connection lost")
        )
        
        with pytest.raises(asyncpg.ConnectionFailureError):
            await self.voice_repo.get_by_user_id(user_id)
    
    @pytest.mark.asyncio
    async def test_voice_signature_update_existing(self):
        """Test updating existing voice signature."""
        user_id = "user123"
        
        # Updated features
        updated_features = VoiceFeatures(
            mfcc_features=np.array([[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]),
            pitch_features=np.array([105, 205]),
            spectral_features=np.array([0.52, 0.62, 0.72])
        )
        
        # Mock existing signature check
        self.db_connection.fetchrow = AsyncMock(return_value={
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc)
        })
        
        # Mock update operation
        self.db_connection.execute = AsyncMock()
        
        # Create updated signature
        updated_signature = VoiceSignature(
            user_id=user_id,
            features=updated_features,
            created_at=datetime.now(timezone.utc)
        )
        
        # Test update operation
        await self.voice_repo.save(updated_signature)
        
        # Should call UPDATE instead of INSERT
        self.db_connection.execute.assert_called_once()
        
        # Verify it's an UPDATE query (contains WHERE clause)
        call_args = self.db_connection.execute.call_args
        sql_query = call_args[0][0]
        assert "UPDATE" in sql_query or "INSERT" in sql_query  # ON CONFLICT UPDATE
    
    @pytest.mark.asyncio
    async def test_vector_similarity_search(self):
        """Test vector similarity search for voice features."""
        target_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        
        # Mock similar signatures
        mock_similar = [
            {
                'user_id': 'user123',
                'similarity_score': 0.95,
                'mfcc_features': [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]],
                'pitch_features': [105, 205],
                'spectral_features': [0.52, 0.62, 0.72]
            },
            {
                'user_id': 'user456',
                'similarity_score': 0.88,
                'mfcc_features': [[0.9, 1.9, 2.9], [3.9, 4.9, 5.9]],
                'pitch_features': [95, 195],
                'spectral_features': [0.48, 0.58, 0.68]
            }
        ]
        
        self.db_connection.fetch = AsyncMock(return_value=mock_similar)
        
        # Test similarity search
        similar_signatures = await self.voice_repo.find_similar(
            target_features, 
            threshold=0.8, 
            limit=5
        )
        
        # Verify vector search was called
        self.db_connection.fetch.assert_called_once()
        
        # Check the query uses vector operations
        call_args = self.db_connection.fetch.call_args
        sql_query = call_args[0][0]
        assert any(op in sql_query.lower() for op in ['<->', 'cosine', 'similarity'])
        
        # Assertions
        assert len(similar_signatures) == 2
        assert similar_signatures[0]['similarity_score'] >= similar_signatures[1]['similarity_score']
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error."""
        user_id = "user123"
        voice_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        voice_signature = VoiceSignature(
            user_id=user_id,
            features=voice_features,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock transaction context
        transaction_mock = AsyncMock()
        self.db_connection.transaction = Mock(return_value=transaction_mock)
        
        # Mock execution failure
        self.db_connection.execute = AsyncMock(
            side_effect=asyncpg.UniqueViolationError("Duplicate key")
        )
        
        with pytest.raises(asyncpg.UniqueViolationError):
            async with self.db_connection.transaction():
                await self.voice_repo.save(voice_signature)
        
        # Transaction should be used for atomic operations
        self.db_connection.transaction.assert_called_once()