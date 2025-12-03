"""Verification service with dynamic phrase support."""

import numpy as np
from typing import Dict, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import VoiceEmbedding, AuditAction, ChallengeId


class VerificationSession:
    """Represents an active verification session."""
    
    def __init__(self, user_id: UUID, verification_id: UUID, challenge: dict):
        self.user_id = user_id
        self.verification_id = verification_id
        self.challenge = challenge
        self.created_at = datetime.now(timezone.utc)


class MultiPhraseVerificationSession:
    """Represents an active multi-phrase verification session (3 phrases)."""
    
    def __init__(self, user_id: UUID, verification_id: UUID, challenges: list):
        self.user_id = user_id
        self.verification_id = verification_id
        self.challenges = challenges
        self.results: list[Dict] = []  # Store results for each challenge
        self.created_at = datetime.now(timezone.utc)


from .services.BiometricValidator import BiometricValidator


class VerificationServiceV2:
    """Service for voice biometric verification with dynamic phrases."""
    
    # In-memory sessions (in production, use Redis)
    _active_sessions: Dict[UUID, VerificationSession] = {}
    _active_multi_sessions: Dict[UUID, MultiPhraseVerificationSession] = {}
    
    def __init__(
        self,
        voice_repo: VoiceSignatureRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        challenge_service,  # ChallengeService
        biometric_validator: BiometricValidator,
        similarity_threshold: float = 0.75,
        anti_spoofing_threshold: float = 0.5
    ):
        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._challenge_service = challenge_service
        self._biometric_validator = biometric_validator
        self._similarity_threshold = similarity_threshold
        self._anti_spoofing_threshold = anti_spoofing_threshold
    
    async def start_verification(
        self,
        user_id: UUID,
        difficulty: str = "medium"
    ) -> Dict:
        """Start verification and get a challenge for the user."""
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Check if user has voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if not voiceprint:
            raise ValueError(f"User {user_id} is not enrolled")
        
        # Create challenge for verification
        challenge = await self._challenge_service.create_challenge(
            user_id=user_id,
            difficulty=difficulty
        )
        
        # Create verification session
        verification_id = uuid4()
        session = VerificationSession(user_id, verification_id, challenge)
        self._active_sessions[verification_id] = session
        
        # Log verification start
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="verification",
            entity_id=str(verification_id),
            metadata={
                "user_id": str(user_id),
                "challenge_id": str(challenge["challenge_id"]),
                "difficulty": difficulty
            }
        )
        
        return {
            "verification_id": str(verification_id),
            "user_id": str(user_id),
            "challenge_id": str(challenge["challenge_id"]),
            "phrase": challenge["phrase"],
            "phrase_id": str(challenge["phrase_id"]),
            "expires_at": challenge["expires_at"]
        }
    
    async def verify_voice(
        self,
        verification_id: UUID,
        challenge_id: ChallengeId,
        embedding: VoiceEmbedding,
        anti_spoofing_score: Optional[float] = None
    ) -> Dict:
        """Verify voice with challenge validation."""
        
        # Get session
        session = self._active_sessions.get(verification_id)
        if not session:
            raise ValueError("Invalid or expired verification session")
        
        # Verify challenge matches
        if challenge_id != session.challenge["challenge_id"]:
            raise ValueError("Challenge does not match verification session")
        
        # Validate challenge (strict validation)
        is_valid, reason = await self._challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=session.user_id
        )
        
        if not is_valid:
            raise ValueError(f"Invalid challenge: {reason}")
        
        # Validate embedding
        if not self._biometric_validator.is_valid_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Get user's voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(session.user_id)
        if not voiceprint:
            raise ValueError("User voiceprint not found")
        
        # Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._biometric_validator.calculate_similarity(embedding, stored_embedding)
        
        # Check anti-spoofing
        is_live = True
        if anti_spoofing_score is not None:
            is_live = anti_spoofing_score < self._anti_spoofing_threshold
        
        # Make decision
        is_verified = (
            similarity_score >= self._similarity_threshold and
            is_live
        )
        
        # Mark challenge as used
        await self._challenge_service.mark_challenge_used(challenge_id)
        
        # Log verification result
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="verification_result",
            entity_id=str(verification_id),
            success=is_verified,
            metadata={
                "user_id": str(session.user_id),
                "challenge_id": str(challenge_id),
                "similarity_score": float(similarity_score),
                "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
                "is_verified": is_verified,
                "is_live": is_live
            }
        )
        
        # Save verification attempt
        # TODO: Uncomment when verification_attempt table is added to schema
        # await self._voice_repo.save_verification_attempt(
        #     user_id=session.user_id,
        #     embedding=embedding,
        #     similarity_score=float(similarity_score),
        #     is_verified=is_verified
        # )
        
        
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
        if not self._biometric_validator.is_valid_embedding(embedding):
            raise ValueError("Invalid voice embedding")
        
        # Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._biometric_validator.calculate_similarity(embedding, stored_embedding)
        
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
        # TODO: Uncomment when verification_attempt table is added to schema
        # await self._voice_repo.save_verification_attempt(
        #     user_id=user_id,
        #     embedding=embedding,
        #     similarity_score=float(similarity_score),
        #     is_verified=is_verified
        # )
        
        
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
        
        # Get verification attempts from audit log
        # We look for verification results
        activity = await self._audit_repo.get_user_activity(str(user_id), hours=24*30, limit=limit)
        
        attempts = []
        for log in activity:
            if log.get('action') == 'verify' and log.get('entity_type') == 'verification_result':
                metadata = log.get('metadata', {})
                attempts.append({
                    "id": log.get('entity_id'),
                    "date": log.get('timestamp').strftime("%Y-%m-%d %H:%M") if log.get('timestamp') else "",
                    "result": "success" if log.get('success') else "failed",
                    "score": int(metadata.get('similarity_score', 0) * 100) if metadata.get('similarity_score') else 0,
                    "method": "Frase Aleatoria" # Default for now, could be extracted from metadata if available
                })
        
        return {
            "user_id": str(user_id),
            "total_attempts": len(attempts),
            "recent_attempts": attempts
        }
    
    async def start_multi_phrase_verification(
        self,
        user_id: UUID,
        difficulty: str = "medium"
    ) -> Dict:
        """Start multi-phrase verification (3 challenges)."""
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Check if user has voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(user_id)
        if not voiceprint:
            raise ValueError(f"User {user_id} is not enrolled")
        
        # Force difficulty to be medium or hard only (ignore easy)
        # For verification, we want more challenging phrases
        if difficulty not in ['medium', 'hard']:
            difficulty = 'medium'
        
        # Create 3 challenges for verification (batch operation)
        challenges = await self._challenge_service.create_challenge_batch(
            user_id=user_id,
            count=3,
            difficulty=difficulty
        )
        
        if len(challenges) < 3:
            raise ValueError("Not enough challenges created for multi-phrase verification")
        
        # Create verification session
        verification_id = uuid4()
        session = MultiPhraseVerificationSession(
            user_id, 
            verification_id,
            challenges
        )
        self._active_multi_sessions[verification_id] = session
        
        # Log verification start
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.VERIFY,
            entity_type="multi_verification",
            entity_id=str(verification_id),
            metadata={
                "user_id": str(user_id),
                "challenge_count": 3,
                "difficulty": difficulty
            }
        )
        
        return {
            "verification_id": str(verification_id),
            "user_id": str(user_id),
            "challenges": session.challenges,
            "total_phrases": 3
        }
    
    async def verify_phrase(
        self,
        verification_id: UUID,
        challenge_id: ChallengeId,
        phrase_number: int,
        embedding: VoiceEmbedding,
        anti_spoofing_score: Optional[float],
        asr_confidence: float
    ) -> Dict:
        """Verify a single challenge in multi-phrase verification."""
        
        # Get session
        session = self._active_multi_sessions.get(verification_id)
        if not session:
            raise ValueError("Invalid or expired verification session")
        
        # Validate challenge
        is_valid, reason = await self._challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=session.user_id
        )
        
        if not is_valid:
            raise ValueError(f"Invalid challenge: {reason}")
        
        # 1. Check anti-spoofing FIRST (immediate rejection)
        if anti_spoofing_score is not None:
            is_spoof = anti_spoofing_score > self._anti_spoofing_threshold
            if is_spoof:
                # Clean up session and reject immediately
                del self._active_multi_sessions[verification_id]
                
                await self._audit_repo.log_event(
                    actor="system",
                    action=AuditAction.VERIFY,
                    entity_type="multi_verification_rejected",
                    entity_id=str(verification_id),
                    success=False,
                    metadata={
                        "user_id": str(session.user_id),
                        "phrase_number": phrase_number,
                        "reason": "spoof_detected",
                        "anti_spoofing_score": anti_spoofing_score
                    }
                )
                
                return {
                    "rejected": True,
                    "reason": "spoof_detected",
                    "anti_spoofing_score": anti_spoofing_score,
                    "phrase_number": phrase_number,
                    "is_complete": True,
                    "individual_score": 0.0
                }
        
        # 2. Apply ASR penalty if confidence < 70%
        asr_penalty = 1.0 if asr_confidence >= 0.70 else 0.5
        
        # 3. Get user's voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(session.user_id)
        if not voiceprint:
            raise ValueError("User voiceprint not found")
        
        # 4. Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._biometric_validator.calculate_similarity(embedding, stored_embedding)
        
        # 5. Apply ASR penalty to get final score for this phrase
        final_score = similarity_score * asr_penalty
        
        # 6. Store result in session
        session.results.append({
            "phrase_number": phrase_number,
            "challenge_id": str(challenge_id),
            "similarity_score": float(similarity_score),
            "asr_confidence": float(asr_confidence),
            "asr_penalty": asr_penalty,
            "final_score": float(final_score)
        })
        
        # Mark challenge as used
        await self._challenge_service.mark_challenge_used(challenge_id)
        
        # 7. Check if this is the last phrase
        is_complete = len(session.results) >= 3
        
        if is_complete:
            # Calculate average score
            avg_score = sum(r["final_score"] for r in session.results) / 3
            is_verified = avg_score >= self._similarity_threshold
            
            # Log final verification result
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.VERIFY,
                entity_type="multi_verification_complete",
                entity_id=str(verification_id),
                success=is_verified,
                metadata={
                    "user_id": str(session.user_id),
                    "average_score": avg_score,
                    "is_verified": is_verified,
                    "results": session.results
                }
            )
            
            # Clean up session
            del self._active_multi_sessions[verification_id]
            
            return {
                "is_complete": True,
                "phrase_number": phrase_number,
                "individual_score": float(final_score),
                "average_score": float(avg_score),
                "is_verified": is_verified,
                "threshold_used": self._similarity_threshold,
                "all_results": session.results
            }
        
        # Not complete yet
        return {
            "is_complete": False,
            "phrase_number": phrase_number,
            "individual_score": float(final_score),
            "phrases_remaining": 3 - len(session.results)
        }


    async def get_verification_history(self, user_id: UUID, limit: int = 10) -> List[Dict]:
        """Get verification history for a user."""
        # TODO: Implement actual database query when verification_results table is created
        # For now, return empty list as placeholder
        logger.info(f"get_verification_history called for user_id={user_id}, limit={limit}")
        return []
