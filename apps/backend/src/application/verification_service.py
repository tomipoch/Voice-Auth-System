"""Verification service with dynamic phrase support."""

import numpy as np
import logging
import difflib
import json
from typing import Dict, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ..domain.repositories.voice_signature_repository_port import VoiceSignatureRepositoryPort
from ..domain.repositories.user_repository_port import UserRepositoryPort
from ..domain.repositories.audit_log_repository_port import AuditLogRepositoryPort
from ..domain.repositories.verification_attempt_repository_port import (
    VerificationAttemptRepositoryPort,
)
from ..domain.repositories.model_version_repository_port import ModelVersionRepositoryPort
from ..shared.types.common_types import VoiceEmbedding, AuditAction, ChallengeId

logger = logging.getLogger(__name__)


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


from .services.biometric_validator import BiometricValidator


class VerificationService:
    """Service for voice biometric verification with dynamic phrases."""
    
    def __init__(
        self,
        voice_repo: VoiceSignatureRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        challenge_service,  # ChallengeService
        biometric_validator: BiometricValidator,
        attempt_repo: Optional[VerificationAttemptRepositoryPort] = None,
        model_version_repo: Optional[ModelVersionRepositoryPort] = None,
        similarity_threshold: Optional[float] = None,
        anti_spoofing_threshold: Optional[float] = None,
    ):
        from ..config import SIMILARITY_THRESHOLD, ANTI_SPOOFING_THRESHOLD

        self._voice_repo = voice_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._challenge_service = challenge_service
        self._biometric_validator = biometric_validator
        self._attempt_repo = attempt_repo
        self._model_version_repo = model_version_repo
        self._similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else SIMILARITY_THRESHOLD
        )
        self._anti_spoofing_threshold = (
            anti_spoofing_threshold
            if anti_spoofing_threshold is not None
            else ANTI_SPOOFING_THRESHOLD
        )
        # In-memory sessions (in production, use Redis)
        # Moved to instance variables to avoid sharing state between instances
        self._active_sessions: Dict[UUID, VerificationSession] = {}
        self._active_multi_sessions: Dict[UUID, MultiPhraseVerificationSession] = {}
    
    def _map_reason(self, is_verified: bool, is_live: bool, phrase_match: bool) -> str:
        """Mapea el resultado de la verificación al enum auth_reason."""
        if is_verified:
            return "ok"
        if not is_live:
            return "spoof"
        if not phrase_match:
            return "bad_phrase"
        return "low_similarity"

    async def _persist_attempt(
        self,
        *,
        user_id: UUID,
        accept: bool,
        reason: str,
        similarity: float,
        spoof_prob: float,
        phrase_match: float,
        phrase_ok: bool,
        policy_id: str,
        client_id: Optional[UUID] = None,
        challenge_id: Optional[UUID] = None,
        audio_bytes: Optional[bytes] = None,
        total_latency_ms: Optional[int] = None,
    ) -> None:
        """Persiste el intento en auth_attempt + scores (+ audio_blob si keep_audio)."""
        if self._attempt_repo is None:
            return
        audio_id = None
        if audio_bytes is not None:
            try:
                policy = await self._user_repo.get_user_policy(user_id)
            except Exception:
                policy = None
            if policy and policy.get("keep_audio"):
                audio_id = await self._attempt_repo.save_audio_blob(audio_bytes, "audio/wav")
        model_ids = {"speaker": None, "antispoof": None, "asr": None}
        if self._model_version_repo is not None:
            for kind in ("speaker", "antispoof", "asr"):
                model_ids[kind] = await self._model_version_repo.get_model_id(kind)
        await self._attempt_repo.record_attempt(
            user_id=user_id,
            client_id=client_id,
            challenge_id=challenge_id,
            audio_id=audio_id,
            accept=accept,
            reason=reason,
            policy_id=policy_id,
            total_latency_ms=total_latency_ms,
            similarity=float(similarity),
            spoof_prob=float(spoof_prob),
            phrase_match=float(phrase_match),
            phrase_ok=bool(phrase_ok),
            speaker_model_id=model_ids.get("speaker"),
            antispoof_model_id=model_ids.get("antispoof"),
            asr_model_id=model_ids.get("asr"),
        )

    def _calculate_phrase_similarity(self, expected: str, transcribed: str) -> float:
        """Calculate similarity between expected and transcribed phrases."""
        norm_expected = expected.lower().strip()
        norm_transcribed = transcribed.lower().strip()
        return difflib.SequenceMatcher(None, norm_expected, norm_transcribed).ratio()
    
    def _calculate_composite_score(
        self,
        similarity_score: float,
        anti_spoofing_score: Optional[float],
        phrase_match_score: float
    ) -> float:
        """Calculate weighted composite verification score."""
        # Speaker: 60%, Anti-spoof: 20%, ASR: 20%
        w_speaker, w_antispoof, w_asr = 0.6, 0.2, 0.2
        genuineness_score = 1.0 - (anti_spoofing_score if anti_spoofing_score else 0.0)
        return (
            similarity_score * w_speaker +
            genuineness_score * w_antispoof +
            phrase_match_score * w_asr
        )
    
    def _is_verification_passed(
        self,
        similarity_score: float,
        is_live: bool,
        phrase_match: bool
    ) -> bool:
        """Determine if verification passed based on all checks."""
        return (
            similarity_score >= self._similarity_threshold and
            is_live and
            phrase_match
        )
    
    def _get_phrase_match_result(
        self,
        transcribed_text: Optional[str],
        expected_phrase: Optional[str]
    ) -> tuple[float, bool]:
        """Calculate phrase match score and result."""
        if not transcribed_text or not expected_phrase:
            return 0.0, True
        score = self._calculate_phrase_similarity(expected_phrase, transcribed_text)
        return score, score >= 0.7  # 70% threshold
    
    def _parse_log_metadata(self, metadata) -> dict:
        """Parse metadata from log entry (handles JSON strings)."""
        from ..shared.json_metadata import parse_json_metadata
        return parse_json_metadata(metadata)
    
    def _transform_log_to_attempt(self, log: dict) -> Optional[dict]:
        """Transform a single audit log entry to verification attempt format."""
        action = log.get('action')
        entity_type = log.get('entity_type')
        valid_actions = {AuditAction.VERIFY.value, 'verify', 'VERIFICATION'}
        valid_types = {'verification_result', 'multi_verification_complete', 'quick_verification'}
        
        if action not in valid_actions or entity_type not in valid_types:
            return None
        
        metadata = self._parse_log_metadata(log.get('metadata', {}))
        
        # Extract score based on verification type
        if entity_type == 'multi_verification_complete':
            score = int(metadata.get('average_score', 0) * 100)
        else:
            score = int(metadata.get('similarity_score', 0) * 100)
        
        timestamp = log.get('timestamp')
        return {
            "id": log.get('entity_id'),
            "date": timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else "",
            "result": "success" if log.get('success') else "failed",
            "score": score,
            "method": "Multi-Frase" if entity_type == 'multi_verification_complete' else "Frase Aleatoria",
            "details": metadata
        }
    
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
        anti_spoofing_score: Optional[float] = None,
        transcribed_text: Optional[str] = None,
        expected_phrase: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        client_id: Optional[UUID] = None,
        total_latency_ms: Optional[int] = None,
    ) -> Dict:
        """Verify voice with challenge validation and optional phrase matching."""
        
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
        
        # Calculate phrase match score using helper
        phrase_match_score, phrase_match = self._get_phrase_match_result(
            transcribed_text, expected_phrase
        )
        
        # Check anti-spoofing
        is_live = anti_spoofing_score is None or anti_spoofing_score < self._anti_spoofing_threshold
        
        # Calculate composite score using helper
        composite_score = self._calculate_composite_score(
            similarity_score, anti_spoofing_score, phrase_match_score
        )
        
        # Make decision using helper
        is_verified = self._is_verification_passed(similarity_score, is_live, phrase_match)
        
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
                "phrase_match_score": float(phrase_match_score),
                "composite_score": float(composite_score),
                "is_verified": is_verified,
                "is_live": is_live,
                "phrase_match": phrase_match
            }
        )
        
        # Log to evaluation system if active
        try:
            from evaluation.evaluation_logger import evaluation_logger
            if evaluation_logger.enabled:
                evaluation_logger.log_verification_attempt(
                    user_id=str(session.user_id),
                    similarity_score=float(similarity_score),
                    spoof_probability=float(anti_spoofing_score) if anti_spoofing_score else None,
                    system_decision="accepted" if is_verified else "rejected",
                    threshold_used=self._similarity_threshold,
                    challenge_id=str(challenge_id),
                    phrase_match_score=float(phrase_match_score)
                )
        except Exception as exc:
            logger.warning("Evaluation logger skipped verification attempt: %s", exc)
        
        # Persistir la decisión y las señales técnicas
        await self._persist_attempt(
            user_id=session.user_id,
            accept=is_verified,
            reason=self._map_reason(is_verified, is_live, phrase_match),
            similarity=similarity_score,
            spoof_prob=anti_spoofing_score if anti_spoofing_score is not None else 0.0,
            phrase_match=phrase_match_score,
            phrase_ok=phrase_match,
            policy_id="single",
            challenge_id=challenge_id,
            audio_bytes=audio_bytes,
            client_id=client_id,
            total_latency_ms=total_latency_ms,
        )

        # Clean up session
        del self._active_sessions[verification_id]
        
        return {
            "verification_id": str(verification_id),
            "user_id": str(session.user_id),
            "is_verified": is_verified,
            "confidence_score": float(composite_score),
            "similarity_score": float(similarity_score),
            "anti_spoofing_score": float(anti_spoofing_score) if anti_spoofing_score else None,
            "phrase_match": phrase_match,
            "phrase_match_score": float(phrase_match_score),
            "is_live": is_live,
            "threshold_used": self._similarity_threshold
        }
    
    async def quick_verify(
        self,
        user_id: UUID,
        embedding: VoiceEmbedding,
        anti_spoofing_score: Optional[float] = None,
        audio_bytes: Optional[bytes] = None,
        client_id: Optional[UUID] = None,
        total_latency_ms: Optional[int] = None,
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
        is_live = anti_spoofing_score is None or anti_spoofing_score < self._anti_spoofing_threshold
        
        # Make decision
        is_verified = similarity_score >= self._similarity_threshold and is_live
        
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

        # Persistir la decisión y las señales técnicas
        await self._persist_attempt(
            user_id=user_id,
            accept=is_verified,
            reason=self._map_reason(is_verified, is_live, phrase_match=True),
            similarity=similarity_score,
            spoof_prob=anti_spoofing_score if anti_spoofing_score is not None else 0.0,
            phrase_match=0.0,
            phrase_ok=True,
            policy_id="quick",
            audio_bytes=audio_bytes,
            client_id=client_id,
            total_latency_ms=total_latency_ms,
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
        
        # Get verification attempts from audit log (last 30 days)
        activity = await self._audit_repo.get_user_activity(str(user_id), hours=24*30, limit=limit)
        logger.debug(f"Retrieved {len(activity)} audit logs for user {user_id}")
        
        # Transform logs to attempt format using helper
        attempts = []
        for log in activity:
            attempt = self._transform_log_to_attempt(log)
            if attempt:
                attempts.append(attempt)
        
        return {
            "user_id": str(user_id),
            "total_attempts": len(attempts),
            "recent_attempts": attempts
        }
    
    def get_multi_session(self, verification_id: UUID) -> Optional[MultiPhraseVerificationSession]:
        """Get an active multi-phrase verification session by ID (public accessor)."""
        return self._active_multi_sessions.get(verification_id)
    
    async def get_multi_session_user(self, verification_id: UUID) -> Optional[Dict]:
        """Get user data for an active multi-phrase verification session."""
        session = self._active_multi_sessions.get(verification_id)
        if session:
            return await self._user_repo.get_user(session.user_id)
        return None
    
    async def get_phrase(self, phrase_id: UUID):
        """Get phrase by ID through challenge service (public accessor)."""
        return await self._challenge_service.get_phrase(phrase_id)
    
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
        transcribed_text: Optional[str] = None,
        anti_spoofing_score: Optional[float] = None,
        audio_bytes: Optional[bytes] = None,
        client_id: Optional[UUID] = None,
        total_latency_ms: Optional[int] = None,
    ) -> Dict:
        """Verify a single phrase implementation with real ASR scoring."""
        
        # Check active session
        session = self._active_multi_sessions.get(verification_id)
        if not session:
            raise ValueError("Invalid verification session")
        
        # 1. Validate session and retrieve expected phrase
        if phrase_number < 1 or phrase_number > 3:
            raise ValueError("Invalid phrase number")
            
        # Get expected phrase from session challenges
        # Challenge list is 0-indexed, phrase_number is 1-indexed
        current_challenge = session.challenges[phrase_number - 1]
        expected_phrase = current_challenge.get("phrase", "")
        
        # Calculate ASR Confidence using helper
        asr_confidence = self._calculate_phrase_similarity(expected_phrase, transcribed_text) if transcribed_text and expected_phrase else 0.0
        
        # Get user's voiceprint
        voiceprint = await self._voice_repo.get_voiceprint_by_user(session.user_id)
        if not voiceprint:
            raise ValueError("User voiceprint not found")
        
        # Calculate similarity
        stored_embedding = np.array(voiceprint.embedding)
        similarity_score = self._biometric_validator.calculate_similarity(embedding, stored_embedding)
        
        # Calculate Genuineness
        spoof_prob = float(anti_spoofing_score) if anti_spoofing_score is not None else 1.0
        
        # Calculate Final Composite Score using helper
        final_score = self._calculate_composite_score(similarity_score, spoof_prob, asr_confidence)
        
        # Store result in session
        session.results.append({
            "phrase_number": phrase_number,
            "challenge_id": str(challenge_id),
            "similarity_score": float(similarity_score),
            "asr_confidence": float(asr_confidence),
            "final_score": float(final_score),
            "anti_spoofing_score": float(spoof_prob),
            "genuineness_score": float(1.0 - spoof_prob)
        })
        
        # Mark challenge as used
        await self._challenge_service.mark_challenge_used(challenge_id)
        
        # 8. Check completion
        is_complete = len(session.results) >= 3
        
        if is_complete:
            # Calculate average score
            avg_score = sum(r["final_score"] for r in session.results) / 3
            is_verified = avg_score >= self._similarity_threshold
            avg_similarity = sum(r["similarity_score"] for r in session.results) / 3
            avg_phrase = sum(r["asr_confidence"] for r in session.results) / 3
            avg_spoof = sum(r["anti_spoofing_score"] for r in session.results) / 3
            any_spoof = any(
                r["anti_spoofing_score"] >= self._anti_spoofing_threshold
                for r in session.results
            )

            # Persistir un intento por verificación multi (decisión final)
            await self._persist_attempt(
                user_id=session.user_id,
                accept=is_verified,
                reason=("spoof" if any_spoof else
                        "ok" if is_verified else "low_similarity"),
                similarity=avg_similarity,
                spoof_prob=avg_spoof,
                phrase_match=avg_phrase,
                phrase_ok=is_verified,
                policy_id="multi",
                challenge_id=UUID(str(session.challenges[0]["challenge_id"])) if session.challenges else None,
                audio_bytes=audio_bytes,
                total_latency_ms=total_latency_ms,
                client_id=client_id,
            )

            # Clean up session (audit log saved in controller with IP, user agent)
            del self._active_multi_sessions[verification_id]

            return {
                "is_complete": True,
                "user_id": str(session.user_id),  # Added for audit logging
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



