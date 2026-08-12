"""Unit tests for PostgresUserRepository using the test database."""

import uuid
from datetime import datetime, timezone

import pytest

from src.infrastructure.persistence.postgres_user_repository import PostgresUserRepository


@pytest.fixture
def user_repo(db_pool):
    return PostgresUserRepository(db_pool)


def _user_kwargs(**overrides) -> dict:
    base = dict(
        external_ref=f"ext-{uuid.uuid4().hex[:8]}",
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        first_name="Test",
        last_name="User",
        role="user",
        company="acme",
    )
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_and_get_user_by_id(user_repo):
    kwargs = _user_kwargs()
    user_id = await user_repo.create_user(**kwargs)
    assert user_id is not None

    user = await user_repo.get_user(user_id)
    assert user is not None
    assert user["email"] == kwargs["email"]
    assert user["role"] == "user"
    assert user["company"] == "acme"


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo):
    kwargs = _user_kwargs()
    user_id = await user_repo.create_user(**kwargs)

    found = await user_repo.get_user_by_email(kwargs["email"])
    assert found is not None
    assert found["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_by_external_ref(user_repo):
    kwargs = _user_kwargs()
    user_id = await user_repo.create_user(**kwargs)

    found = await user_repo.get_user_by_external_ref(kwargs["external_ref"])
    assert found is not None
    assert found["id"] == user_id


@pytest.mark.asyncio
async def test_user_exists(user_repo):
    user_id = await user_repo.create_user(**_user_kwargs())
    assert await user_repo.user_exists(user_id) is True
    assert await user_repo.user_exists(uuid.uuid4()) is False


@pytest.mark.asyncio
async def test_update_user(user_repo):
    user_id = await user_repo.create_user(**_user_kwargs())
    await user_repo.update_user(user_id, {"first_name": "Updated", "company": "newco"})

    user = await user_repo.get_user(user_id)
    assert user["first_name"] == "Updated"
    assert user["company"] == "newco"


@pytest.mark.asyncio
async def test_failed_auth_attempts_increment_and_reset(user_repo):
    user_id = await user_repo.create_user(**_user_kwargs())

    await user_repo.increment_failed_auth_attempts(user_id)
    await user_repo.increment_failed_auth_attempts(user_id)
    user = await user_repo.get_user(user_id)
    assert user["failed_auth_attempts"] == 2

    await user_repo.reset_failed_auth_attempts(user_id)
    user = await user_repo.get_user(user_id)
    assert user["failed_auth_attempts"] == 0


@pytest.mark.asyncio
async def test_lock_account(user_repo):
    from datetime import timedelta
    user_id = await user_repo.create_user(**_user_kwargs())
    await user_repo.lock_user_account(user_id, timedelta(minutes=15))

    user = await user_repo.get_user(user_id)
    assert user["locked_until"] is not None


@pytest.mark.asyncio
async def test_delete_user(user_repo):
    user_id = await user_repo.create_user(**_user_kwargs())
    await user_repo.delete_user(user_id)
    assert await user_repo.get_user(user_id) is None


@pytest.mark.asyncio
async def test_set_and_get_user_policy(user_repo):
    user_id = await user_repo.create_user(**_user_kwargs())
    await user_repo.set_user_policy(user_id, keep_audio=True, retention_days=30)
    policy = await user_repo.get_user_policy(user_id)
    assert policy is not None
    assert policy["keep_audio"] is True
    assert policy["retention_days"] == 30


@pytest.mark.asyncio
async def test_get_users_by_company_pagination(user_repo):
    for _ in range(3):
        await user_repo.create_user(**_user_kwargs(company="shared-co"))
    await user_repo.create_user(**_user_kwargs(company="other-co"))

    users_page1, total = await user_repo.get_users_by_company("shared-co", page=1, limit=2)
    assert total >= 3
    assert len(users_page1) == 2

    users_page2, _ = await user_repo.get_users_by_company("shared-co", page=2, limit=2)
    assert len(users_page2) >= 1


@pytest.mark.asyncio
async def test_get_all_users_pagination(user_repo):
    for _ in range(3):
        await user_repo.create_user(**_user_kwargs())
    users, total = await user_repo.get_all_users(page=1, limit=2)
    assert total >= 3
    assert len(users) == 2
