"""Unit tests for phrase DTOs (Fase 3 coverage)."""

from src.application.dto.phrase_dto import (
    BookDTO,
    PhraseDTO,
    PhraseListDTO,
    PhraseStatsDTO,
)


def test_phrase_dto_stores_fields():
    dto = PhraseDTO(
        id="abc", text="hello world", source=None, word_count=2,
        char_count=11, language="es", difficulty="easy",
        is_active=True, created_at="2024-01-01T00:00:00+00:00",
    )
    assert dto.id == "abc"
    assert dto.text == "hello world"
    assert dto.is_active is True


def test_phrase_stats_dto_stores_fields():
    dto = PhraseStatsDTO(
        total=10, active=8, inactive=2, easy=3, medium=4, hard=3, language="es"
    )
    assert dto.total == 10
    assert dto.active == 8
    assert dto.easy == 3


def test_book_dto_stores_fields():
    dto = BookDTO(id="1", title="Don Quixote", author="Cervantes")
    assert dto.title == "Don Quixote"
    assert dto.author == "Cervantes"


def test_book_dto_optional_author():
    dto = BookDTO(id="2", title="Anonymous", author=None)
    assert dto.author is None


def test_phrase_list_dto_defaults():
    dto = PhraseListDTO()
    assert dto.phrases == []
    assert dto.total == 0
    assert dto.page == 1
    assert dto.limit == 50
    assert dto.total_pages == 1
