"""Tests de PostgresClientAppRepository contra la BD de pruebas."""

import uuid

import pytest

from src.infrastructure.persistence.postgres_client_app_repository import (
    PostgresClientAppRepository,
)


@pytest.fixture
def client_repo(db_pool):
    return PostgresClientAppRepository(db_pool)


@pytest.mark.asyncio
async def test_create_client_returns_key_and_validates(client_repo, db_pool):
    """create_client devuelve client_id + key cruda; la key valida contra key_hash."""
    suffix = uuid.uuid4().hex[:8]
    name = f"BancoDemo-{suffix}"
    client_id, raw_key = await client_repo.create_client(name, f"api-{suffix}@banco.cl")
    assert client_id is not None
    assert len(raw_key) >= 32

    found = await client_repo.get_client_by_api_key(
        PostgresClientAppRepository.hash_api_key(raw_key)
    )
    assert found is not None
    assert found["name"] == name
    assert found["contact_email"] == f"api-{suffix}@banco.cl"
    assert found["revoked_at"] is None

    assert await client_repo.get_client_by_api_key("hash-inexistente") is None

    await db_pool.execute("DELETE FROM api_key WHERE client_id = $1", client_id)
    await db_pool.execute("DELETE FROM client_app WHERE id = $1", client_id)


@pytest.mark.asyncio
async def test_rotate_and_revoke_api_key(client_repo, db_pool):
    suffix = uuid.uuid4().hex[:8]
    name = f"ClienteB-{suffix}"
    client_id, raw_key = await client_repo.create_client(name)
    try:
        new_key = await client_repo.rotate_api_key(client_id)
        assert new_key is not None and new_key != raw_key
        assert await client_repo.get_client_by_api_key(
            PostgresClientAppRepository.hash_api_key(raw_key)
        ) is None
        assert await client_repo.get_client_by_api_key(
            PostgresClientAppRepository.hash_api_key(new_key)
        ) is not None

        await client_repo.revoke_api_key(client_id)
        assert await client_repo.get_client_by_api_key(
            PostgresClientAppRepository.hash_api_key(new_key)
        ) is None
    finally:
        await db_pool.execute("DELETE FROM api_key WHERE client_id = $1", client_id)
        await db_pool.execute("DELETE FROM client_app WHERE id = $1", client_id)


@pytest.mark.asyncio
async def test_rotate_returns_none_for_missing_client(client_repo):
    """rotate_api_key de un cliente inexistente devuelve None."""
    missing = uuid.uuid4()
    assert await client_repo.rotate_api_key(missing) is None


@pytest.mark.asyncio
async def test_list_clients(client_repo, db_pool):
    suffix = uuid.uuid4().hex[:8]
    c1, _ = await client_repo.create_client(f"Cliente Uno {suffix}")
    c2, _ = await client_repo.create_client(f"Cliente Dos {suffix}")
    try:
        clients = await client_repo.list_clients()
        names = {c["name"] for c in clients}
        assert f"Cliente Uno {suffix}" in names and f"Cliente Dos {suffix}" in names
        assert all("key_hash" not in c for c in clients)
    finally:
        await db_pool.execute(
            "DELETE FROM api_key WHERE client_id IN ($1, $2)", c1, c2
        )
        await db_pool.execute("DELETE FROM client_app WHERE id IN ($1, $2)", c1, c2)
