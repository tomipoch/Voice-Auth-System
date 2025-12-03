"""Integration tests for verification history endpoint."""

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


class TestVerificationHistory:
    """Test suite for verification history endpoint."""
    
    def test_get_verification_history_empty(self, client, mock_user_id):
        """
        Test getting verification history for user with no verifications.
        Should return empty list.
        """
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.get_verification_history') as mock_history:
            mock_history.return_value = []
            
            # Act
            response = client.get(f"/api/verification/user/{mock_user_id}/history?limit=5")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["history"], list)
            assert len(data["history"]) == 0
    
    def test_get_verification_history_with_results(self, client, mock_user_id):
        """
        Test getting verification history for user with verification attempts.
        Should return list of attempts.
        """
        # Arrange
        mock_history_data = [
            {
                "verification_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": True,
                "similarity_score": 0.92,
                "phrase_match": True
            },
            {
                "verification_id": str(uuid4()),
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "success": False,
                "similarity_score": 0.65,
                "phrase_match": True
            }
        ]
        
        with patch('src.application.verification_service_v2.VerificationServiceV2.get_verification_history') as mock_history:
            mock_history.return_value = mock_history_data
            
            # Act
            response = client.get(f"/api/verification/user/{mock_user_id}/history?limit=5")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["history"]) == 2
            assert data["history"][0]["success"] is True
            assert data["history"][1]["success"] is False
    
    def test_get_verification_history_limit(self, client, mock_user_id):
        """
        Test that limit parameter correctly limits results.
        """
        # Arrange
        mock_history_data = [
            {"verification_id": str(uuid4()), "timestamp": datetime.now(timezone.utc).isoformat()}
            for _ in range(10)
        ]
        
        with patch('src.application.verification_service_v2.VerificationServiceV2.get_verification_history') as mock_history:
            # Mock should respect limit
            def get_history(user_id, limit):
                return mock_history_data[:limit]
            
            mock_history.side_effect = get_history
            
            # Act
            response = client.get(f"/api/verification/user/{mock_user_id}/history?limit=3")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["history"]) <= 3
            
            # Verify service was called with correct limit
            mock_history.assert_called_once()
            call_args = mock_history.call_args
            assert call_args[1]["limit"] == 3 or call_args[0][1] == 3
    
    def test_get_verification_history_invalid_user(self, client):
        """
        Test getting verification history with invalid user_id.
        Should return 400 Bad Request.
        """
        # Act
        response = client.get("/api/verification/user/invalid-uuid/history")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid user ID" in data["detail"] or "invalid" in data["detail"].lower()
    
    def test_get_verification_history_default_limit(self, client, mock_user_id):
        """
        Test that default limit is applied when not specified.
        """
        # Arrange
        with patch('src.application.verification_service_v2.VerificationServiceV2.get_verification_history') as mock_history:
            mock_history.return_value = []
            
            # Act
            response = client.get(f"/api/verification/user/{mock_user_id}/history")
            
            # Assert
            assert response.status_code == 200
            
            # Verify default limit was used (should be 10)
            mock_history.assert_called_once()
            call_args = mock_history.call_args
            # Check if limit parameter was passed (default should be 10)
            if len(call_args[0]) > 1:
                assert call_args[0][1] == 10
            elif "limit" in call_args[1]:
                assert call_args[1]["limit"] == 10
