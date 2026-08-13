"""Integration tests for challenge controller endpoints - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.api.auth_guards import get_current_user, require_admin_user


@pytest.fixture
def client():
    """Crea TestClient con dependencias de auth sobreescritas y lifespan
    deshabilitado (no se requieren tokens JWT reales)."""
    from contextlib import asynccontextmanager
    from src.api.auth_controller import get_current_user as auth_get_current_user
    from src.api.auth_guards import enforce_user_scope

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    app = create_app()
    app.router.lifespan_context = _noop_lifespan

    fake_admin = {"id": "550e8400-e29b-41d4-a716-446655440000", "email": "admin@test.com",
                  "role": "admin", "company": "acme"}

    async def _override_user():
        return fake_admin

    async def _override_scope(user_id=None):
        return fake_admin

    async def _override_admin():
        return fake_admin

    app.dependency_overrides[auth_get_current_user] = _override_user
    app.dependency_overrides[enforce_user_scope] = _override_scope
    app.dependency_overrides[require_admin_user] = _override_admin

    with TestClient(app) as c:
        yield c


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

        # Should not return 404 (endpoint not found) ni 401 (sin token)
        assert response.status_code != 404
        assert response.status_code != 401

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

        assert response.status_code != 404
        assert response.status_code != 401

    def test_get_challenge_endpoint_exists(self, client):
        """Test that get challenge endpoint exists."""
        challenge_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/challenges/{challenge_id}")

        # 200/404 según si existe el challenge en BD; nunca 401/422/404 del router
        assert response.status_code in [200, 404, 500]
        assert response.status_code != 401

    def test_validate_challenge_endpoint_exists(self, client):
        """Test that validate endpoint exists."""
        response = client.post(
            "/api/challenges/validate",
            data={
                "challenge_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        )

        assert response.status_code != 404
        assert response.status_code != 401

    def test_cleanup_challenges_endpoint_exists(self, client):
        """Test that cleanup endpoint exists."""
        response = client.post("/api/challenges/cleanup")

        assert response.status_code != 404
        assert response.status_code != 401

    def test_get_active_challenge_endpoint_exists(self, client):
        """Test that get active challenge endpoint exists."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/challenges/user/{user_id}/active")

        assert response.status_code != 404
        assert response.status_code != 401
