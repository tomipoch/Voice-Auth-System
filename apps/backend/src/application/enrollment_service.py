"""Enrollment service with dynamic phrase support and persistent sessions."""

import numpy as np
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from ..domain.model.VoiceSignature import VoiceSignature
from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import UserId, VoiceEmbedding, AuditAction, ChallengeId
from ..shared.constants.biometric_constants import MIN_ENROLLMENT_SAMPLES, MAX_ENROLLMENT_SAMPLES

logger = logging.getLogger(__name__)


from .services.BiometricValidator import BiometricValidator


class EnrollmentService:
    """Service for handling voice biometric enrollment with dynamic phrases.
    
    Sessions are now persisted in the database, so they survive server restarts.
    """
    
    def __init__(
        self,
        voice_repo: VoiceSignatureRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        challenge_service,  # ChallengeService
        biometric_validator: BiometricValidator,
        session_repo=None  # PostgresEnrollmentSessionRepository (optional for backwards compat)
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._challenge_service = challenge_service
        self._biometric_validator = biometric_validator
        self._session_repo = session_repo
        # Fallback in-memory sessions (for backwards compatibility if no session_repo)
        self._active_sessions: Dict[UUID, dict] = {}
    
    async def _get_session(self, enrollment_id: UUID) -> Optional[dict]:
        """Get session from database or memory."""
        if self._session_repo:
            return await self._session_repo.get_session(enrollment_id)
        return self._active_sessions.get(enrollment_id)
    
    async def _save_session(self, enrollment_id: UUID, user_id: UUID, challenges: List[dict]) -> None:
        """Save session to database or memory."""
        if self._session_repo:
            await self._session_repo.create_session(enrollment_id, user_id, challenges)
        else:
            self._active_sessions[enrollment_id] = {
                "id": enrollment_id,
                "user_id": user_id,
                "challenges": challenges,
                "samples_collected": 0,
                "challenge_index": 0,
                "created_at": datetime.now(timezone.utc)
            }
    
    async def _update_session(self, enrollment_id: UUID, samples_collected: int, challenge_index: int) -> None:
        """Update session progress."""
        if self._session_repo:
            await self._session_repo.update_session(enrollment_id, samples_collected, challenge_index)
        else:
            if enrollment_id in self._active_sessions:
                self._active_sessions[enrollment_id]["samples_collected"] = samples_collected
                self._active_sessions[enrollment_id]["challenge_index"] = challenge_index
    
    async def _delete_session(self, enrollment_id: UUID) -> None:
        """Delete/complete session."""
        if self._session_repo:
            await self._session_repo.complete_session(enrollment_id)
        else:
            self._active_sessions.pop(enrollment_id, None)
    
    async def start_enrollment(
        self,
        user_id: Optional[UUID] = None,
        external_ref: Optional[str] = None,
        difficulty: str = "medium",
        force_overwrite: bool = False
    ) -> Dict:
        """Start enrollment process for a user."""
        # Create or get user if not provided
        if not user_id:
            # First check if user with external_ref already exists
            if external_ref:
                existing_user = await self._user_repo.get_user_by_external_ref(external_ref)
                if existing_user:
                    user_id = existing_user.get("id") or existing_user.get("user_id")
                    if isinstance(user_id, str):
                        user_id = UUID(user_id)
                    logger.info(f"Found existing user with external_ref {external_ref}: {user_id}")
                else:
                    user_id = await self._user_repo.create_user(external_ref=external_ref)
                    logger.info(f"Created new user with external_ref {external_ref}: {user_id}")
            else:
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
        
        # Create enrollment session (stored in database)
        enrollment_id = uuid4()
        await self._save_session(enrollment_id, user_id, challenges)
        
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
        
        logger.info(f"Started enrollment session {enrollment_id} for user {user_id}")
        
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
        
        # Get session from database
        session = await self._get_session(enrollment_id)
        if not session:
            raise ValueError("Invalid or expired enrollment session")
        
        user_id = session["user_id"]
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        challenges = session["challenges"]
        samples_collected = session["samples_collected"]
        challenge_index = session["challenge_index"]
        
        # Validate embedding
        if not self._biometric_validator.is_valid_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Verify challenge belongs to this enrollment (flexible comparison)
        challenge_id_str = str(challenge_id)
        challenge_found = any(
            str(c.get("challenge_id", "")) == challenge_id_str for c in challenges
        )
        
        if not challenge_found:
            logger.warning(f"Challenge {challenge_id_str} not found. Available: {[c.get('challenge_id') for c in challenges]}")
            raise ValueError("Challenge does not belong to this enrollment session")
        
        # Validate challenge (strict validation)
        is_valid, reason = await self._challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        if not is_valid:
            raise ValueError(f"Invalid challenge: {reason}")
        
        # Store the sample
        sample_id = await self._voice_repo.save_enrollment_sample(
            user_id=user_id,
            embedding=embedding,
            snr_db=snr_db,
            duration_sec=duration_sec
        )
        
        # Mark challenge as used
        await self._challenge_service.mark_challenge_used(challenge_id)
        
        # Update session
        samples_collected += 1
        challenge_index += 1
        await self._update_session(enrollment_id, samples_collected, challenge_index)
        
        # Check if enrollment is complete
        is_complete = samples_collected >= MIN_ENROLLMENT_SAMPLES
        next_challenge = None if is_complete else (
            challenges[challenge_index] 
            if challenge_index < len(challenges) 
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
                "user_id": str(user_id),
                "challenge_id": str(challenge_id),
                "sample_number": samples_collected,
                "snr_db": snr_db,
                "duration_sec": duration_sec
            }
        )
        
        logger.info(f"Added sample {samples_collected}/{MIN_ENROLLMENT_SAMPLES} for enrollment {enrollment_id}")
        
        return {
            "sample_id": str(sample_id),
            "samples_completed": samples_collected,
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
        
        # Get session from database
        session = await self._get_session(enrollment_id)
        if not session:
            raise ValueError("Invalid or expired enrollment session")
        
        user_id = session["user_id"]
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        samples_collected = session["samples_collected"]
        
        if samples_collected < MIN_ENROLLMENT_SAMPLES:
            raise ValueError(
                f"Insufficient samples. Need {MIN_ENROLLMENT_SAMPLES}, got {samples_collected}"
            )
        
        # Get all enrollment samples
        samples = await self._voice_repo.get_enrollment_samples(user_id)
        
        # Calculate average embedding
        embeddings = [np.array(sample['embedding']) for sample in samples[-MIN_ENROLLMENT_SAMPLES:]]
        average_embedding = np.mean(embeddings, axis=0)
        average_embedding = average_embedding / np.linalg.norm(average_embedding)
        
        # Check if user already has a voiceprint
        existing_voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if existing_voiceprint:
            await self._voice_repo.save_voiceprint_history(existing_voiceprint)
        
        # Create voiceprint
        voiceprint = VoiceSignature(
            id=uuid4(),
            user_id=user_id,
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
                "user_id": str(user_id),
                "quality_score": quality_score,
                "samples_used": len(embeddings)
            }
        )
        
        # Clean up session
        await self._delete_session(enrollment_id)
        
        logger.info(f"Completed enrollment {enrollment_id} with quality {quality_score:.2f}")
        
        return {
            "voiceprint_id": str(voiceprint.id),
            "user_id": str(user_id),
            "quality_score": quality_score,
            "samples_used": len(embeddings)
        }
    
    async def get_enrollment_status(self, user_id: UUID) -> Dict:
        """Get enrollment status for a user."""
        
        if not await self._user_repo.user_exists(user_id):
            return {
                "user_id": str(user_id),
                "enrollment_id": None,
                "is_enrolled": False,
                "samples_count": 0,
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": [],
                "created_at": None
            }
        
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        samples = await self._voice_repo.get_enrollment_samples(user_id)
        
        # Get phrases used (could query phrase_usage table in future)
        phrase_usages = []
        
        if voiceprint:
            return {
                "user_id": str(user_id),
                "enrollment_id": None,
                "is_enrolled": True,
                "samples_count": len(samples),
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": phrase_usages,
                "created_at": voiceprint.created_at.isoformat()
            }
        elif samples:
            return {
                "user_id": str(user_id),
                "enrollment_id": None,
                "is_enrolled": False,
                "samples_count": len(samples),
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": phrase_usages,
                "created_at": None
            }
        else:
            return {
                "user_id": str(user_id),
                "enrollment_id": None,
                "is_enrolled": False,
                "samples_count": 0,
                "required_samples": MIN_ENROLLMENT_SAMPLES,
                "phrases_used": [],
                "created_at": None
            }
    
    def get_session(self, enrollment_id: UUID) -> Optional[dict]:
        """Get an active enrollment session by ID (sync fallback for in-memory)."""
        return self._active_sessions.get(enrollment_id)
    
    async def get_session_async(self, enrollment_id: UUID) -> Optional[dict]:
        """Get an active enrollment session by ID (async, from database)."""
        return await self._get_session(enrollment_id)
    
    async def get_session_user(self, enrollment_id: UUID) -> Optional[Dict]:
        """Get user data for an active enrollment session."""
        session = await self._get_session(enrollment_id)
        if session:
            user_id = session["user_id"]
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            return await self._user_repo.get_user(user_id)
        return None

    async def delete_enrollment(self, user_id: UUID) -> Dict:
        """Delete user's voice enrollment (voiceprint).
        
        Args:
            user_id: UUID of the user
            
        Returns:
            dict with success status and message
        """
        try:
            # Check if user exists and has enrollment
            user = await self._user_repo.get_user(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Check if voiceprint exists
            voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
            if not voiceprint:
                raise ValueError("No enrollment found for this user")
            
            # Delete voiceprint from database
            await self._voice_repo.delete_voiceprint(user_id)
            
            # Clean up any active sessions for this user
            if self._session_repo:
                await self._session_repo.delete_user_sessions(user_id)
            
            # Log audit event
            await self._audit_repo.log_action(
                user_id=user_id,
                action=AuditAction.ENROLLMENT_DELETED,
                details={"deleted_at": datetime.now(timezone.utc).isoformat()}
            )
            
            logger.info(f"Deleted enrollment for user {user_id}")
            
            return {
                "success": True,
                "message": "Voice enrollment deleted successfully"
            }
            
        except ValueError as e:
            logger.error(f"Error deleting enrollment for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting enrollment for user {user_id}: {str(e)}")
            raise ValueError(f"Failed to delete enrollment: {str(e)}")
    
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
