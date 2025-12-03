"""DTOs for verification module."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class StartVerificationRequest(BaseModel):
    """Request to start verification process."""
    user_id: UUID
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class StartVerificationResponse(BaseModel):
    """Response after starting verification."""
    success: bool
    verification_id: str
    user_id: str  # Changed from UUID to str to match controller
    phrase: dict
    message: str


class VerifyVoiceRequest(BaseModel):
    """Request to verify voice."""
    user_id: UUID
    verification_id: UUID
    phrase_id: UUID
    # audio_file se maneja como UploadFile en el controller


class VerifyVoiceResponse(BaseModel):
    """Response after voice verification."""
    verification_id: Optional[str]
    user_id: str
    is_verified: bool
    confidence_score: float
    similarity_score: float
    anti_spoofing_score: Optional[float]
    phrase_match: Optional[bool]
    is_live: bool
    threshold_used: float


# Multi-phrase verification DTOs
class StartMultiPhraseVerificationResponse(BaseModel):
    """Response after starting multi-phrase verification."""
    verification_id: str
    user_id: str
    phrases: list[dict]  # [{"id": "...", "text": "...", "difficulty": "..."}]
    total_phrases: int


class VerifyPhraseResponse(BaseModel):
    """Response after verifying a single phrase in multi-phrase verification."""
    phrase_number: int
    individual_score: float
    is_complete: bool
    
    # Only present if is_complete=False
    phrases_remaining: Optional[int] = None
    
    # Only present if is_complete=True
    average_score: Optional[float] = None
    is_verified: Optional[bool] = None
    threshold_used: Optional[float] = None
    all_results: Optional[list[dict]] = None
    
    # In case of spoof detection
    rejected: Optional[bool] = None
    reason: Optional[str] = None

