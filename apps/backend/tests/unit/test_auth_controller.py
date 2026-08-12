"""Unit tests for auth_controller using FastAPI TestClient with mocked AuthService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.auth_controller import auth_router, get_auth_service


def _login_result():
    user_id = str(uuid4())
    return {
        "access_token": "fake-access-token",
        "refresh_token": "fake-refresh-token",
        "expires_in": 7200,
        "user": {
            "id": user_id,
            "name": "Test User",
            "email": "user@example.com",
            "role": "user",
            "company": "acme",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "voice_template": None,
            "settings": {},
        },
    }


@pytest.fixture
def auth_service_mock():
    m = MagicMock()
    m.login = AsyncMock(return_value=_login_result())
    m.refresh = AsyncMock(return_value=_login_result())
    return m


@pytest.fixture
def client(auth_service_mock):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router)

    async def _override_get_auth_service():
        return auth_service_mock

    app.dependency_overrides[get_auth_service] = _override_get_auth_service

    with TestClient(app) as c:
        yield c


def test_login_success(client, auth_service_mock):
    r = client.post("/login", json={"email": "user@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] == "fake-access-token"
    assert data["user"]["email"] == "user@example.com"
    auth_service_mock.login.assert_awaited_once()


def test_login_invalid_credentials_translates_to_401(client, auth_service_mock):
    from src.application.auth_service import AuthError

    auth_service_mock.login = AsyncMock(
        side_effect=AuthError(status_code=401, detail="Invalid credentials")
    )
    r = client.post("/login", json={"email": "user@example.com", "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"


def test_login_locked_account_translates_to_403(client, auth_service_mock):
    from src.application.auth_service import AuthError

    auth_service_mock.login = AsyncMock(
        side_effect=AuthError(status_code=403, detail="Account locked")
    )
    r = client.post("/login", json={"email": "user@example.com", "password": "locked-account"})
    assert r.status_code == 403


def test_refresh_success(client, auth_service_mock):
    r = client.post("/refresh", json={"refresh_token": "old-refresh"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] == "fake-access-token"
    auth_service_mock.refresh.assert_awaited_once()


def test_refresh_invalid_token_returns_401(client, auth_service_mock):
    from src.application.auth_service import AuthError

    auth_service_mock.refresh = AsyncMock(
        side_effect=AuthError(status_code=401, detail="Invalid refresh token")
    )
    r = client.post("/refresh", json={"refresh_token": "bad"})
    assert r.status_code == 401


def test_login_validation_error_422(client):
    r = client.post("/login", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
