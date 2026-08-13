"""Integration tests for the auth controller."""


import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Crea TestClient con lifespan deshabilitado (no requiere BD ni modelos)."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    app = create_app()
    app.router.lifespan_context = _noop_lifespan
    return TestClient(app)


def register_user(client, name, email, password):
    return client.post("/api/auth/register", json={"name": name, "email": email, "password": password})


def login_user(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_health_check(client):
    """Health check devuelve 200; status puede ser 'healthy' o 'starting' según
    si el lifespan inicializó la BD (TESTING=True evita init_db_pool)."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "voice-biometrics-api"
    assert body["version"] == "1.0.0"
    assert body["status"] in ("healthy", "starting")
    assert "components" in body
    assert body["components"]["database"] in ("up", "down")
    assert body["components"]["models"] in ("loaded", "loading")