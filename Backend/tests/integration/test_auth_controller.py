"""Integration tests for the auth controller."""

from fastapi.testclient import TestClient
from src.main import app
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

client = TestClient(app)

# Helper function to register a user
def register_user(name, email, password):
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password}
    )
    return response

# Helper function to log in a user
def login_user(email, password):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    return response


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "voice-biometrics-api",
        "version": "1.0.0",
    }

# @pytest.mark.asyncio
# async def test_register_user(db_pool):
#     """Test user registration."""
#     email = f"testuser_{uuid4()}@example.com"
#     response = register_user("Test User", email, "password123")
#     assert response.status_code == 200
#     assert "user_id" in response.json()

# @pytest.mark.asyncio
# async def test_register_existing_user(db_pool):
#     """Test registration with an already existing email."""
#     email = f"existing_{uuid4()}@example.com"
#     register_user("Existing User", email, "password123")
#     response = register_user("Existing User", email, "password123")
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Email already registered"

# @pytest.mark.asyncio
# async def test_login_user(db_pool):
#     """Test successful user login."""
#     email = f"loginuser_{uuid4()}@example.com"
#     register_user("Login User", email, "password123")
#     response = login_user(email, "password123")
#     assert response.status_code == 200
#     assert "access_token" in response.json()
#     assert "user" in response.json()
#     assert response.json()["user"]["email"] == email

# @pytest.mark.asyncio
# async def test_login_invalid_credentials(db_pool):
#     """Test login with invalid credentials."""
#     email = f"invalid_{uuid4()}@example.com"
#     register_user("Invalid User", email, "password123")
#     response = login_user(email, "wrongpassword")
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Incorrect email or password"

# @pytest.mark.asyncio
# async def test_account_lockout(db_pool):
#     """Test account lockout mechanism."""
#     email = f"locked_{uuid4()}@example.com"
#     register_user("Locked User", email, "password123")

#     # Attempt login multiple times to trigger lockout
#     for _ in range(5): # MAX_FAILED_ATTEMPTS is 5
#         response = login_user(email, "wrongpassword")
#         assert response.status_code == 401
#         assert response.json()["detail"] == "Incorrect email or password"
    
#     # Next attempt should be locked
#     response = login_user(email, "wrongpassword")
#     assert response.status_code == 403
#     assert "Account locked" in response.json()["detail"]

#     # After lockout, successful login should reset attempts
#     # (This part is tricky with TestClient as time doesn't advance.
#     # For a real integration test, you'd need to mock time or wait.)
#     # For now, we'll just assert that a correct login *would* work if not locked.
#     # In a real scenario, we'd wait for LOCKOUT_MINUTES.
#     response = login_user(email, "password123")
#     # This will still fail with 403 because time doesn't advance in TestClient
#     # assert response.status_code == 200 
#     # assert "access_token" in response.json()