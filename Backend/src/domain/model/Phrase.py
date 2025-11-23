"""Phrase domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Phrase:
    """Represents a phrase that can be used for enrollment or verification."""
    
    id: UUID
    text: str
    source: Optional[str]
    word_count: int
    char_count: int
    language: str
    difficulty: str  # 'easy', 'medium', 'hard'
    is_active: bool
    created_at: datetime
    
    def __post_init__(self):
        """Validate phrase data after initialization."""
        if not self.text or len(self.text.strip()) == 0:
            raise ValueError("Phrase text cannot be empty")
        
        if self.word_count < 1:
            raise ValueError("Word count must be at least 1")
        
        if self.char_count < 20 or self.char_count > 500:
            raise ValueError("Character count must be between 20 and 500")
        
        if self.difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")
    
    def is_available(self) -> bool:
        """Check if the phrase is available for use."""
        return self.is_active
    
    def get_display_text(self) -> str:
        """Get the phrase text for display purposes."""
        return self.text.strip()


@dataclass
class PhraseUsage:
    """Represents a usage record of a phrase by a user."""
    
    id: UUID
    phrase_id: UUID
    user_id: UUID
    used_for: str  # 'enrollment' or 'verification'
    used_at: datetime
    
    def __post_init__(self):
        """Validate usage data after initialization."""
        if self.used_for not in ['enrollment', 'verification']:
            raise ValueError("used_for must be 'enrollment' or 'verification'")
