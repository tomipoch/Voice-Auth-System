"""Data Transfer Objects for verification requests and responses."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class VerificationRequestDTO:
    """Request DTO for voice verification."""
    
    # Audio data
    audio_data: bytes
    audio_format: str  # "wav", "mp3", etc.
    
    # User identification
    user_id: Optional[UUID] = None
    external_user_ref: Optional[str] = None
    
    # Challenge verification
    challenge_id: Optional[UUID] = None
    expected_phrase: Optional[str] = None
    
    # Client context
    client_id: Optional[UUID] = None
    
    # Additional context for risk assessment
    context: Optional[Dict[str, Any]] = None
    
    def validate(self) -> list[str]:
        """Validate the request and return list of errors."""
        errors = []
        
        if not self.audio_data:
            errors.append("Audio data is required")
        
        if not self.audio_format:
            errors.append("Audio format is required")
        
        if not self.user_id and not self.external_user_ref:
            errors.append("Either user_id or external_user_ref is required")
        
        if not self.challenge_id and not self.expected_phrase:
            errors.append("Either challenge_id or expected_phrase is required")
        
        return errors