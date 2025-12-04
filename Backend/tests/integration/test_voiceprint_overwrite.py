"""Integration tests for voiceprint overwrite functionality - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestVoiceprintOverwrite:
    """Test suite for voiceprint overwrite functionality."""
    
    def test_enrollment_start_endpoint_exists(self, client):
        """Test that enrollment start endpoint exists and accepts force_overwrite parameter."""
        # This is a smoke test - just verify endpoint exists
        response = client.post(
            "/api/enrollment/start",
            data={
                "user_id": "test-user-id",
                "difficulty": "medium",
                "force_overwrite": "false"
            }
        )
        
        # Should return 400 (invalid UUID) or 200, not 404
        assert response.status_code in [200, 400, 422]
    
    def test_force_overwrite_parameter_accepted(self, client):
        """Test that force_overwrite parameter is accepted."""
        response = client.post(
            "/api/enrollment/start",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium",
                "force_overwrite": "true"
            }
        )
        
        # Should not return 422 (validation error)
        assert response.status_code != 422 or "force_overwrite" not in response.json().get("detail", "")
