"""Unit tests for Repository Pattern implementations."""

import pytest
from unittest.mock import Mock, AsyncMock
import numpy as np
from datetime import datetime, timezone

from src.domain.ports.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from src.domain.ports.AuthAttemptRepositoryPort import AuthAttemptRepositoryPort
from src.infrastructure.repositories.PostgreSQLVoiceSignatureRepository import (
    PostgreSQLVoiceSignatureRepository
)
from src.infrastructure.repositories.PostgreSQLAuthAttemptRepository import (
    PostgreSQLAuthAttemptRepository
)
from src.domain.model.VoiceSignature import VoiceSignature
from src.domain.model.AuthAttemptResult import AuthAttemptResult, BiometricScores
from src.shared.types.common_types import VoiceFeatures, AuthReason


class TestRepositoryPattern:
    """Test suite for Repository Pattern implementations."""
    
    def test_voice_signature_repository_interface(self):
        """Test voice signature repository implements the port interface."""
        # Mock database connection
        db_connection = Mock()
        
        # Create repository instance
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Verify it implements the port interface
        assert isinstance(repository, VoiceSignatureRepositoryPort)
        
        # Verify required methods exist
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'get_by_user_id')
        assert hasattr(repository, 'delete_by_user_id')
        assert hasattr(repository, 'find_similar')
    
    def test_auth_attempt_repository_interface(self):
        """Test auth attempt repository implements the port interface."""
        # Mock database connection
        db_connection = Mock()
        
        # Create repository instance
        repository = PostgreSQLAuthAttemptRepository(db_connection)
        
        # Verify it implements the port interface
        assert isinstance(repository, AuthAttemptRepositoryPort)
        
        # Verify required methods exist
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'get_by_user_id')
        assert hasattr(repository, 'get_failed_attempts')
        assert hasattr(repository, 'get_recent_attempts')
    
    @pytest.mark.asyncio
    async def test_voice_signature_repository_save_method(self):
        """Test voice signature repository save method."""
        # Mock database connection
        db_connection = Mock()
        db_connection.fetchrow = AsyncMock(return_value=None)  # No existing record
        db_connection.execute = AsyncMock()
        
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Create test data
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
        
        # Test save operation
        await repository.save(voice_signature)
        
        # Verify database operations were called
        db_connection.fetchrow.assert_called_once()
        db_connection.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_voice_signature_repository_get_by_user_id(self):
        """Test voice signature repository get_by_user_id method."""
        # Mock database connection
        db_connection = Mock()
        mock_row = {
            'user_id': 'user123',
            'mfcc_features': [[1, 2, 3], [4, 5, 6]],
            'pitch_features': [100, 200],
            'spectral_features': [0.5, 0.6, 0.7],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        db_connection.fetchrow = AsyncMock(return_value=mock_row)
        
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Test get operation
        result = await repository.get_by_user_id("user123")
        
        # Verify result
        assert result is not None
        assert result.user_id == "user123"
        assert isinstance(result.features, VoiceFeatures)
        
        # Verify database call
        db_connection.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_voice_signature_repository_delete_by_user_id(self):
        """Test voice signature repository delete_by_user_id method."""
        # Mock database connection
        db_connection = Mock()
        db_connection.execute = AsyncMock(return_value="DELETE 1")
        
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Test delete operation
        result = await repository.delete_by_user_id("user123")
        
        # Verify result
        assert result is True
        
        # Verify database call
        db_connection.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_voice_signature_repository_find_similar(self):
        """Test voice signature repository find_similar method."""
        # Mock database connection
        db_connection = Mock()
        mock_results = [
            {
                'user_id': 'user456',
                'similarity_score': 0.95,
                'mfcc_features': [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]],
                'pitch_features': [105, 205],
                'spectral_features': [0.52, 0.62, 0.72]
            }
        ]
        db_connection.fetch = AsyncMock(return_value=mock_results)
        
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Test similarity search
        target_features = VoiceFeatures(
            mfcc_features=np.array([[1, 2, 3], [4, 5, 6]]),
            pitch_features=np.array([100, 200]),
            spectral_features=np.array([0.5, 0.6, 0.7])
        )
        
        results = await repository.find_similar(target_features, threshold=0.8)
        
        # Verify results
        assert len(results) == 1
        assert results[0]['user_id'] == 'user456'
        assert results[0]['similarity_score'] == pytest.approx(0.95)
        
        # Verify database call
        db_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_attempt_repository_save_method(self):
        """Test auth attempt repository save method."""
        # Mock database connection
        db_connection = Mock()
        db_connection.execute = AsyncMock()
        
        repository = PostgreSQLAuthAttemptRepository(db_connection)
        
        # Create test data
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
        
        # Test save operation
        await repository.save(auth_attempt)
        
        # Verify database operation was called
        db_connection.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_attempt_repository_get_by_user_id(self):
        """Test auth attempt repository get_by_user_id method."""
        # Mock database connection
        db_connection = Mock()
        mock_attempts = [
            {
                'user_id': 'user123',
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
            }
        ]
        db_connection.fetch = AsyncMock(return_value=mock_attempts)
        
        repository = PostgreSQLAuthAttemptRepository(db_connection)
        
        # Test get operation
        results = await repository.get_by_user_id("user123", limit=10)
        
        # Verify results
        assert len(results) == 1
        assert results[0].user_id == "user123"
        assert results[0].success is True
        assert results[0].reason == AuthReason.OK
        
        # Verify database call
        db_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_attempt_repository_get_failed_attempts(self):
        """Test auth attempt repository get_failed_attempts method."""
        # Mock database connection
        db_connection = Mock()
        mock_failed_attempts = [
            {
                'user_id': 'user123',
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
        db_connection.fetch = AsyncMock(return_value=mock_failed_attempts)
        
        repository = PostgreSQLAuthAttemptRepository(db_connection)
        
        # Test get failed attempts
        results = await repository.get_failed_attempts("user123", hours=24)
        
        # Verify results
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].reason == AuthReason.LOW_SIMILARITY
        
        # Verify database call
        db_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_repository_dependency_injection(self):
        """Test repository dependency injection pattern."""
        # Mock database connection
        db_connection = Mock()
        
        # Create repositories
        voice_repo = PostgreSQLVoiceSignatureRepository(db_connection)
        auth_repo = PostgreSQLAuthAttemptRepository(db_connection)
        
        # Test that they can be used interchangeably through their ports
        def service_with_voice_repo(repo: VoiceSignatureRepositoryPort):
            return repo
        
        def service_with_auth_repo(repo: AuthAttemptRepositoryPort):
            return repo
        
        # These should work without type errors
        assert service_with_voice_repo(voice_repo) == voice_repo
        assert service_with_auth_repo(auth_repo) == auth_repo
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self):
        """Test repository error handling."""
        # Mock database connection with error
        db_connection = Mock()
        db_connection.fetchrow = AsyncMock(side_effect=Exception("Database error"))
        
        repository = PostgreSQLVoiceSignatureRepository(db_connection)
        
        # Test that database errors propagate
        with pytest.raises(Exception, match="Database error"):
            await repository.get_by_user_id("user123")
    
    def test_repository_initialization(self):
        """Test repository proper initialization."""
        db_connection = Mock()
        
        # Test voice signature repository
        voice_repo = PostgreSQLVoiceSignatureRepository(db_connection)
        assert voice_repo.db_connection == db_connection
        
        # Test auth attempt repository
        auth_repo = PostgreSQLAuthAttemptRepository(db_connection)
        assert auth_repo.db_connection == db_connection