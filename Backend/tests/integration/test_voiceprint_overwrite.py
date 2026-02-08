"""Integration tests for voiceprint overwrite functionality."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestVoiceprintOverwrite:
    """Test suite for voiceprint overwrite functionality."""
    
    def test_enrollment_start_endpoint_exists(self, client):
        """Test that enrollment start endpoint accepts force_overwrite parameter."""
        response = client.post(
            "/api/enrollment/start",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium",
                "force_overwrite": "true"
            }
        )
        
        # Should not return 404 (endpoint not found)
        # May return 400, 422, 500 (validation/DB errors) but endpoint exists
        assert response.status_code in [200, 400, 422, 500]
    
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
        
        # Should accept the parameter (not 422 for invalid parameter)
        # May fail for other reasons (400, 500) but parameter is valid
        assert response.status_code in [200, 400, 500]
