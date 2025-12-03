"""Enrollment service with dynamic phrase support."""

import numpy as np
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ..domain.model.VoiceSignature import VoiceSignature
from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import UserId, VoiceEmbedding, AuditAction, ChallengeId
from ..shared.constants.biometric_constants import MIN_ENROLLMENT_SAMPLES, MAX_ENROLLMENT_SAMPLES


class EnrollmentSession:
    """Represents an active enrollment session."""
    
    def __init__(self, user_id: UUID, enrollment_id: UUID, challenges: List[dict]):
        self.user_id = user_id
        self.enrollment_id = enrollment_id
        self.challenges = challenges  # List of challenge dicts
        self.samples_collected = 0
        self.challenge_index = 0
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
        challenge_service,  # ChallengeService
        biometric_validator: BiometricValidator
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._challenge_service = challenge_service
        self._biometric_validator = biometric_validator
    
    async def start_enrollment(
        self,
        user_id: Optional[UUID] = None,
        external_ref: Optional[str] = None,
        difficulty: str = "medium",
        force_overwrite: bool = False
    ) -> Dict:
        """Start enrollment process for a user."""
        # Create user if not provided
        if not user_id:
            user_id = await self._user_repo.create_user(external_ref=external_ref)
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Check if user already has a voiceprint
        existing_voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        voiceprint_exists = existing_voiceprint is not None
        
        if voiceprint_exists and not force_overwrite:
            # Return response indicating voiceprint exists, but don't create enrollment
            return {
                "enrollment_id": "",
                "user_id": str(user_id),
                "challenges": [],
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "voiceprint_exists": True,
                "message": "User already has a voiceprint. Set force_overwrite=true to replace it."
            }
        
        # If force_overwrite is True and voiceprint exists, delete the old one
        if voiceprint_exists and force_overwrite:
            await self._voice_repo.delete_voiceprint(user_id)
            logger.info(f"Deleted existing voiceprint for user {user_id} (force_overwrite=True)")
        
        # Create challenges for enrollment (batch operation)
        challenges = await self._challenge_service.create_challenge_batch(
            user_id=user_id,
            count=MIN_ENROLLMENT_SAMPLES,
            difficulty=difficulty
        )
        
        if len(challenges) < MIN_ENROLLMENT_SAMPLES:
            raise ValueError(f"Not enough challenges created. Need {MIN_ENROLLMENT_SAMPLES}")
        
        # Create enrollment session
        enrollment_id = uuid4()
        session = EnrollmentSession(user_id, enrollment_id, challenges)
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
                "challenge_count": len(challenges)
            }
        )
        
        return {
            "enrollment_id": str(enrollment_id),
            "user_id": str(user_id),
            "challenges": challenges,
            "required_samples": MIN_ENROLLMENT_SAMPLES
        }
    
    async def add_enrollment_sample(
        self,
        enrollment_id: UUID,
        challenge_id: ChallengeId,
        embedding: VoiceEmbedding,
        snr_db: Optional[float] = None,
        duration_sec: Optional[float] = None
    ) -> Dict:
        """Add an enrollment sample with challenge validation."""
        
        # Get session
        session = self._active_sessions.get(enrollment_id)
        if not session:
            raise ValueError("Invalid or expired enrollment session")
        
        # Validate embedding
        if not self._biometric_validator.is_valid_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Verify challenge belongs to this enrollment
        challenge_found = any(c["challenge_id"] == challenge_id for c in session.challenges)
        if not challenge_found:
            raise ValueError("Challenge does not belong to this enrollment session")
        
        # Validate challenge (strict validation)
        is_valid, reason = await self._challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=session.user_id
        )
        
        if not is_valid:
            raise ValueError(f"Invalid challenge: {reason}")
        
        # Store the sample
        sample_id = await self._voice_repo.save_enrollment_sample(
            user_id=session.user_id,
            embedding=embedding,
            snr_db=snr_db,
            duration_sec=duration_sec
        )
        
        # Mark challenge as used
        await self._challenge_service.mark_challenge_used(challenge_id)
        
        # Update session
        session.samples_collected += 1
        session.challenge_index += 1
        
        # Check if enrollment is complete
        is_complete = session.samples_collected >= MIN_ENROLLMENT_SAMPLES
        next_challenge = None if is_complete else (
            session.challenges[session.challenge_index] 
            if session.challenge_index < len(session.challenges) 
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
                "challenge_id": str(challenge_id),
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
            "next_challenge": next_challenge
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
            created_at=datetime.now(timezone.utc)
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
