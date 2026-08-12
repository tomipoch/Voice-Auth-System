"""Unit tests for the AuthService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.auth_service import AuthError, AuthService


def _make_user(**overrides) -> dict:
    user = {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "password": "$2b$12$dummyhashdummyhashdummyhashdummyhashdummyhashdummyhash",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "company": "acme",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "failed_auth_attempts": 0,
        "locked_until": None,
    }
    user.update(overrides)
    return user


def _make_service(user=None) -> AuthService:
    user_repo = MagicMock()
    user_repo.get_user_by_email = AsyncMock(return_value=user)
    user_repo.increment_failed_auth_attempts = AsyncMock()
    user_repo.lock_user_account = AsyncMock()
    user_repo.reset_failed_auth_attempts = AsyncMock()
    audit_repo = MagicMock()
    audit_repo.log_event = AsyncMock()
    return AuthService(user_repo=user_repo, audit_repo=audit_repo)


@pytest.mark.asyncio
class TestAuthService:
    async def test_login_success(self):
        user = _make_user()
        service = _make_service(user=user)
        with patch("src.application.auth_service.bcrypt.checkpw", return_value=True):
            result = await service.login("user@example.com", "right-password", ip="1.2.3.4")
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["expires_in"] == AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert result["user"]["email"] == "user@example.com"
        service._user_repo.reset_failed_auth_attempts.assert_awaited_once()
        service._audit_repo.log_event.assert_awaited_once()

    async def test_login_user_not_found(self):
        service = _make_service(user=None)
        with pytest.raises(AuthError) as exc:
            await service.login("ghost@example.com", "x", ip="1.2.3.4")
        assert exc.value.status_code == 401
        service._user_repo.reset_failed_auth_attempts.assert_not_awaited()

    async def test_login_wrong_password_increments_and_raises(self):
        user = _make_user(failed_auth_attempts=1)
        service = _make_service(user=user)
        with patch("src.application.auth_service.bcrypt.checkpw", return_value=False):
            with pytest.raises(AuthError) as exc:
                await service.login("user@example.com", "wrong", ip="1.2.3.4")
        assert exc.value.status_code == 401
        service._user_repo.increment_failed_auth_attempts.assert_awaited_once()
        service._user_repo.lock_user_account.assert_not_awaited()

    async def test_login_locks_after_max_attempts(self):
        user = _make_user(failed_auth_attempts=AuthService.MAX_FAILED_ATTEMPTS - 1)
        service = _make_service(user=user)
        with patch("src.application.auth_service.bcrypt.checkpw", return_value=False):
            with pytest.raises(AuthError):
                await service.login("user@example.com", "wrong", ip="1.2.3.4")
        service._user_repo.lock_user_account.assert_awaited_once()

    async def test_login_locked_account(self):
        locked = _make_user(locked_until=datetime.now(timezone.utc) + timedelta(minutes=10))
        service = _make_service(user=locked)
        with pytest.raises(AuthError) as exc:
            await service.login("user@example.com", "anything", ip="1.2.3.4")
        assert exc.value.status_code == 403
        service._user_repo.reset_failed_auth_attempts.assert_not_awaited()

    async def test_refresh_success(self):
        user = _make_user()
        service = _make_service(user=user)
        # Issue a real refresh token via the service itself
        from src.config import ALGORITHM, SECRET_KEY
        import jwt
        token = jwt.encode(
            {"sub": "user@example.com", "user_id": str(user["id"]), "type": "refresh"},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        result = await service.refresh(refresh_token=token)
        assert "access_token" in result
        assert result["refresh_token"] == token

    async def test_refresh_invalid_token(self):
        service = _make_service()
        with pytest.raises(AuthError) as exc:
            await service.refresh(refresh_token="not-a-jwt")
        assert exc.value.status_code == 401

    async def test_refresh_wrong_type(self):
        service = _make_service()
        from src.config import ALGORITHM, SECRET_KEY
        import jwt
        token = jwt.encode(
            {"sub": "user@example.com", "user_id": "x", "type": "access"},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        with pytest.raises(AuthError):
            await service.refresh(refresh_token=token)

    def test_user_to_response_shape(self):
        user = _make_user()
        resp = AuthService.user_to_response(user)
        assert resp["email"] == user["email"]
        assert resp["name"] == "Test User"
        assert resp["role"] == "user"
        assert resp["voice_template"] is None
