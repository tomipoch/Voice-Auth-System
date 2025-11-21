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
    success: bool
    verification_id: str
    is_verified: bool
    confidence_score: float
    similarity_score: Optional[float]
    anti_spoofing_score: Optional[float]
    phrase_match: Optional[bool]
    decision: str
    message: str
    metadata: Optional[dict] = None
