"""Integration tests for voiceprint overwrite functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

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


@pytest.fixture
def mock_enrollment_data():
    """Create mock enrollment data."""
    return {
        "user_id": str(uuid4()),
        "difficulty": "medium",
        "force_overwrite": False
    }


class TestVoiceprintOverwrite:
    """Test suite for voiceprint overwrite functionality."""
    
    def test_enrollment_with_existing_voiceprint_no_force(self, client, mock_user_id):
        """
        Test enrollment when voiceprint exists and force_overwrite=False.
        Should return voiceprint_exists=True without creating enrollment.
        """
        # Arrange
        with patch('src.infrastructure.config.dependencies.get_voice_repository') as mock_repo:
            # Mock existing voiceprint
            mock_voice_repo = AsyncMock()
            mock_voice_repo.get_voiceprint_by_user.return_value = {
                "id": str(uuid4()),
                "user_id": mock_user_id,
                "created_at": datetime.now(timezone.utc)
            }
            mock_repo.return_value = mock_voice_repo
            
            # Act
            response = client.post(
                "/api/enrollment/start",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium",
                    "force_overwrite": "false"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["voiceprint_exists"] is True
            assert data["enrollment_id"] == ""
            assert len(data["challenges"]) == 0
            assert "already has a voiceprint" in data["message"]
    
    def test_enrollment_with_existing_voiceprint_force_true(self, client, mock_user_id):
        """
        Test enrollment when voiceprint exists and force_overwrite=True.
        Should delete old voiceprint and create new enrollment.
        """
        # Arrange
        with patch('src.infrastructure.config.dependencies.get_voice_repository') as mock_voice_repo, \
             patch('src.infrastructure.config.dependencies.get_challenge_service') as mock_challenge_service:
            
            # Mock existing voiceprint
            voice_repo = AsyncMock()
            voice_repo.get_voiceprint_by_user.return_value = {
                "id": str(uuid4()),
                "user_id": mock_user_id
            }
            voice_repo.delete_voiceprint.return_value = True
            mock_voice_repo.return_value = voice_repo
            
            # Mock challenge creation
            challenge_service = AsyncMock()
            challenge_service.create_challenge_batch.return_value = [
                {
                    "challenge_id": str(uuid4()),
                    "phrase": "Test phrase 1",
                    "phrase_id": str(uuid4()),
                    "difficulty": "medium"
                }
            ]
            mock_challenge_service.return_value = challenge_service
            
            # Act
            response = client.post(
                "/api/enrollment/start",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium",
                    "force_overwrite": "true"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["voiceprint_exists"] is False
            assert data["enrollment_id"] != ""
            assert len(data["challenges"]) > 0
            
            # Verify delete was called
            voice_repo.delete_voiceprint.assert_called_once_with(mock_user_id)
    
    def test_enrollment_without_existing_voiceprint(self, client, mock_user_id):
        """
        Test enrollment when no voiceprint exists.
        Should create enrollment normally.
        """
        # Arrange
        with patch('src.infrastructure.config.dependencies.get_voice_repository') as mock_voice_repo, \
             patch('src.infrastructure.config.dependencies.get_challenge_service') as mock_challenge_service:
            
            # Mock no existing voiceprint
            voice_repo = AsyncMock()
            voice_repo.get_voiceprint_by_user.return_value = None
            mock_voice_repo.return_value = voice_repo
            
            # Mock challenge creation
            challenge_service = AsyncMock()
            challenge_service.create_challenge_batch.return_value = [
                {
                    "challenge_id": str(uuid4()),
                    "phrase": "Test phrase 1",
                    "phrase_id": str(uuid4()),
                    "difficulty": "medium"
                }
            ]
            mock_challenge_service.return_value = challenge_service
            
            # Act
            response = client.post(
                "/api/enrollment/start",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data.get("voiceprint_exists", False) is False
            assert data["enrollment_id"] != ""
            assert len(data["challenges"]) > 0
    
    def test_force_overwrite_deletes_old_voiceprint(self, client, mock_user_id):
        """
        Test that force_overwrite actually deletes the old voiceprint.
        """
        # Arrange
        old_voiceprint_id = str(uuid4())
        
        with patch('src.infrastructure.config.dependencies.get_voice_repository') as mock_voice_repo:
            voice_repo = AsyncMock()
            voice_repo.get_voiceprint_by_user.return_value = {
                "id": old_voiceprint_id,
                "user_id": mock_user_id
            }
            voice_repo.delete_voiceprint.return_value = True
            mock_voice_repo.return_value = voice_repo
            
            # Act
            response = client.post(
                "/api/enrollment/start",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium",
                    "force_overwrite": "true"
                }
            )
            
            # Assert
            voice_repo.delete_voiceprint.assert_called_once()
            call_args = voice_repo.delete_voiceprint.call_args
            assert str(call_args[0][0]) == mock_user_id
