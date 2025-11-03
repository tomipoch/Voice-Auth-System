"""Challenge service for generating and validating dynamic phrases."""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from ..domain.repositories.ChallengeRepositoryPort import ChallengeRepositoryPort
from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..shared.types.common_types import UserId, ChallengeId, AuditAction
from ..shared.constants.biometric_constants import (
    CHALLENGE_EXPIRY_MINUTES, 
    MIN_PHRASE_LENGTH, 
    MAX_PHRASE_LENGTH
)


class ChallengeService:
    """Service for generating and managing dynamic voice challenges."""
    
    # Common words for phrase generation
    COMMON_WORDS = [
        "apple", "bridge", "camera", "doctor", "elephant", "flower", "guitar", "hammer",
        "island", "jacket", "kitchen", "laptop", "mountain", "notebook", "orange", "pencil",
        "queen", "rainbow", "sunset", "teacher", "umbrella", "violet", "window", "yellow",
        "zebra", "author", "basket", "candle", "desert", "engine", "forest", "garden",
        "harbor", "igloo", "jungle", "ladder", "market", "ocean", "planet", "rabbit",
        "silver", "turtle", "vessel", "wizard", "crystal", "dolphin", "eagle", "fabric"
    ]
    
    NUMBERS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    
    def __init__(
        self,
        challenge_repo: ChallengeRepositoryPort,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort
    ):
        self._challenge_repo = challenge_repo
        self._user_repo = user_repo
        self._audit_repo = audit_repo
    
    async def create_challenge(self, user_id: UserId) -> dict:
        """Create a new challenge for a user."""
        
        # Verify user exists
        if not await self._user_repo.user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist")
        
        # Generate challenge phrase
        phrase = self._generate_phrase()
        
        # Set expiration time
        expires_at = datetime.now() + timedelta(minutes=CHALLENGE_EXPIRY_MINUTES)
        
        # Save challenge
        challenge_id = await self._challenge_repo.create_challenge(
            user_id=user_id,
            phrase=phrase,
            expires_at=expires_at
        )
        
        # Log challenge creation
        await self._audit_repo.log_event(
            actor="system",
            action=AuditAction.CREATE_CHALLENGE,
            entity_type="challenge",
            entity_id=str(challenge_id),
            metadata={
                "user_id": str(user_id),
                "phrase_length": len(phrase),
                "expires_at": expires_at.isoformat()
            }
        )
        
        return {
            "challenge_id": challenge_id,
            "phrase": phrase,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": int((expires_at - datetime.now()).total_seconds())
        }
    
    async def get_challenge(self, challenge_id: ChallengeId) -> Optional[dict]:
        """Get challenge details by ID."""
        return await self._challenge_repo.get_challenge(challenge_id)
    
    async def get_active_challenge(self, user_id: UserId) -> Optional[dict]:
        """Get the most recent active challenge for a user."""
        return await self._challenge_repo.get_active_challenge(user_id)
    
    async def validate_challenge(
        self, 
        challenge_id: ChallengeId, 
        user_id: Optional[UserId] = None
    ) -> tuple[bool, str]:
        """
        Validate a challenge.
        
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        
        # Get challenge
        challenge = await self._challenge_repo.get_challenge(challenge_id)
        if not challenge:
            return False, "Challenge not found"
        
        # Check if challenge belongs to user (if specified)
        if user_id and challenge.get('user_id') != user_id:
            return False, "Challenge does not belong to user"
        
        # Check if already used
        if challenge.get('used_at'):
            return False, "Challenge already used"
        
        # Check if expired
        expires_at = challenge.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            return False, "Challenge expired"
        
        return True, "Valid"
    
    async def mark_challenge_used(self, challenge_id: ChallengeId) -> None:
        """Mark a challenge as used."""
        await self._challenge_repo.mark_challenge_used(challenge_id)
    
    async def cleanup_expired_challenges(self) -> int:
        """Clean up expired challenges."""
        deleted_count = await self._challenge_repo.cleanup_expired_challenges()
        
        if deleted_count > 0:
            await self._audit_repo.log_event(
                actor="system",
                action=AuditAction.DELETE_USER,  # Using existing enum
                entity_type="challenge_cleanup",
                entity_id="batch",
                metadata={"deleted_count": deleted_count}
            )
        
        return deleted_count
    
    def _generate_phrase(self) -> str:
        """Generate a random phrase for voice challenge."""
        
        # Choose phrase type randomly
        phrase_type = random.choice(["word_sequence", "number_sequence", "mixed"])
        
        if phrase_type == "number_sequence":
            return self._generate_number_phrase()
        elif phrase_type == "word_sequence":
            return self._generate_word_phrase()
        else:
            return self._generate_mixed_phrase()
    
    def _generate_word_phrase(self) -> str:
        """Generate a phrase with random words."""
        num_words = random.randint(3, 6)
        words = random.sample(self.COMMON_WORDS, num_words)
        phrase = " ".join(words)
        
        # Ensure phrase is within length limits
        while len(phrase) < MIN_PHRASE_LENGTH:
            words.append(random.choice(self.COMMON_WORDS))
            phrase = " ".join(words)
        
        if len(phrase) > MAX_PHRASE_LENGTH:
            # Truncate to fit
            phrase = phrase[:MAX_PHRASE_LENGTH].rsplit(' ', 1)[0]
        
        return phrase.title()
    
    def _generate_number_phrase(self) -> str:
        """Generate a phrase with random numbers."""
        num_count = random.randint(4, 8)
        numbers = [random.choice(self.NUMBERS) for _ in range(num_count)]
        return " ".join(numbers).title()
    
    def _generate_mixed_phrase(self) -> str:
        """Generate a mixed phrase with words and numbers."""
        components = []
        
        # Add 2-3 words
        word_count = random.randint(2, 3)
        components.extend(random.sample(self.COMMON_WORDS, word_count))
        
        # Add 2-3 numbers
        number_count = random.randint(2, 3)
        components.extend([random.choice(self.NUMBERS) for _ in range(number_count)])
        
        # Shuffle components
        random.shuffle(components)
        
        phrase = " ".join(components)
        
        # Ensure within limits
        if len(phrase) > MAX_PHRASE_LENGTH:
            phrase = phrase[:MAX_PHRASE_LENGTH].rsplit(' ', 1)[0]
        
        return phrase.title()
    
    def generate_test_phrase(self, phrase_type: str = "mixed") -> str:
        """Generate a test phrase (for testing purposes)."""
        if phrase_type == "numbers":
            return self._generate_number_phrase()
        elif phrase_type == "words":
            return self._generate_word_phrase()
        else:
            return self._generate_mixed_phrase()