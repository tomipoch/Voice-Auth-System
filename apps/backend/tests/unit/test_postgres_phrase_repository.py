"""Integration-style unit tests for PostgresPhraseRepository.

Uses the test database (voice_biometrics_test) bootstrapped by conftest.
Each test runs in a transaction that is rolled back at teardown.
"""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.model.phrase import Phrase
from src.infrastructure.persistence.postgres_phrase_repository import (
    PostgresPhraseRepository,
)


def _make_phrase(**overrides) -> Phrase:
    defaults = dict(
        id=uuid.uuid4(),
        text="Frase de prueba suficientemente larga para pasar checks",
        source="test",
        word_count=8,
        char_count=53,
        language="es",
        difficulty="medium",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Phrase(**defaults)


@pytest.fixture
def phrase_repo(db_pool):
    return PostgresPhraseRepository(db_pool)


@pytest.mark.asyncio
async def test_save_and_find_by_id(phrase_repo):
    phrase = _make_phrase(text="Frase uno de prueba para guardar y leer")
    await phrase_repo.save(phrase)
    found = await phrase_repo.find_by_id(phrase.id)
    assert found is not None
    assert found.text == phrase.text
    assert found.difficulty == "medium"


@pytest.mark.asyncio
async def test_find_all_active_filters_by_difficulty_and_language(phrase_repo):
    a = _make_phrase(text="Frase A facil de prueba con longitud", difficulty="easy", language="es")
    b = _make_phrase(text="Frase B dificil de prueba con longitud", difficulty="hard", language="es")
    c = _make_phrase(text="English phrase for test with length ok", difficulty="easy", language="en")
    for p in (a, b, c):
        await phrase_repo.save(p)

    es_easy = await phrase_repo.find_all_active(difficulty="easy", language="es")
    assert any(p.id == a.id for p in es_easy)
    assert all(p.difficulty == "easy" and p.language == "es" for p in es_easy)


@pytest.mark.asyncio
async def test_find_random_returns_active_phrases_only(phrase_repo):
    active = _make_phrase(text="Frase activa para random con longitud", is_active=True)
    inactive = _make_phrase(text="Frase inactiva random con longitud", is_active=False)
    await phrase_repo.save(active)
    await phrase_repo.save(inactive)

    results = await phrase_repo.find_random(count=5, language="es")
    assert all(p.is_active for p in results)


@pytest.mark.asyncio
async def test_count_by_difficulty_and_by_status(phrase_repo):
    await phrase_repo.save(_make_phrase(text="Frase uno easy de prueba con longitud", difficulty="easy", is_active=True))
    await phrase_repo.save(_make_phrase(text="Frase dos easy de prueba con longitud", difficulty="easy", is_active=True))
    await phrase_repo.save(_make_phrase(text="Frase hard inactiva de prueba con longitud", difficulty="hard", is_active=False))

    by_diff = await phrase_repo.count_by_difficulty("es")
    assert by_diff.get("easy", 0) >= 2
    assert by_diff.get("hard", 0) >= 1

    by_status = await phrase_repo.count_by_status("es")
    assert by_status["active"] >= 2
    assert by_status["inactive"] >= 1


@pytest.mark.asyncio
async def test_list_books_returns_seeded_books(phrase_repo):
    """La BD de pruebas (init.sql consolidado) siembra los metadatos de libros."""
    books = await phrase_repo.list_books()
    assert len(books) >= 26  # seed del baseline (36 con los PDFs faltantes agregados)
    assert all(b["title"] and b["author"] for b in books)


@pytest.mark.asyncio
async def test_update_active_status_and_delete(phrase_repo):
    phrase = _make_phrase(text="Frase update delete de prueba con longitud")
    await phrase_repo.save(phrase)

    assert await phrase_repo.update_active_status(phrase.id, False) is True
    found = await phrase_repo.find_by_id(phrase.id)
    assert found.is_active is False

    assert await phrase_repo.delete(phrase.id) is True
    assert await phrase_repo.find_by_id(phrase.id) is None

    # Updating a missing phrase returns False
    assert await phrase_repo.update_active_status(uuid.uuid4(), True) is False
    assert await phrase_repo.delete(uuid.uuid4()) is False


@pytest.fixture
async def user_in_pool(db_pool):
    """Crea un usuario en el pool (visible para phrase_repo) y lo limpia al final."""
    user_id = await db_pool.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        f"phrase-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Phrase", "Test", "user", "acme", "{}",
    )
    yield user_id
    await db_pool.execute('DELETE FROM "user" WHERE id = $1', user_id)


@pytest.mark.asyncio
async def test_get_recent_phrase_ids_orders_by_recency(phrase_repo, user_in_pool, db_pool):
    """get_recent_phrase_ids devuelve las frases más recientes primero."""
    from datetime import timedelta

    older = _make_phrase(text="Frase antigua para orden por recencia")
    middle = _make_phrase(text="Frase intermedia para orden por recencia")
    newer = _make_phrase(text="Frase reciente para orden por recencia")
    for p in (older, middle, newer):
        await phrase_repo.save(p)

    now = datetime.now(timezone.utc)
    for phrase_id, minutes_ago in [(older.id, 120), (middle.id, 60), (newer.id, 5)]:
        await db_pool.execute(
            "INSERT INTO phrase_usage (phrase_id, user_id, used_for, used_at) VALUES ($1, $2, 'verification', $3)",
            phrase_id, user_in_pool, now - timedelta(minutes=minutes_ago),
        )

    recent = await phrase_repo.get_recent_phrase_ids(user_in_pool, limit=3)
    assert recent == [newer.id, middle.id, older.id]

    # Cleanup
    await db_pool.execute("DELETE FROM phrase_usage WHERE user_id = $1", user_in_pool)
    for p in (older, middle, newer):
        await phrase_repo.delete(p.id)
