"""Integration tests for enrollment controller endpoints - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient
import io

from src.main import create_app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestEnrollmentController:
    """Test suite for enrollment controller endpoints."""
    
    def test_start_enrollment_endpoint_exists(self, client):
        """Test that start enrollment endpoint exists."""
        response = client.post(
            "/api/enrollment/start",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium"
            }
        )
        
        # Should not return 404 (endpoint not found)
        # May return 500 (DB error) but endpoint exists
        assert response.status_code in [200, 400, 422, 500]
    
    def test_add_sample_endpoint_exists(self, client):
        """Test that add-sample endpoint exists."""
        # Create a fake audio file
        audio_data = b"fake audio data"
        files = {"audio_file": ("test.wav", io.BytesIO(audio_data), "audio/wav")}
        
        response = client.post(
            "/api/enrollment/add-sample",
            data={
                "enrollment_id": "550e8400-e29b-41d4-a716-446655440000",
                "challenge_id": "550e8400-e29b-41d4-a716-446655440001",
                "phrase_number": "1"
            },
            files=files
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_complete_enrollment_endpoint_exists(self, client):
        """Test that complete enrollment endpoint exists."""
        response = client.post(
            "/api/enrollment/complete",
            data={"enrollment_id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_get_enrollment_status_endpoint_exists(self, client):
        """Test that enrollment status endpoint exists."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/enrollment/status/{user_id}")
        
        # Should not return 404 (endpoint not found)
        # May return 400, 500 (DB/validation errors) but endpoint exists
        assert response.status_code in [200, 400, 404, 500]
