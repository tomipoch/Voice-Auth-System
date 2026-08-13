"""Unit tests for admin API client management."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.admin_controller import admin_router


@pytest.fixture
def client_repo():
    repo = MagicMock()
    repo.create_client = AsyncMock(return_value=(uuid4(), "sk_test_abc"))
    repo.list_clients = AsyncMock(return_value=[
        {"id": "c1", "name": "Banco", "contact_email": None, "key_created_at": None, "revoked_at": None},
    ])
    repo.rotate_api_key = AsyncMock(return_value="sk_new_xyz")
    repo.revoke_api_key = AsyncMock()
    return repo


@pytest.fixture
def client(client_repo):
    from src.infrastructure.config.dependencies import get_client_app_repository
    # Forzar carga de auth_guards antes que admin_controller para que
    # admin_controller.require_admin_user sea la misma referencia.
    import src.api.auth_guards as guards
    _ = guards.require_admin_user

    app = FastAPI()
    app.include_router(admin_router)

    async def _override_repo():
        return client_repo

    async def _override_admin():
        return {"id": str(uuid4()), "email": "admin@test.com", "role": "admin"}

    app.dependency_overrides[get_client_app_repository] = _override_repo
    app.dependency_overrides[guards.require_admin_user] = _override_admin

    return TestClient(app)


def test_create_client_returns_key_once(client, client_repo):
    response = client.post("/clients", json={"name": "BancoDemo", "contact_email": "api@x.cl"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["api_key"] == "sk_test_abc"
    assert body["name"] == "BancoDemo"
    client_repo.create_client.assert_awaited_once()


def test_list_clients_never_exposes_key_hash(client, client_repo):
    response = client.get("/clients")
    assert response.status_code == 200, response.text
    assert "key_hash" not in response.text


def test_rotate_and_revoke(client, client_repo):
    cid = uuid4()
    response = client.post(f"/clients/{cid}/rotate")
    assert response.status_code == 200, response.text
    assert response.json()["api_key"] == "sk_new_xyz"

    response = client.delete(f"/clients/{cid}")
    assert response.status_code == 200, response.text
    client_repo.revoke_api_key.assert_awaited_once_with(cid)


def test_rotate_returns_404_when_missing(client, client_repo):
    client_repo.rotate_api_key = AsyncMock(return_value=None)
    response = client.post(f"/clients/{uuid4()}/rotate")
    assert response.status_code == 404
