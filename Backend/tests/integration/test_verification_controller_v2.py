"""Integration tests for verification controller V2 endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import io

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
def mock_audio_file():
    """Create a mock audio file."""
    audio_data = b"fake audio data"
    return ("test_audio.wav", io.BytesIO(audio_data), "audio/wav")


class TestVerificationControllerV2:
    """Test suite for verification controller V2 endpoints."""
    
    def test_start_multi_phrase_verification(self, client, mock_user_id):
        """Test starting multi-phrase verification."""
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.start_multi_phrase_verification') as mock_start:
            mock_start.return_value = {
                "verification_id": str(uuid4()),
                "user_id": mock_user_id,
                "challenges": [
                    {
                        "challenge_id": str(uuid4()),
                        "phrase": "Test phrase 1",
                        "phrase_id": str(uuid4()),
                        "difficulty": "medium"
                    },
                    {
                        "challenge_id": str(uuid4()),
                        "phrase": "Test phrase 2",
                        "phrase_id": str(uuid4()),
                        "difficulty": "medium"
                    },
                    {
                        "challenge_id": str(uuid4()),
                        "phrase": "Test phrase 3",
                        "phrase_id": str(uuid4()),
                        "difficulty": "medium"
                    }
                ],
                "required_phrases": 3
            }
            
            # Act
            response = client.post(
                "/api/verification/start-multi",
                data={
                    "user_id": mock_user_id,
                    "difficulty": "medium"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "verification_id" in data
            assert len(data["challenges"]) == 3
    
    def test_verify_phrase_success(self, client, mock_audio_file):
        """Test successful phrase verification."""
        # Arrange
        verification_id = str(uuid4())
        phrase_id = str(uuid4())
        
        with patch('src.application.verification_service_v2.VerificationServiceV2.verify_phrase') as mock_verify:
            mock_verify.return_value = {
                "success": True,
                "phrase_verified": True,
                "similarity_score": 0.92,
                "anti_spoofing_score": 0.95,
                "phrase_match": True,
                "phrases_completed": 1,
                "phrases_required": 3,
                "verification_complete": False
            }
            
            # Act
            response = client.post(
                "/api/verification/verify-phrase",
                data={
                    "verification_id": verification_id,
                    "phrase_id": phrase_id,
                    "phrase_number": "1"
                },
                files={"audio_file": mock_audio_file}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["phrase_verified"] is True
            assert data["similarity_score"] >= 0.9
    
    def test_verify_phrase_invalid_challenge(self, client, mock_audio_file):
        """Test phrase verification with invalid challenge_id."""
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.verify_phrase') as mock_verify:
            mock_verify.side_effect = ValueError("Challenge does not belong to this verification session")
            
            # Act
            response = client.post(
                "/api/verification/verify-phrase",
                data={
                    "verification_id": str(uuid4()),
                    "phrase_id": str(uuid4()),
                    "phrase_number": "1"
                },
                files={"audio_file": mock_audio_file}
            )
            
            # Assert
            assert response.status_code in [400, 500]
            data = response.json()
            assert "detail" in data
    
    def test_get_verification_history(self, client, mock_user_id):
        """Test getting verification history."""
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.get_verification_history') as mock_history:
            mock_history.return_value = [
                {
                    "verification_id": str(uuid4()),
                    "timestamp": "2024-01-01T12:00:00Z",
                    "success": True,
                    "similarity_score": 0.92
                }
            ]
            
            # Act
            response = client.get(f"/api/verification/user/{mock_user_id}/history?limit=5")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["history"], list)
    
    def test_start_verification_user_not_enrolled(self, client, mock_user_id):
        """Test starting verification for user who is not enrolled."""
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.start_multi_phrase_verification') as mock_start:
            mock_start.side_effect = ValueError("User is not enrolled")
            
            # Act
            response = client.post(
                "/api/verification/start-multi",
                data={"user_id": mock_user_id}
            )
            
            # Assert
            assert response.status_code in [400, 404]
            data = response.json()
            assert "detail" in data
