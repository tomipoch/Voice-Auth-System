"""Unit tests for src.shared.json_metadata (Fase 3 coverage)."""


from src.shared.json_metadata import parse_json_metadata


def test_parse_dict_passes_through():
    assert parse_json_metadata({"a": 1}) == {"a": 1}


def test_parse_empty_returns_empty():
    assert parse_json_metadata("") == {}
    assert parse_json_metadata(None) == {}


def test_parse_valid_json_string():
    assert parse_json_metadata('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_parse_invalid_json_returns_empty():
    assert parse_json_metadata("{not valid json") == {}
    assert parse_json_metadata("undefined") == {}
