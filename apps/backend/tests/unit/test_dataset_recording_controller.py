"""Tests del controller de dataset recording con system_settings mockeado."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dataset_recording_controller import router as dataset_router


@pytest.fixture
def settings_repo():
    return MagicMock()


@pytest.fixture
def client(settings_repo):
    """Crea un TestClient con la dependencia get_system_settings_repository sobreescrita."""
    from src.infrastructure.config.dependencies import get_system_settings_repository
    from src.api.auth_guards import require_admin_user

    app = FastAPI()
    app.include_router(dataset_router)

    settings_repo.get = AsyncMock(return_value=None)
    settings_repo.set = AsyncMock()

    async def _override_settings_repo():
        return settings_repo

    async def _override_admin():
        return {"id": str(uuid4()), "email": "admin@test.com", "role": "admin"}

    app.dependency_overrides[get_system_settings_repository] = _override_settings_repo
    app.dependency_overrides[require_admin_user] = _override_admin

    return TestClient(app)


def test_start_recording_persists_settings(client, settings_repo):
    with patch("src.api.dataset_recording_controller.dataset_recorder") as recorder:
        recorder.start_recording.return_value = "sess_1"
        recorder.session_dir = MagicMock()
        recorder.session_dir.__str__ = lambda _: "/tmp/sess"

        response = client.post("/api/dataset-recording/start", json={"session_name": "mini"})
        assert response.status_code == 200, response.text
        settings_repo.set.assert_awaited_once()
        key = settings_repo.set.await_args.args[0]
        value = settings_repo.set.await_args.args[1]
        assert key == "dataset_recording"
        assert value["enabled"] is True
        assert value["session_id"] == "sess_1"


def test_stop_recording_clears_settings(client, settings_repo):
    with patch("src.api.dataset_recording_controller.dataset_recorder") as recorder:
        recorder.stop_recording.return_value = "/tmp/sess_stopped"
        response = client.post("/api/dataset-recording/stop")
        assert response.status_code == 200, response.text
        settings_repo.set.assert_awaited_once()
        key = settings_repo.set.await_args.args[0]
        value = settings_repo.set.await_args.args[1]
        assert key == "dataset_recording"
        assert value["enabled"] is False


def test_status_reads_persisted_settings(client, settings_repo):
    settings_repo.get = AsyncMock(return_value={
        "enabled": True, "session_id": "sess_1", "session_dir": "/tmp/sess"
    })
    with patch("src.api.dataset_recording_controller.dataset_recorder") as recorder:
        recorder.get_session_summary.return_value = {
            "enabled": True, "total_users": 0,
            "total_enrollment_audios": 0, "total_verification_audios": 0,
        }
        response = client.get("/api/dataset-recording/status")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["enabled"] is True
        assert body["session_id"] == "sess_1"
