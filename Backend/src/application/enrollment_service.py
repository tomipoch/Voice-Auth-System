"""Enrollment service with dynamic phrase support."""

import numpy as np
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ..domain.model.VoiceSignature import VoiceSignature
from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..domain.repositories.PhraseRepositoryPort import PhraseRepositoryPort, PhraseUsageRepositoryPort
from ..shared.types.common_types import UserId, VoiceEmbedding, AuditAction
from ..shared.constants.biometric_constants import MIN_ENROLLMENT_SAMPLES, MAX_ENROLLMENT_SAMPLES


class EnrollmentSession:
    """Represents an active enrollment session."""
    
    def __init__(self, user_id: UUID, enrollment_id: UUID, phrases: List[dict]):
        self.user_id = user_id
        self.enrollment_id = enrollment_id
        self.phrases = phrases
        self.samples_collected = 0
        self.phrase_index = 0
        self.created_at = datetime.now(timezone.utc)


from .services.BiometricValidator import BiometricValidator


class EnrollmentService:
    """Service for handling voice biometric enrollment with dynamic phrases."""
    
    # In-memory sessions (in production, use Redis or database)
    _active_sessions: Dict[UUID, EnrollmentSession] = {}
    
    def __init__(
        self,
        voice_repo: VoiceSignatureRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        phrase_repo: PhraseRepositoryPort,
        phrase_usage_repo: PhraseUsageRepositoryPort,
        biometric_validator: BiometricValidator
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._phrase_repo = phrase_repo
        self._phrase_usage_repo = phrase_usage_repo
        self._biometric_validator = biometric_validator
    
    async def start_enrollment(
        self,
        user_id: Optional[UUID] = None,
        external_ref: Optional[str] = None,
        difficulty: str = "medium"
    ) -> Dict:
        """Start enrollment process and get phrases for the user."""
        
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
        
        # Get random phrases for enrollment
        phrases = await self._phrase_repo.find_random(
            user_id=user_id,
            exclude_recent=True,
            difficulty=difficulty,
            language='es',
            count=MIN_ENROLLMENT_SAMPLES
        )
        
        if len(phrases) < MIN_ENROLLMENT_SAMPLES:
            raise ValueError(f"Not enough phrases available. Need {MIN_ENROLLMENT_SAMPLES}")
        
        # Convert phrases to dict
        phrases_dict = [
            {
                "id": str(phrase.id),
                "text": phrase.text,
                "difficulty": phrase.difficulty,
                "word_count": phrase.word_count
            }
            for phrase in phrases
        ]
        
        # Create enrollment session
        enrollment_id = uuid4()
        session = EnrollmentSession(user_id, enrollment_id, phrases_dict)
        self._active_sessions[enrollment_id] = session
        
        # Log enrollment start
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="enrollment",
            entity_id=str(enrollment_id),
            metadata={
                "user_id": str(user_id),
                "difficulty": difficulty,
                "phrase_count": len(phrases_dict)
            }
        )
        
        return {
            "enrollment_id": str(enrollment_id),
            "user_id": str(user_id),
            "phrases": phrases_dict,
            "required_samples": MIN_ENROLLMENT_SAMPLES
        }
    
    async def add_enrollment_sample(
        self,
        enrollment_id: UUID,
        phrase_id: UUID,
        embedding: VoiceEmbedding,
        snr_db: Optional[float] = None,
        duration_sec: Optional[float] = None
    ) -> Dict:
        """Add an enrollment sample with phrase validation."""
        
        # Get session
        session = self._active_sessions.get(enrollment_id)
        if not session:
            raise ValueError("Invalid or expired enrollment session")
        
        # Validate embedding
        if not self._biometric_validator.is_valid_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Verify phrase belongs to this enrollment
        phrase_found = any(p["id"] == str(phrase_id) for p in session.phrases)
        if not phrase_found:
            raise ValueError("Phrase does not belong to this enrollment session")
        
        # Store the sample
        sample_id = await self._voice_repo.save_enrollment_sample(
            user_id=session.user_id,
            embedding=embedding,
            snr_db=snr_db,
            duration_sec=duration_sec
        )
        
        # Record phrase usage
        await self._phrase_usage_repo.record_usage(
            phrase_id=phrase_id,
            user_id=session.user_id,
            used_for="enrollment"
        )
        
        # Update session
        session.samples_collected += 1
        session.phrase_index += 1
        
        # Check if enrollment is complete
        is_complete = session.samples_collected >= MIN_ENROLLMENT_SAMPLES
        next_phrase = None if is_complete else (
            session.phrases[session.phrase_index] 
            if session.phrase_index < len(session.phrases) 
            else None
        )
        
        # Log sample addition
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="enrollment_sample",
            entity_id=str(sample_id),
            metadata={
                "enrollment_id": str(enrollment_id),
                "user_id": str(session.user_id),
                "phrase_id": str(phrase_id),
                "sample_number": session.samples_collected,
                "snr_db": snr_db,
                "duration_sec": duration_sec
            }
        )
        
        return {
            "sample_id": str(sample_id),
            "samples_completed": session.samples_collected,
            "samples_required": MIN_ENROLLMENT_SAMPLES,
            "is_complete": is_complete,
            "next_phrase": next_phrase
        }
    
    async def complete_enrollment(
        self,
        enrollment_id: UUID,
        speaker_model_id: Optional[int] = None
    ) -> Dict:
        """Complete enrollment by creating final voiceprint."""
        
        # Get session
        session = self._active_sessions.get(enrollment_id)
        if not session:
            raise ValueError("Invalid or expired enrollment session")
        
        if session.samples_collected < MIN_ENROLLMENT_SAMPLES:
            raise ValueError(
                f"Insufficient samples. Need {MIN_ENROLLMENT_SAMPLES}, got {session.samples_collected}"
            )
        
        # Get all enrollment samples
        samples = await self._voice_repo.get_enrollment_samples(session.user_id)
        
        # Calculate average embedding
        embeddings = [np.array(sample['embedding']) for sample in samples[-MIN_ENROLLMENT_SAMPLES:]]
        average_embedding = np.mean(embeddings, axis=0)
        average_embedding = average_embedding / np.linalg.norm(average_embedding)
        
        # Check if user already has a voiceprint
        existing_voiceprint = await self._voice_repo.get_voiceprint_by_user(session.user_id)
        if existing_voiceprint:
            await self._voice_repo.save_voiceprint_history(existing_voiceprint)
        
        # Create voiceprint
        voiceprint = VoiceSignature(
            id=uuid4(),
            user_id=session.user_id,
            embedding=average_embedding,
            created_at=datetime.now(timezone.utc),
            speaker_model_id=speaker_model_id
        )
        
        # Save voiceprint
        if existing_voiceprint:
            await self._voice_repo.update_voiceprint(voiceprint)
        else:
            await self._voice_repo.save_voiceprint(voiceprint)
        
        # Calculate quality
        quality_score = self._calculate_enrollment_quality(embeddings)
        
        # Log completion
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.ENROLL,
            entity_type="voiceprint",
            entity_id=str(voiceprint.id),
            metadata={
                "enrollment_id": str(enrollment_id),
                "user_id": str(session.user_id),
                "quality_score": quality_score,
                "samples_used": len(embeddings)
            }
        )
        
        # Clean up session
        del self._active_sessions[enrollment_id]
        
        return {
            "voiceprint_id": str(voiceprint.id),
            "user_id": str(session.user_id),
            "quality_score": quality_score,
            "samples_used": len(embeddings)
        }
    
    async def get_enrollment_status(self, user_id: UUID) -> Dict:
        """Get enrollment status for a user."""
        
        if not await self._user_repo.user_exists(user_id):
            return {"status": "user_not_found"}
        
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        samples = await self._voice_repo.get_enrollment_samples(user_id)
        
        # Get phrases used
        phrase_usages = []
        # This would query phrase_usage table in real implementation
        
        if voiceprint:
            return {
                "status": "enrolled",
                "voiceprint_id": str(voiceprint.id),
                "created_at": voiceprint.created_at.isoformat(),
                "samples_count": len(samples),
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": phrase_usages
            }
        elif samples:
            return {
                "status": "in_progress",
                "samples_count": len(samples),
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": phrase_usages
            }
        else:
            return {
                "status": "not_started",
                "samples_count": 0,
                "required_samples": MIN_ENROLLMENT_SAMPLES
            }
    

    
    def _calculate_enrollment_quality(self, embeddings: List[np.ndarray]) -> float:
        """Calculate enrollment quality based on consistency."""
        if len(embeddings) < 2:
            return 0.5
        
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self._biometric_validator.calculate_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        return float(np.mean(similarities)) if similarities else 0.5
