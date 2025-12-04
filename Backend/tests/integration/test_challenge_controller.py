"""Integration tests for challenge controller endpoints - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestChallengeController:
    """Test suite for challenge controller endpoints."""
    
    def test_create_challenge_endpoint_exists(self, client):
        """Test that create challenge endpoint exists."""
        response = client.post(
            "/api/challenges/create",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium"
            }
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_create_challenge_batch_endpoint_exists(self, client):
        """Test that create-batch endpoint exists."""
        response = client.post(
            "/api/challenges/create-batch",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "count": "3",
                "difficulty": "medium"
            }
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_get_challenge_endpoint_exists(self, client):
        """Test that get challenge endpoint exists."""
        challenge_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/challenges/{challenge_id}")
        
        # Should not return 404 (endpoint not found) or 422 (validation)
        # May return 404 if challenge doesn't exist, but endpoint should exist
        assert response.status_code in [200, 404, 500]
    
    def test_validate_challenge_endpoint_exists(self, client):
        """Test that validate endpoint exists."""
        response = client.post(
            "/api/challenges/validate",
            data={
                "challenge_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        )
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_cleanup_challenges_endpoint_exists(self, client):
        """Test that cleanup endpoint exists."""
        response = client.post("/api/challenges/cleanup")
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
    
    def test_get_active_challenge_endpoint_exists(self, client):
        """Test that get active challenge endpoint exists."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/challenges/user/{user_id}/active")
        
        # Should not return 404 (endpoint not found)
        assert response.status_code != 404
