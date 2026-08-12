"""Integration tests for verification controller V2 endpoints - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestVerificationControllerV2:
    """Test suite for verification controller V2 endpoints."""
    
    def test_start_multi_phrase_verification_endpoint_exists(self, client):
        """Test that start-multi endpoint exists."""
        response = client.post(
            "/api/verification/start-multi",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium"
            }
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_verify_phrase_endpoint_exists(self, client):
        """Test that verify-phrase endpoint exists."""
        import io
        audio_data = b"fake audio data"
        files = {"audio_file": ("test.wav", io.BytesIO(audio_data), "audio/wav")}
        
        response = client.post(
            "/api/verification/verify-phrase",
            data={
                "verification_id": "550e8400-e29b-41d4-a716-446655440000",
                "phrase_id": "550e8400-e29b-41d4-a716-446655440001",
                "phrase_number": "1"
            },
            files=files
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_verification_history_endpoint_exists(self, client):
        """Test that verification history endpoint exists."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/verification/user/{user_id}/history?limit=5")
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
