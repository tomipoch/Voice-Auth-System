"""Integration tests for challenge controller endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Create a mock user ID."""
    return str(uuid4())


class TestChallengeController:
    """Test suite for challenge controller endpoints."""
    
    def test_create_challenge(self, client, mock_user_id):
        """Test creating a single challenge."""
        # Arrange
        with patch('src.application.challenge_service.ChallengeService.create_challenge') as mock_create:
            mock_create.return_value = {
                "challenge_id": str(uuid4()),
                "user_id": mock_user_id,
                "phrase": "Test phrase",
                "phrase_id": str(uuid4()),
                "difficulty": "medium",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
            }
            
            # Act
            response = client.post(
                "/api/challenges/create",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "challenge" in data
            assert data["challenge"]["user_id"] == mock_user_id
    
    def test_create_challenge_batch(self, client, mock_user_id):
        """Test creating multiple challenges in batch."""
        # Arrange
        with patch('src.application.challenge_service.ChallengeService.create_challenge_batch') as mock_batch:
            mock_batch.return_value = [
                {
                    "challenge_id": str(uuid4()),
                    "phrase": f"Test phrase {i}",
                    "phrase_id": str(uuid4()),
                    "difficulty": "medium"
                }
                for i in range(3)
            ]
            
            # Act
            response = client.post(
                "/api/challenges/create-batch",
                data={
                    "user_id": mock_user_id,
                    "count": "3",
                    "difficulty": "medium"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["challenges"]) == 3
            assert data["count"] == 3
    
    def test_get_challenge(self, client):
        """Test getting a specific challenge by ID."""
        # Arrange
        challenge_id = str(uuid4())
        
        with patch('src.application.challenge_service.ChallengeService.get_challenge') as mock_get:
            mock_get.return_value = {
                "challenge_id": challenge_id,
                "phrase": "Test phrase",
                "difficulty": "medium",
                "used": False
            }
            
            # Act
            response = client.get(f"/api/challenges/{challenge_id}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["challenge"]["challenge_id"] == challenge_id
    
    def test_validate_challenge(self, client, mock_user_id):
        """Test validating a challenge."""
        # Arrange
        challenge_id = str(uuid4())
        
        with patch('src.application.challenge_service.ChallengeService.validate_challenge_strict') as mock_validate:
            mock_validate.return_value = (True, "Challenge is valid")
            
            # Act
            response = client.post(
                "/api/challenges/validate",
                data={
                    "challenge_id": challenge_id,
                    "user_id": mock_user_id
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_valid"] is True
    
    def test_cleanup_expired_challenges(self, client):
        """Test cleanup of expired challenges."""
        # Arrange
        with patch('src.application.challenge_service.ChallengeService.cleanup_expired_challenges') as mock_cleanup:
            mock_cleanup.return_value = 5  # 5 challenges deleted
            
            # Act
            response = client.post("/api/challenges/cleanup")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["deleted_count"] == 5
    
    def test_get_active_challenge(self, client, mock_user_id):
        """Test getting active challenge for a user."""
        # Arrange
        with patch('src.application.challenge_service.ChallengeService.get_active_challenge') as mock_active:
            mock_active.return_value = {
                "challenge_id": str(uuid4()),
                "phrase": "Active test phrase",
                "difficulty": "medium"
            }
            
            # Act
            response = client.get(f"/api/challenges/user/{mock_user_id}/active")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["challenge"] is not None
