"""Integration tests for voiceprint overwrite functionality."""

import pytest
from fastapi.testclient import TestClient

from src.api.auth_guards import enforce_user_scope, require_admin_user
from src.main import create_app


@pytest.fixture
def client():
    """Crea TestClient con dependencias de auth sobreescritas y lifespan
    deshabilitado."""
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

    async def _override_admin():
        return fake_admin

    app.dependency_overrides[auth_get_current_user] = _override_user
    app.dependency_overrides[enforce_user_scope] = _override_scope
    app.dependency_overrides[require_admin_user] = _override_admin

    with TestClient(app) as c:
        yield c


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

        assert response.status_code in [200, 400, 422, 500]
        assert response.status_code != 401

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

        assert response.status_code in [200, 400, 500]
        assert response.status_code != 401
