"""Challenge service for managing dynamic phrase challenges with database integration."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ..domain.repositories.ChallengeRepositoryPort import ChallengeRepositoryPort
from ..domain.repositories.PhraseRepositoryPort import PhraseRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from .phrase_quality_rules_service import PhraseQualityRulesService
from ..shared.types.common_types import UserId, ChallengeId, AuditAction

logger = logging.getLogger(__name__)


class ChallengeService:
    """Service for generating and managing dynamic voice challenges using phrase database."""
    
    def __init__(
        self,
        challenge_repo: ChallengeRepositoryPort,
        phrase_repo: PhraseRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        rules_service: PhraseQualityRulesService
    ):
        self._challenge_repo = challenge_repo
        self._phrase_repo = phrase_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._rules_service = rules_service
    
    async def create_challenge_batch(
        self,
        user_id: UserId,
        count: int = 3,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create multiple challenges at once (optimized for batch operations).
        
        Args:
            user_id: User UUID
            count: Number of challenges to create (default: 3)
            difficulty: Phrase difficulty level (easy/medium/hard)
            
        Returns:
            List of challenge dictionaries
        """
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Check rate limiting
        await self._check_rate_limits(user_id)
        
        # Get configuration from rules
        expiry_minutes = await self._rules_service.get_rule_value('challenge_expiry_minutes', default=5.0)
        exclude_recent = int(await self._rules_service.get_rule_value('exclude_recent_phrases', default=50.0))
        
        # Get recent phrase IDs to exclude
        recent_phrase_ids = await self._phrase_repo.get_recent_phrase_ids(
            user_id=user_id,
            limit=exclude_recent
        )
        
        # Get random phrases from database (1 query for all)
        # Note: find_random() uses exclude_recent=True by default, which excludes last 30 days
        phrases = await self._phrase_repo.find_random(
            user_id=user_id,
            count=count,
            difficulty=difficulty,
            language='es',
            exclude_recent=True  # This will exclude recent phrases automatically
        )
        
        if len(phrases) < count:
            # Fallback: allow repetition if not enough unique phrases
            logger.warning(f"Only {len(phrases)} unique phrases available, need {count}. Allowing repetition.")
            phrases = await self._phrase_repo.find_random(
                user_id=user_id,
                count=count,
                difficulty=difficulty,
                language='es',
                exclude_recent=False  # Allow repetition
            )
        
        if not phrases:
            raise ValueError("No phrases available for challenges")
        
        # Create challenges with difficulty-based expiration
        challenges = []
        for phrase in phrases:
            # Get timeout based on phrase difficulty
            from ..config import CHALLENGE_TIMEOUT
            timeout_seconds = CHALLENGE_TIMEOUT.get(phrase.difficulty, 90)  # Default to 90 seconds
            expires_at = datetime.now() + timedelta(seconds=timeout_seconds)
            
            # Create challenge in database
            challenge_id = await self._challenge_repo.create_challenge(
                user_id=user_id,
                phrase=phrase.text,
                phrase_id=phrase.id,
                expires_at=expires_at
            )
            
            # Note: Phrase usage tracking removed - not critical for challenge creation
            # Usage will be tracked when challenge is actually used in enrollment/verification

            
            # Log challenge creation
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.CREATE_CHALLENGE,
                entity_type="challenge",
                entity_id=str(challenge_id),
                metadata={
                    "user_id": str(user_id),
                    "phrase_id": str(phrase.id),
                    "phrase_length": len(phrase.text),
                    "difficulty": phrase.difficulty,
                    "expires_at": expires_at.isoformat()
                }
            )
            
            challenges.append({
                "challenge_id": challenge_id,
                "phrase": phrase.text,
                "phrase_id": phrase.id,
                "difficulty": phrase.difficulty,
                "expires_at": expires_at.isoformat(),
                "expires_in_seconds": int((expires_at - datetime.now()).total_seconds())
            })
        
        logger.info(f"Created {len(challenges)} challenges for user {user_id}")
        return challenges
    
    async def create_challenge(
        self,
        user_id: UserId,
        difficulty: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single challenge (convenience method).
        
        Args:
            user_id: User UUID
            difficulty: Phrase difficulty level (easy/medium/hard)
            
        Returns:
            Challenge dictionary
        """
        batch = await self.create_challenge_batch(
            user_id=user_id,
            count=1,
            difficulty=difficulty
        )
        
        return batch[0]
    
    async def get_challenge(self, challenge_id: ChallengeId) -> Optional[Dict[str, Any]]:
        """Get challenge details by ID."""
        return await self._challenge_repo.get_challenge(challenge_id)
    
    async def get_active_challenge(self, user_id: UserId) -> Optional[Dict[str, Any]]:
        """Get the most recent active challenge for a user."""
        return await self._challenge_repo.get_active_challenge(user_id)
    
    async def validate_challenge_strict(
        self, 
        challenge_id: ChallengeId, 
        user_id: UserId
    ) -> tuple[bool, str]:
        """
        Strict challenge validation with comprehensive checks.
        
        Args:
            challenge_id: Challenge UUID
            user_id: User UUID
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        # Get challenge
        challenge = await self._challenge_repo.get_challenge(challenge_id)
        if not challenge:
            return False, "Challenge not found"
        
        # Check if challenge belongs to user
        if challenge.get('user_id') != user_id:
            await self._audit_repo.log_event(
                actor=str(user_id),
                action=AuditAction.VERIFY,
                entity_type="challenge_validation",
                entity_id=str(challenge_id),
                metadata={"error": "user_mismatch", "expected_user": str(challenge.get('user_id'))}
            )
            return False, "Challenge does not belong to user"
        
        # Check if already used
        if challenge.get('used_at'):
            return False, "Challenge already used"
        
        # Check if expired
        expires_at = challenge.get('expires_at')
        if expires_at and datetime.now(timezone.utc) > expires_at:
            return False, "Challenge expired"
        
        return True, "Valid"
    
    async def mark_challenge_used(self, challenge_id: ChallengeId) -> None:
        """Mark a challenge as used."""
        await self._challenge_repo.mark_challenge_used(challenge_id)
    
    async def cleanup_expired_challenges(self) -> int:
        """Clean up expired challenges based on configured rules."""
        cleanup_hours = int(await self._rules_service.get_rule_value('cleanup_expired_after_hours', default=1.0))
        deleted_count = await self._challenge_repo.cleanup_expired_challenges(older_than_hours=cleanup_hours)
        
        if deleted_count > 0:
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.DELETE_USER,  # Using existing enum
                entity_type="challenge_cleanup",
                entity_id="expired_batch",
                metadata={"deleted_count": deleted_count, "older_than_hours": cleanup_hours}
            )
        
        return deleted_count
    
    async def cleanup_used_challenges(self) -> int:
        """Clean up used challenges based on configured rules."""
        cleanup_hours = int(await self._rules_service.get_rule_value('cleanup_used_after_hours', default=24.0))
        deleted_count = await self._challenge_repo.cleanup_used_challenges(older_than_hours=cleanup_hours)
        
        if deleted_count > 0:
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.DELETE_USER,  # Using existing enum
                entity_type="challenge_cleanup",
                entity_id="used_batch",
                metadata={"deleted_count": deleted_count, "older_than_hours": cleanup_hours}
            )
        
        return deleted_count
    
    async def analyze_phrase_performance(self) -> Dict[str, Any]:
        """
        Analyze phrase performance and auto-disable problematic phrases.
        Uses configurable rules from admin settings.
        
        Returns:
            Dictionary with analysis results
        """
        # Get thresholds from rules
        min_success_rate = await self._rules_service.get_rule_value('min_success_rate', default=0.70)
        min_asr_score = await self._rules_service.get_rule_value('min_asr_score', default=0.80)
        min_phrase_ok_rate = await self._rules_service.get_rule_value('min_phrase_ok_rate', default=0.75)
        min_attempts = int(await self._rules_service.get_rule_value('min_attempts_for_analysis', default=10.0))
        
        # Query phrase performance
        # This would need to be implemented in PhraseRepository
        # For now, return placeholder
        logger.info(f"Analyzing phrase performance with thresholds: success_rate={min_success_rate}, asr={min_asr_score}, phrase_ok={min_phrase_ok_rate}")
        
        return {
            "analyzed": 0,
            "disabled": 0,
            "thresholds": {
                "min_success_rate": min_success_rate,
                "min_asr_score": min_asr_score,
                "min_phrase_ok_rate": min_phrase_ok_rate,
                "min_attempts": min_attempts
            }
        }
    
    async def _check_rate_limits(self, user_id: UserId) -> None:
        """
        Check if user has exceeded rate limits.
        
        Raises:
            ValueError: If rate limit exceeded
        """
        # Get rate limits from rules
        max_active = int(await self._rules_service.get_rule_value('max_challenges_per_user', default=3.0))
        max_per_hour = int(await self._rules_service.get_rule_value('max_challenges_per_hour', default=20.0))
        
        # Check active challenges
        active_count = await self._challenge_repo.count_active_challenges(user_id)
        if active_count >= max_active:
            raise ValueError(
                f"User has too many active challenges ({active_count}). "
                f"Maximum allowed: {max_active}. Please wait for existing challenges to expire."
            )
        
        # Check recent challenges (last hour)
        recent_count = await self._challenge_repo.count_recent_challenges(user_id, since_hours=1)
        if recent_count >= max_per_hour:
            raise ValueError(
                f"Rate limit exceeded. Maximum {max_per_hour} challenges per hour. "
                f"Current count: {recent_count}. Try again later."
            )