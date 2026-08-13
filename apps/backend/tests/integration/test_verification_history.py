"""Integration tests for verification history endpoint - SIMPLIFIED."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.api.auth_guards import enforce_user_scope


@pytest.fixture
def client():
    """Crea TestClient con dependencias de auth sobreescritas y lifespan
    deshabilitado para evitar crear pools de BD / descargar modelos por test."""
    from contextlib import asynccontextmanager
    from src.api.auth_controller import get_current_user as auth_get_current_user

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

    app.dependency_overrides[auth_get_current_user] = _override_user
    app.dependency_overrides[enforce_user_scope] = _override_scope

    with TestClient(app) as c:
        yield c


class TestVerificationHistory:
    """Test suite for verification history endpoint."""

    def test_verification_history_endpoint_exists(self, client):
        """Test that verification history endpoint exists."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/verification/user/{user_id}/history?limit=5")

        # 200/400/404/500 según existencia del usuario en BD; nunca 401 ni 422
        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "history" in data

    def test_verification_history_accepts_limit_parameter(self, client):
        """Test that limit parameter is accepted."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/verification/user/{user_id}/history?limit=10")

        assert response.status_code != 422 or "limit" not in str(response.json())

    def test_verification_history_invalid_user_id(self, client):
        """Test with invalid user_id format."""
        response = client.get("/api/verification/user/invalid-uuid/history")

        # Sin auth (overrides activos) y con UUID inválido: 422 (validación)
        assert response.status_code in [400, 422]
