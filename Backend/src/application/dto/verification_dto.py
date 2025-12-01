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
