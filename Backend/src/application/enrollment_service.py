"""Enrollment service for voice biometric enrollment."""

import numpy as np
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..domain.model.VoiceSignature import VoiceSignature
from ..domain.repositories.VoiceTemplateRepositoryPort import VoiceTemplateRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import UserId, VoiceEmbedding, AuditAction
from ..shared.constants.biometric_constants import MIN_ENROLLMENT_SAMPLES, MAX_ENROLLMENT_SAMPLES


class EnrollmentService:
    """Service for handling voice biometric enrollment using Builder pattern concepts."""
    
    def __init__(
        self,
        voice_repo: VoiceTemplateRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
    
    async def start_enrollment(
        self,
        user_id: Optional[UserId] = None,
        external_ref: Optional[str] = None
    ) -> UserId:
        """Start enrollment process for a user."""
        
        # Create user if doesn't exist
        if user_id is None:
            if external_ref:
                existing_user = await self._user_repo.get_user_by_external_ref(external_ref)
                if existing_user:
                    user_id = existing_user['id']
                else:
                    user_id = await self._user_repo.create_user(external_ref)
            else:
                user_id = await self._user_repo.create_user()
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Log enrollment start
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="enrollment",
            entity_id=str(user_id),
            metadata={"stage": "started"}
        )
        
        return user_id
    
    async def add_enrollment_sample(
        self,
        user_id: UserId,
        embedding: VoiceEmbedding,
        snr_db: Optional[float] = None,
        duration_sec: Optional[float] = None
    ) -> UUID:
        """Add an enrollment sample for a user."""
        
        # Validate embedding
        if not self._validate_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Check if user already has too many samples
        existing_samples = await self._voice_repo.get_enrollment_samples(user_id)
        if len(existing_samples) >= MAX_ENROLLMENT_SAMPLES:
            raise ValueError(f"Maximum enrollment samples ({MAX_ENROLLMENT_SAMPLES}) reached")
        
        # Store the sample
        sample_id = await self._voice_repo.save_enrollment_sample(
            user_id=user_id,
            embedding=embedding,
            snr_db=snr_db,
            duration_sec=duration_sec
        )
        
        # Log sample addition
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="enrollment_sample",
            entity_id=str(sample_id),
            metadata={
                "user_id": str(user_id),
                "sample_count": len(existing_samples) + 1,
                "snr_db": snr_db,
                "duration_sec": duration_sec
            }
        )
        
        return sample_id
    
    async def complete_enrollment(
        self,
        user_id: UserId,
        speaker_model_id: Optional[int] = None
    ) -> VoiceSignature:
        """Complete enrollment by creating final voiceprint from samples."""
        
        # Get all enrollment samples
        samples = await self._voice_repo.get_enrollment_samples(user_id)
        
        if len(samples) < MIN_ENROLLMENT_SAMPLES:
            raise ValueError(
                f"Insufficient enrollment samples. Need at least {MIN_ENROLLMENT_SAMPLES}, got {len(samples)}"
            )
        
        # Calculate average embedding
        embeddings = [np.array(sample['embedding']) for sample in samples]
        average_embedding = np.mean(embeddings, axis=0)
        
        # Normalize the embedding
        average_embedding = average_embedding / np.linalg.norm(average_embedding)
        
        # Check if user already has a voiceprint (re-enrollment)
        existing_voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if existing_voiceprint:
            # Save old voiceprint to history
            await self._voice_repo.save_voiceprint_history(existing_voiceprint)
        
        # Create new voiceprint
        voiceprint = VoiceSignature(
            id=uuid4(),
            user_id=user_id,
            embedding=average_embedding,
            created_at=datetime.now(),
            speaker_model_id=speaker_model_id
        )
        
        # Save the voiceprint
        if existing_voiceprint:
            await self._voice_repo.update_voiceprint(voiceprint)
        else:
            await self._voice_repo.save_voiceprint(voiceprint)
        
        # Calculate quality metrics
        quality_score = self._calculate_enrollment_quality(embeddings)
        
        # Log completion
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="voiceprint",
            entity_id=str(voiceprint.id),
            metadata={
                "user_id": str(user_id),
                "sample_count": len(samples),
                "quality_score": quality_score,
                "re_enrollment": existing_voiceprint is not None
            }
        )
        
        return voiceprint
    
    async def get_enrollment_status(self, user_id: UserId) -> dict:
        """Get current enrollment status for a user."""
        
        # Check if user exists
        if not await self._user_repo.user_exists(user_id):
            return {"status": "user_not_found"}
        
        # Get current voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        
        # Get enrollment samples
        samples = await self._voice_repo.get_enrollment_samples(user_id)
        
        if voiceprint:
            return {
                "status": "enrolled",
                "voiceprint_id": str(voiceprint.id),
                "created_at": voiceprint.created_at.isoformat(),
                "sample_count": len(samples)
            }
        elif samples:
            return {
                "status": "in_progress",
                "sample_count": len(samples),
                "samples_needed": max(0, MIN_ENROLLMENT_SAMPLES - len(samples))
            }
        else:
            return {
                "status": "not_started",
                "samples_needed": MIN_ENROLLMENT_SAMPLES
            }
    
    def _validate_embedding(self, embedding: VoiceEmbedding) -> bool:
        """Validate voice embedding."""
        if embedding is None:
            return False
        
        # Check shape (256-dimensional)
        if embedding.shape != (256,):
            return False
        
        # Check for NaN or infinity
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False
        
        # Check if not all zeros
        if np.allclose(embedding, 0):
            return False
        
        return True
    
    def _calculate_enrollment_quality(self, embeddings: List[np.ndarray]) -> float:
        """Calculate quality score for enrollment based on consistency."""
        if len(embeddings) < 2:
            return 0.5
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                # Cosine similarity
                norm_i = embeddings[i] / np.linalg.norm(embeddings[i])
                norm_j = embeddings[j] / np.linalg.norm(embeddings[j])
                sim = np.dot(norm_i, norm_j)
                similarities.append(max(0, sim))
        
        # Return average similarity as quality score
        return np.mean(similarities) if similarities else 0.5