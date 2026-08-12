"""Unit tests for PostgresAuditLogRepository."""

import uuid
from datetime import datetime, timezone

import pytest

from src.infrastructure.persistence.postgres_audit_log_repository import PostgresAuditLogRepository
from src.shared.types.common_types import AuditAction


@pytest.fixture
def audit_repo(db_pool):
    return PostgresAuditLogRepository(db_pool)


@pytest.mark.asyncio
async def test_log_event_and_get_user_activity(audit_repo):
    actor = f"user-{uuid.uuid4().hex[:8]}"
    await audit_repo.log_event(
        actor=actor,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=actor,
        success=True,
        metadata={"ip": "127.0.0.1"},
    )
    logs = await audit_repo.get_user_activity(actor, hours=24, limit=10)
    assert any(l["actor"] == actor and l["action"] == AuditAction.LOGIN.value for l in logs)


@pytest.mark.asyncio
async def test_log_event_with_failure(audit_repo):
    actor = f"user-{uuid.uuid4().hex[:8]}"
    await audit_repo.log_event(
        actor=actor,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=actor,
        success=False,
        metadata={"reason": "bad password"},
    )
    logs = await audit_repo.get_user_activity(actor, hours=24, limit=10)
    found = next((l for l in logs if l["actor"] == actor), None)
    assert found is not None
    assert found["success"] is False


@pytest.mark.asyncio
async def test_get_logs_with_filters(audit_repo):
    actor = f"user-{uuid.uuid4().hex[:8]}"
    await audit_repo.log_event(
        actor=actor, action=AuditAction.LOGIN, entity_type="user", entity_id=actor
    )
    await audit_repo.log_event(
        actor=actor, action=AuditAction.LOGOUT, entity_type="user", entity_id=actor
    )

    login_logs = await audit_repo.get_logs(action=AuditAction.LOGIN.value, limit=50)
    assert all(l["action"] == AuditAction.LOGIN.value for l in login_logs)


@pytest.mark.asyncio
async def test_get_user_activity_limit(audit_repo):
    actor = f"user-{uuid.uuid4().hex[:8]}"
    for _ in range(5):
        await audit_repo.log_event(
            actor=actor, action=AuditAction.LOGIN, entity_type="user", entity_id=actor
        )
    logs = await audit_repo.get_user_activity(actor, hours=24, limit=3)
    assert len(logs) == 3
