"""Integration tests for enrollment controller endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
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


class TestEnrollmentController:
    """Test suite for enrollment controller endpoints."""
    
    def test_start_enrollment_success(self, client, mock_user_id):
        """Test successful enrollment start."""
        # Arrange
        with patch('src.application.enrollment_service.EnrollmentService.start_enrollment') as mock_start:
            mock_start.return_value = {
                "enrollment_id": str(uuid4()),
                "user_id": mock_user_id,
                "challenges": [
                    {
                        "challenge_id": str(uuid4()),
                        "phrase": "Test phrase",
                        "phrase_id": str(uuid4()),
                        "difficulty": "medium"
                    }
                ],
                "required_samples": 3,
                "voiceprint_exists": False
            }
            
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
            assert "enrollment_id" in data
            assert len(data["challenges"]) > 0
    
    def test_start_enrollment_with_force_overwrite(self, client, mock_user_id):
        """Test enrollment start with force_overwrite=True."""
        # Arrange
        with patch('src.application.enrollment_service.EnrollmentService.start_enrollment') as mock_start:
            mock_start.return_value = {
                "enrollment_id": str(uuid4()),
                "user_id": mock_user_id,
                "challenges": [{"challenge_id": str(uuid4()), "phrase": "Test"}],
                "required_samples": 3,
                "voiceprint_exists": False
            }
            
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
            mock_start.assert_called_once()
            call_kwargs = mock_start.call_args[1]
            assert call_kwargs["force_overwrite"] is True
    
    def test_add_sample_success(self, client, mock_user_id, mock_audio_file):
        """Test successful sample addition."""
        # Arrange
        enrollment_id = str(uuid4())
        challenge_id = str(uuid4())
        
        with patch('src.application.enrollment_service.EnrollmentService.add_sample') as mock_add:
            mock_add.return_value = {
                "success": True,
                "samples_collected": 1,
                "samples_required": 3,
                "enrollment_complete": False
            }
            
            # Act
            response = client.post(
                "/api/enrollment/add-sample",
                data={
                    "enrollment_id": enrollment_id,
                    "challenge_id": challenge_id,
                    "phrase_number": "1"
                },
                files={"audio_file": mock_audio_file}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["samples_collected"] == 1
    
    def test_add_sample_invalid_challenge(self, client, mock_audio_file):
        """Test adding sample with invalid challenge_id."""
        # Arrange
        with patch('src.application.enrollment_service.EnrollmentService.add_sample') as mock_add:
            mock_add.side_effect = ValueError("Challenge does not belong to this enrollment session")
            
            # Act
            response = client.post(
                "/api/enrollment/add-sample",
                data={
                    "enrollment_id": str(uuid4()),
                    "challenge_id": str(uuid4()),
                    "phrase_number": "1"
                },
                files={"audio_file": mock_audio_file}
            )
            
            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
    
    def test_complete_enrollment_success(self, client):
        """Test successful enrollment completion."""
        # Arrange
        enrollment_id = str(uuid4())
        
        with patch('src.application.enrollment_service.EnrollmentService.complete_enrollment') as mock_complete:
            mock_complete.return_value = {
                "success": True,
                "voiceprint_id": str(uuid4()),
                "user_id": str(uuid4()),
                "samples_used": 3
            }
            
            # Act
            response = client.post(
                "/api/enrollment/complete",
                data={"enrollment_id": enrollment_id}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "voiceprint_id" in data
    
    def test_complete_enrollment_insufficient_samples(self, client):
        """Test enrollment completion with insufficient samples."""
        # Arrange
        with patch('src.application.enrollment_service.EnrollmentService.complete_enrollment') as mock_complete:
            mock_complete.side_effect = ValueError("Insufficient samples")
            
            # Act
            response = client.post(
                "/api/enrollment/complete",
                data={"enrollment_id": str(uuid4())}
            )
            
            # Assert
            assert response.status_code == 400
    
    def test_get_enrollment_status(self, client, mock_user_id):
        """Test getting enrollment status."""
        # Arrange
        with patch('src.application.enrollment_service.EnrollmentService.get_enrollment_status') as mock_status:
            mock_status.return_value = {
                "status": "in_progress",
                "samples_count": 2,
                "required_samples": 3
            }
            
            # Act
            response = client.get(f"/api/enrollment/status/{mock_user_id}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "in_progress"
            assert data["samples_count"] == 2
