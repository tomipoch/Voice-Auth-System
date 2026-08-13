"""Unit tests for the admin controller.

Covers the user-management and stats endpoints with mocked repositories
and a single dependency-injected identity. The override targets the
upstream ``get_current_user`` dependency so the real ``require_admin``
and ``require_admin_user`` guards run their actual role checks.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.admin_controller import admin_router
from src.api.auth_controller import get_current_user
from src.infrastructure.config.dependencies import (
    get_audit_log_repository,
    get_user_repository,
)


def _make_admin(role: str = "admin", company: str = "familia") -> dict:
    return {
        "id": str(uuid4()),
        "email": f"{role}@{company}.com",
        "role": role,
        "company": company,
    }


def _user(**overrides) -> dict:
    base = {
        "id": uuid4(),
        "email": "u@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "company": "familia",
        "is_active": True,
        "has_voiceprint": False,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "last_login": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def user_repo():
    repo = MagicMock()
    repo.get_users_by_company = AsyncMock(return_value=([], 0))
    repo.get_all_users = AsyncMock(return_value=([], 0))
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.update_user = AsyncMock()
    repo.delete_user = AsyncMock()
    return repo


@pytest.fixture
def audit_repo():
    repo = MagicMock()
    repo.get_logs = AsyncMock(return_value=[])
    return repo


def _build_client(user_repo, audit_repo, current_user):
    app = FastAPI()
    app.include_router(admin_router)

    async def _override_user_repo():
        return user_repo

    async def _override_audit_repo():
        return audit_repo

    async def _override_current_user(_=None):
        return current_user

    app.dependency_overrides[get_user_repository] = _override_user_repo
    app.dependency_overrides[get_audit_log_repository] = _override_audit_repo
    app.dependency_overrides[get_current_user] = _override_current_user
    return TestClient(app)


class TestListUsers:
    def test_admin_sees_only_own_company(self, user_repo, audit_repo):
        user_repo.get_users_by_company = AsyncMock(
            return_value=(
                [_user(), _user(email="b@example.com")],
                2,
            )
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.get("/users?page=1&limit=10")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] == 2
        assert len(body["users"]) == 2
        user_repo.get_users_by_company.assert_awaited_once_with("familia", 1, 10)
        user_repo.get_all_users.assert_not_awaited()

    def test_admin_response_filters_out_admins(self, user_repo, audit_repo):
        user_repo.get_users_by_company = AsyncMock(
            return_value=(
                [_user(), _user(role="admin", email="otheradmin@example.com")],
                2,
            )
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.get("/users")
        body = response.json()
        assert body["total"] == 1
        assert all(u["role"] == "user" for u in body["users"])

    def test_regular_user_is_forbidden(self, user_repo, audit_repo):
        client = _build_client(user_repo, audit_repo, _make_admin(role="user"))
        response = client.get("/users")
        assert response.status_code == 403


class TestStats:
    def _two_users(self):
        u = _user(has_voiceprint=True)
        u2 = _user(email="b@example.com")
        return [u, u2]

    def test_admin_stats_count_enrollments_and_verifications(
        self, user_repo, audit_repo
    ):
        users = self._two_users()
        user_repo.get_users_by_company = AsyncMock(return_value=(users, len(users)))
        now = datetime.now(timezone.utc)
        audit_repo.get_logs = AsyncMock(
            return_value=[
                {
                    "action": "VERIFY",
                    "entity_type": "verification_result",
                    "actor": str(users[1]["id"]),
                    "success": True,
                    "timestamp": now - timedelta(hours=2),
                },
                {
                    "action": "VERIFY",
                    "entity_type": "verification_result",
                    "actor": str(users[1]["id"]),
                    "success": False,
                    "timestamp": now - timedelta(hours=5),
                },
            ]
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.get("/stats")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total_users"] == 2
        assert body["total_enrollments"] == 1
        assert body["total_verifications"] == 2
        assert body["success_rate"] == pytest.approx(0.5)
        assert body["failed_verifications_24h"] == 1
        assert len(body["daily_verifications"]) == 7

    def test_admin_stats_drop_outsider_logs(self, user_repo, audit_repo):
        users = self._two_users()
        company_user_id = str(users[1]["id"])
        outsider_id = str(uuid4())
        user_repo.get_users_by_company = AsyncMock(return_value=(users, len(users)))
        now = datetime.now(timezone.utc)
        audit_repo.get_logs = AsyncMock(
            return_value=[
                {
                    "action": "VERIFY",
                    "entity_type": "verification_result",
                    "actor": company_user_id,
                    "success": True,
                    "timestamp": now,
                },
                {
                    "action": "VERIFY",
                    "entity_type": "verification_result",
                    "actor": outsider_id,
                    "success": True,
                    "timestamp": now,
                },
            ]
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.get("/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["total_verifications"] == 1

    def test_superadmin_is_forbidden_by_require_admin(self, user_repo, audit_repo):
        client = _build_client(user_repo, audit_repo, _make_admin(role="superadmin"))
        response = client.get("/stats")
        assert response.status_code == 403


class TestDeleteUser:
    def test_admin_cannot_delete_other_company(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "email": "x@y.com",
                "company": "other",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.delete(f"/users/{target_id}")
        assert response.status_code == 403
        user_repo.delete_user.assert_not_awaited()

    def test_admin_can_delete_own_company_user(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "email": "x@y.com",
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.delete(f"/users/{target_id}")
        assert response.status_code == 200, response.text
        user_repo.delete_user.assert_awaited_once_with(target_id)

    def test_cannot_delete_self(self, user_repo, audit_repo):
        admin_dict = _make_admin()
        client = _build_client(user_repo, audit_repo, admin_dict)
        response = client.delete(f"/users/{admin_dict['id']}")
        assert response.status_code == 400
        user_repo.delete_user.assert_not_awaited()

    def test_delete_returns_404_when_missing(self, user_repo, audit_repo):
        user_repo.get_user_by_id = AsyncMock(return_value=None)
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.delete(f"/users/{uuid4()}")
        assert response.status_code == 404


class TestUpdateUser:
    def test_admin_cannot_promote_to_admin(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"role": "admin"},
        )
        assert response.status_code == 403
        user_repo.update_user.assert_not_awaited()

    def test_admin_cannot_update_other_company(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "other",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"first_name": "New"},
        )
        assert response.status_code == 403

    def test_admin_cannot_change_company(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"company": "other-company"},
        )
        assert response.status_code == 403

    def test_admin_can_update_own_company_fields(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"first_name": "Nuevo", "last_name": "Apellido"},
        )
        assert response.status_code == 200, response.text
        user_repo.update_user.assert_awaited_once()
        updates = user_repo.update_user.await_args.args[1]
        assert updates["first_name"] == "Nuevo"
        assert "role" not in updates
        assert "company" not in updates

    def test_invalid_rut_format_returns_422(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"rut": "not-a-rut"},
        )
        assert response.status_code == 422

    def test_invalid_rut_checksum_returns_400(self, user_repo, audit_repo):
        target_id = uuid4()
        user_repo.get_user_by_id = AsyncMock(
            return_value={
                "id": target_id,
                "company": "familia",
                "role": "user",
            }
        )
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{target_id}",
            json={"rut": "12345678-0"},
        )
        assert response.status_code == 400

    def test_update_404_when_missing(self, user_repo, audit_repo):
        user_repo.get_user_by_id = AsyncMock(return_value=None)
        client = _build_client(user_repo, audit_repo, _make_admin())
        response = client.patch(
            f"/users/{uuid4()}",
            json={"first_name": "X"},
        )
        assert response.status_code == 404
        user_repo.update_user.assert_not_awaited()
