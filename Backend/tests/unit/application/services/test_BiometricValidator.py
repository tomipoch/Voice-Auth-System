"""Unit tests for the BiometricValidator service."""

import numpy as np
import pytest

from src.application.services.BiometricValidator import BiometricValidator
from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION


@pytest.fixture
def biometric_validator() -> BiometricValidator:
    """Fixture for the BiometricValidator service."""
    return BiometricValidator()


def test_calculate_similarity_identical_embeddings(biometric_validator: BiometricValidator):
    """Test that identical embeddings have a similarity of 1.0."""
    embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    similarity = biometric_validator.calculate_similarity(embedding, embedding)
    assert np.isclose(similarity, 1.0)


def test_calculate_similarity_orthogonal_embeddings(biometric_validator: BiometricValidator):
    """Test that orthogonal embeddings have a similarity of 0.0."""
    embedding1 = np.zeros(EMBEDDING_DIMENSION).astype(np.float32)
    embedding1[0] = 1.0
    embedding2 = np.zeros(EMBEDDING_DIMENSION).astype(np.float32)
    embedding2[1] = 1.0
    similarity = biometric_validator.calculate_similarity(embedding1, embedding2)
    assert np.isclose(similarity, 0.0)


def test_is_valid_embedding_valid(biometric_validator: BiometricValidator):
    """Test that a valid embedding is considered valid."""
    embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    assert biometric_validator.is_valid_embedding(embedding)


def test_is_valid_embedding_none(biometric_validator: BiometricValidator):
    """Test that a None embedding is considered invalid."""
    assert not biometric_validator.is_valid_embedding(None)


def test_is_valid_embedding_wrong_shape(biometric_validator: BiometricValidator):
    """Test that an embedding with the wrong shape is considered invalid."""
    embedding = np.random.rand(EMBEDDING_DIMENSION + 1).astype(np.float32)
    assert not biometric_validator.is_valid_embedding(embedding)


def test_is_valid_embedding_nan(biometric_validator: BiometricValidator):
    """Test that an embedding with NaN values is considered invalid."""
    embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    embedding[0] = np.nan
    assert not biometric_validator.is_valid_embedding(embedding)


def test_is_valid_embedding_inf(biometric_validator: BiometricValidator):
    """Test that an embedding with infinity values is considered invalid."""
    embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    embedding[0] = np.inf
    assert not biometric_validator.is_valid_embedding(embedding)


def test_is_valid_embedding_zeros(biometric_validator: BiometricValidator):
    """Test that an embedding with all zeros is considered invalid."""
    embedding = np.zeros(EMBEDDING_DIMENSION).astype(np.float32)
    assert not biometric_validator.is_valid_embedding(embedding)
