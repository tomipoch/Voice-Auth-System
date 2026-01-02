"""Biometric validator service."""

import numpy as np
from ...shared.types.common_types import VoiceEmbedding
from ...shared.constants.biometric_constants import EMBEDDING_DIMENSION


class BiometricValidator:
    """Service for validating biometric data."""

    def calculate_similarity(
        self, embedding1: VoiceEmbedding, embedding2: VoiceEmbedding
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        # Normalize embeddings
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)

        # Calculate cosine similarity
        similarity = np.dot(norm1, norm2)

        # Clamp to [0, 1] and return
        return max(0.0, min(1.0, similarity))

    def is_valid_embedding(self, embedding: VoiceEmbedding) -> bool:
        """Check if the embedding is valid."""
        if embedding is None:
            return False

        # Check shape
        if embedding.shape != (EMBEDDING_DIMENSION,):
            return False

        # Check for NaN or infinity
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False

        # Check if not all zeros
        if np.allclose(embedding, 0):
            return False

        return True
