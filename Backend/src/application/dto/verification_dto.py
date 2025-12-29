"""DTOs for verification module with OpenAPI documentation."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class StartVerificationRequest(BaseModel):
    """Request to start a voice verification session."""
    user_id: UUID = Field(..., description="UUID of the user to verify")
    difficulty: str = Field(
        default="medium", 
        pattern="^(easy|medium|hard)$",
        description="Phrase difficulty level"
    )

    model_config = {"json_schema_extra": {"examples": [{"user_id": "550e8400-e29b-41d4-a716-446655440000", "difficulty": "medium"}]}}


class StartVerificationResponse(BaseModel):
    """Response after starting verification session."""
    success: bool = Field(..., description="Whether the session started successfully")
    verification_id: str = Field(..., description="Unique session ID for this verification")
    user_id: str = Field(..., description="User ID being verified")
    phrase: dict = Field(..., description="Phrase to read (contains id, text, difficulty)")
    message: str = Field(..., description="Human-readable status message")


class VerifyVoiceRequest(BaseModel):
    """Request to verify a voice sample."""
    user_id: UUID = Field(..., description="UUID of the user")
    verification_id: UUID = Field(..., description="Session ID from /start")
    phrase_id: UUID = Field(..., description="ID of the phrase that was read")
    # audio_file is handled as UploadFile in controller


class VerifyVoiceResponse(BaseModel):
    """Response containing voice verification results."""
    verification_id: Optional[str] = Field(None, description="Verification session ID")
    user_id: str = Field(..., description="User ID that was verified")
    is_verified: bool = Field(..., description="Final verification decision")
    confidence_score: float = Field(..., description="Overall confidence (0-1)", ge=0, le=1)
    similarity_score: float = Field(..., description="Voice similarity to enrolled voiceprint (0-1)", ge=0, le=1)
    anti_spoofing_score: Optional[float] = Field(None, description="Probability of genuine speech (0-1)")
    phrase_match: Optional[bool] = Field(None, description="Whether spoken text matched expected phrase")
    is_live: bool = Field(..., description="Whether anti-spoofing passed")
    threshold_used: float = Field(..., description="Similarity threshold used for decision")


# Multi-phrase verification DTOs
class StartMultiPhraseVerificationResponse(BaseModel):
    """Response after starting multi-phrase (3 phrases) verification."""
    verification_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(..., description="User ID being verified")
    challenges: list[dict] = Field(..., description="List of 3 phrases to read")
    total_phrases: int = Field(..., description="Total phrases required (always 3)")


class VerifyPhraseResponse(BaseModel):
    """Response after verifying a single phrase in multi-phrase verification."""
    phrase_number: int = Field(..., description="Which phrase was verified (1, 2, or 3)")
    individual_score: float = Field(..., description="Similarity score for this phrase")
    is_complete: bool = Field(..., description="Whether all 3 phrases are complete")
    
    # Only present if is_complete=False
    phrases_remaining: Optional[int] = Field(None, description="Phrases left to verify")
    
    # Only present if is_complete=True
    average_score: Optional[float] = Field(None, description="Average score across all phrases")
    is_verified: Optional[bool] = Field(None, description="Final verification decision")
    threshold_used: Optional[float] = Field(None, description="Threshold used for decision")
    all_results: Optional[list[dict]] = Field(None, description="Detailed results for each phrase")
    
    # In case of spoof detection
    rejected: Optional[bool] = Field(None, description="Whether rejected due to spoofing")
    reason: Optional[str] = Field(None, description="Rejection reason if applicable")


# Error response schema for documentation
class ErrorResponse(BaseModel):
    """Standard error response format."""
    detail: str = Field(..., description="Error message describing what went wrong")
    
    model_config = {"json_schema_extra": {"examples": [{"detail": "User not found"}]}}
