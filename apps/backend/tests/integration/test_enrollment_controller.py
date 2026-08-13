"""Integration tests for enrollment controller endpoints - SIMPLIFIED."""

import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.auth_guards import enforce_user_scope, require_admin_user
from src.main import create_app


@pytest.fixture
def client():
    """Crea TestClient con dependencias de auth sobreescritas y lifespan
    deshabilitado (evita descargar modelos ML y crear pools de BD por test)."""
    from contextlib import asynccontextmanager

    from src.api.auth_controller import get_current_user as auth_get_current_user
    from src.infrastructure.config.dependencies import get_voice_biometric_engine

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

    fake_engine = MagicMock()
    fake_engine.validate_audio_quality = MagicMock(return_value={"is_valid": True, "snr_db": 20.0, "duration_sec": 1.0})
    fake_engine.extract_embedding_only = MagicMock(return_value=None)

    def _override_engine():
        return fake_engine

    app.dependency_overrides[auth_get_current_user] = _override_user
    app.dependency_overrides[enforce_user_scope] = _override_scope
    app.dependency_overrides[require_admin_user] = _override_admin
    app.dependency_overrides[get_voice_biometric_engine] = _override_engine

    with TestClient(app) as c:
        yield c


class TestEnrollmentController:
    """Test suite for enrollment controller endpoints."""

    def test_start_enrollment_endpoint_exists(self, client):
        """Test that start enrollment endpoint exists."""
        response = client.post(
            "/api/enrollment/start",
            data={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium"
            }
        )

        # 200/400/422/500 según validación o DB; nunca 401 ni 404 del router
        assert response.status_code in [200, 400, 422, 500]
        assert response.status_code != 401

    def test_add_sample_endpoint_exists(self, client):
        """Test that add-sample endpoint exists."""
        audio_data = b"fake audio data"
        files = {"audio_file": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = client.post(
            "/api/enrollment/add-sample",
            data={
                "enrollment_id": "550e8400-e29b-41d4-a716-446655440000",
                "challenge_id": "550e8400-e29b-41d4-a716-446655440001",
                "phrase_number": "1"
            },
            files=files
        )

        assert response.status_code != 404
        assert response.status_code != 401

    def test_complete_enrollment_endpoint_exists(self, client):
        """Test that complete enrollment endpoint exists."""
        response = client.post(
            "/api/enrollment/complete",
            data={"enrollment_id": "550e8400-e29b-41d4-a716-446655440000"}
        )

        assert response.status_code != 404
        assert response.status_code != 401

    def test_get_enrollment_status_endpoint_exists(self, client):
        """Test that enrollment status endpoint exists and returns 200."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/enrollment/status/{user_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "user_not_found"
