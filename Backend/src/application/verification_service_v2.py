"""Verification service with dynamic phrase support."""

import numpy as np
from typing import Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ..domain.repositories.VoiceTemplateRepositoryPort import VoiceTemplateRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..domain.repositories.PhraseRepositoryPort import PhraseRepositoryPort, PhraseUsageRepositoryPort
from ..shared.types.common_types import VoiceEmbedding, AuditAction


class VerificationSession:
    """Represents an active verification session."""
    
    def __init__(self, user_id: UUID, verification_id: UUID, phrase: dict):
        self.user_id = user_id
        self.verification_id = verification_id
        self.phrase = phrase
        self.created_at = datetime.now(timezone.utc)


class VerificationServiceV2:
    """Service for voice biometric verification with dynamic phrases."""
    
    # In-memory sessions (in production, use Redis)
    _active_sessions: Dict[UUID, VerificationSession] = {}
    
    def __init__(
        self,
        voice_repo: VoiceTemplateRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        phrase_repo: PhraseRepositoryPort,
        phrase_usage_repo: PhraseUsageRepositoryPort,
        similarity_threshold: float = 0.75,
        anti_spoofing_threshold: float = 0.5
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._phrase_repo = phrase_repo
        self._phrase_usage_repo = phrase_usage_repo
        self._similarity_threshold = similarity_threshold
        self._anti_spoofing_threshold = anti_spoofing_threshold
    
    async def start_verification(
        self,
        user_id: UUID,
        difficulty: str = "medium"
    ) -> Dict:
        """Start verification and get a phrase for the user."""
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Check if user has voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if not voiceprint:
            raise ValueError(f"User {user_id} is not enrolled")
        
        # Get random phrase for verification (exclude recently used)
        phrases = await self._phrase_repo.find_random(
            user_id=user_id,
            exclude_recent=True,
            difficulty=difficulty,
            language='es',
            count=1
        )
        
        if not phrases:
            raise ValueError("No phrases available for verification")
        
        phrase = phrases[0]
        phrase_dict = {
            "id": str(phrase.id),
            "text": phrase.text,
            "difficulty": phrase.difficulty,
            "word_count": phrase.word_count
        }
        
        # Create verification session
        verification_id = uuid4()
        session = VerificationSession(user_id, verification_id, phrase_dict)
        self._active_sessions[verification_id] = session
        
        # Log verification start
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="verification",
            entity_id=str(verification_id),
            metadata={
                "user_id": str(user_id),
                "phrase_id": phrase_dict["id"],
                "difficulty": difficulty
            }
        )
        
        return {
            "verification_id": str(verification_id),
            "user_id": str(user_id),
            "phrase": phrase_dict
        }
    
    async def verify_voice(
        self,
        verification_id: UUID,
        phrase_id: UUID,
        embedding: VoiceEmbedding,
        anti_spoofing_score: Optional[float] = None
    ) -> Dict:
        """Verify voice with phrase validation."""
        
        # Get session
        session = self._active_sessions.get(verification_id)
        if not session:
            raise ValueError("Invalid or expired verification session")
        
        # Verify phrase matches
        if str(phrase_id) != session.phrase["id"]:
            raise ValueError("Phrase does not match verification session")
        
        # Validate embedding
        if not self._validate_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Get user's voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(session.user_id)
        if not voiceprint:
            raise ValueError("User voiceprint not found")
        
        # Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._calculate_similarity(embedding, stored_embedding)
        
        # Check anti-spoofing
        is_live = True
        if anti_spoofing_score is not None:
            is_live = anti_spoofing_score < self._anti_spoofing_threshold
        
        # Make decision
        is_verified = (
            similarity_score >= self._similarity_threshold and
            is_live
        )
        
        # Record phrase usage
        await self._phrase_usage_repo.record_usage(
            phrase_id=phrase_id,
            user_id=session.user_id,
            used_for="verification"
        )
        
        # Log verification result
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="verification_result",
            entity_id=str(verification_id),
            success=is_verified,
            metadata={
                "user_id": str(session.user_id),
                "phrase_id": str(phrase_id),
                "similarity_score": float(similarity_score),
                "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
                "is_verified": is_verified,
                "is_live": is_live
            }
        )
        
        # Save verification attempt
        await self._voice_repo.save_verification_attempt(
            user_id=session.user_id,
            embedding=embedding,
            similarity_score=float(similarity_score),
            is_verified=is_verified
        )
        
        # Clean up session
        del self._active_sessions[verification_id]
        
        return {
            "verification_id": str(verification_id),
            "user_id": str(session.user_id),
            "is_verified": is_verified,
            "confidence_score": float(similarity_score),
            "similarity_score": float(similarity_score),
            "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
            "phrase_match": True,
            "is_live": is_live,
            "threshold_used": self._similarity_threshold
        }
    
    async def quick_verify(
        self,
        user_id: UUID,
        embedding: VoiceEmbedding,
        anti_spoofing_score: Optional[float] = None
    ) -> Dict:
        """Quick verification without phrase management (for simple use cases)."""
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Get voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if not voiceprint:
            raise ValueError(f"User {user_id} is not enrolled")
        
        # Validate embedding
        if not self._validate_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._calculate_similarity(embedding, stored_embedding)
        
        # Check anti-spoofing
        is_live = True
        if anti_spoofing_score is not None:
            is_live = anti_spoofing_score < self._anti_spoofing_threshold
        
        # Make decision
        is_verified = (
            similarity_score >= self._similarity_threshold and
            is_live
        )
        
        # Log verification
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="quick_verification",
            entity_id=str(user_id),
            success=is_verified,
            metadata={
                "similarity_score": float(similarity_score),
                "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
                "is_verified": is_verified
            }
        )
        
        # Save attempt
        await self._voice_repo.save_verification_attempt(
            user_id=user_id,
            embedding=embedding,
            similarity_score=float(similarity_score),
            is_verified=is_verified
        )
        
        return {
            "user_id": str(user_id),
            "is_verified": is_verified,
            "confidence_score": float(similarity_score),
            "similarity_score": float(similarity_score),
            "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
            "is_live": is_live,
            "threshold_used": self._similarity_threshold
        }
    
    async def get_verification_history(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> Dict:
        """Get verification history for a user."""
        
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Get verification attempts (would be implemented in voice_repo)
        # For now, return placeholder
        attempts = []
        
        return {
            "user_id": str(user_id),
            "total_attempts": len(attempts),
            "recent_attempts": attempts[:limit]
        }
    
    def _validate_embedding(self, embedding: VoiceEmbedding) -> bool:
        """Validate voice embedding."""
        if embedding is None:
            return False
        
        if embedding.shape != (256,):
            return False
        
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False
        
        if np.allclose(embedding, 0):
            return False
        
        return True
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        # Normalize embeddings
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(norm1, norm2)
        
        # Return value between 0 and 1
        return float(max(0, min(1, (similarity + 1) / 2)))
