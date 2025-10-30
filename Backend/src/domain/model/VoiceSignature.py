"""Voice signature domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
import numpy as np

from ...shared.types.common_types import VoiceEmbedding, UserId


@dataclass
class VoiceSignature:
    """Represents a user's voice biometric signature (voiceprint)."""
    
    id: UUID
    user_id: UserId
    embedding: VoiceEmbedding
    created_at: datetime
    speaker_model_id: Optional[int] = None
    
    def calculate_similarity(self, other_embedding: VoiceEmbedding) -> float:
        """Calculate cosine similarity with another embedding."""
        # Normalize embeddings
        norm_self = self.embedding / np.linalg.norm(self.embedding)
        norm_other = other_embedding / np.linalg.norm(other_embedding)
        
        # Calculate cosine similarity
        similarity = np.dot(norm_self, norm_other)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def is_valid_embedding(self) -> bool:
        """Check if the embedding is valid."""
        if self.embedding is None:
            return False
        
        # Check shape
        expected_shape = (256,)  # From constants
        if self.embedding.shape != expected_shape:
            return False
        
        # Check for NaN or infinity
        if np.any(np.isnan(self.embedding)) or np.any(np.isinf(self.embedding)):
            return False
        
        # Check if not all zeros
        if np.allclose(self.embedding, 0):
            return False
        
        return True