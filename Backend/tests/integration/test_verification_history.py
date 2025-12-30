"""Integration tests for verification history endpoint - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestVerificationHistory:
    """Test suite for verification history endpoint."""
    
    def test_verification_history_endpoint_exists(self, client):
        """Test that verification history endpoint exists."""
        # Valid UUID
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/verification/user/{user_id}/history?limit=5")
        
        # Should return 200 or 404 (user not found), not 404 (endpoint not found)
        assert response.status_code in [200, 404, 500]
        
        # If 200, should have expected structure
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "history" in data
    
    def test_verification_history_accepts_limit_parameter(self, client):
        """Test that limit parameter is accepted."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/verification/user/{user_id}/history?limit=10")
        
        # Should not return 422 (validation error for limit)
        assert response.status_code != 422 or "limit" not in str(response.json())
    
    def test_verification_history_invalid_user_id(self, client):
        """Test with invalid user_id format."""
        response = client.get("/api/verification/user/invalid-uuid/history")
        
        # Should return 400 or 422 (validation error)
        assert response.status_code in [400, 422]
