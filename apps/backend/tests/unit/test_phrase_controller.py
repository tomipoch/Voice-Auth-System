"""Unit tests for phrase controller using FastAPI TestClient with mocked services.

Tests the HTTP layer of /api/phrases/{books,stats,list,random} without
requiring a running app lifespan (we override dependencies).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.phrase_controller import router as phrase_router
from src.application.dto.phrase_dto import PhraseDTO, PhraseStatsDTO
from src.domain.model.phrase import Phrase
from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION


def _make_phrase(**overrides) -> Phrase:
    from datetime import datetime, timezone
    from uuid import uuid4
    p = Phrase(
        id=uuid4(),
        text="Frase de prueba suficientemente larga",
        source="test",
        word_count=5,
        char_count=33,
        language="es",
        difficulty="medium",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    return p


@pytest.fixture
def phrase_service_mock():
    m = MagicMock()
    m.list_books = AsyncMock(return_value=[])
    m.get_phrase_stats = AsyncMock(return_value=PhraseStatsDTO(
        total=0, active=0, inactive=0, easy=0, medium=0, hard=0, language="es"
    ))
    m.list_phrases_paginated = AsyncMock(return_value=None)  # not used in these tests
    m.get_random_phrases = AsyncMock(return_value=[])
    return m


@pytest.fixture
def client(phrase_service_mock):
    from src.api import phrase_controller as pc
    from src.api.phrase_controller import get_phrase_service, get_current_admin_user

    app = __import__("fastapi").FastAPI()
    app.include_router(phrase_router)

    async def _override_get_phrase_service():
        return phrase_service_mock

    async def _override_get_current_admin_user():
        return {"id": "admin-id", "email": "admin@test.com", "role": "admin"}

    app.dependency_overrides[get_phrase_service] = _override_get_phrase_service
    app.dependency_overrides[get_current_admin_user] = _override_get_current_admin_user

    with TestClient(app) as c:
        yield c


def test_books_returns_empty_list(client, phrase_service_mock):
    r = client.get("/books")
    assert r.status_code == 200
    assert r.json() == []


def test_books_returns_books(client, phrase_service_mock):
    from src.application.dto.phrase_dto import BookDTO
    phrase_service_mock.list_books = AsyncMock(return_value=[
        BookDTO(id="b1", title="1984", author="Orwell"),
        BookDTO(id="b2", title="Don Quixote", author="Cervantes"),
    ])
    r = client.get("/books")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["title"] == "1984"


def test_stats_returns_stats(client, phrase_service_mock):
    phrase_service_mock.get_phrase_stats = AsyncMock(return_value=PhraseStatsDTO(
        total=100, active=80, inactive=20, easy=30, medium=40, hard=30, language="es"
    ))
    r = client.get("/stats", params={"language": "es"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total"] == 100
    assert data["active"] == 80
    assert data["easy"] == 30


def test_random_returns_phrases(client, phrase_service_mock):
    p1 = _make_phrase()
    p2 = _make_phrase()
    phrase_service_mock.get_random_phrases = AsyncMock(return_value=[
        PhraseDTO(
            id=str(p1.id), text=p1.text, source=p1.source, word_count=p1.word_count,
            char_count=p1.char_count, language=p1.language, difficulty=p1.difficulty,
            is_active=p1.is_active, created_at=p1.created_at.isoformat(),
        ),
        PhraseDTO(
            id=str(p2.id), text=p2.text, source=p2.source, word_count=p2.word_count,
            char_count=p2.char_count, language=p2.language, difficulty=p2.difficulty,
            is_active=p2.is_active, created_at=p2.created_at.isoformat(),
        ),
    ])
    r = client.get("/random", params={"count": 2})
    assert r.status_code == 200, r.text
    assert len(r.json()) == 2
