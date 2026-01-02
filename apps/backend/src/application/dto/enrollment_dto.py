"""DTOs for enrollment module with OpenAPI documentation."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class StartEnrollmentRequest(BaseModel):
    """Request to start voice enrollment session."""
    user_id: Optional[UUID] = Field(None, description="Existing user UUID (optional)")
    external_ref: Optional[str] = Field(None, description="External reference ID")
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$", description="Phrase difficulty")


class StartEnrollmentResponse(BaseModel):
    """Response after starting enrollment session."""
    success: bool = Field(..., description="Whether session started successfully")
    user_id: str = Field(..., description="User ID for this enrollment")
    enrollment_id: str = Field(..., description="Unique enrollment session ID")
    challenges: List[dict] = Field(..., description="List of phrases to read")
    required_samples: int = Field(..., description="Total samples needed (usually 3)")
    message: str = Field(..., description="Human-readable status message")
    voiceprint_exists: bool = Field(False, description="Whether user already has a voiceprint")


class AddEnrollmentSampleRequest(BaseModel):
    """Request to add a voice sample to enrollment."""
    user_id: UUID = Field(..., description="User UUID")
    enrollment_id: UUID = Field(..., description="Session ID from /start")
    phrase_id: UUID = Field(..., description="ID of the phrase that was read")


class AddEnrollmentSampleResponse(BaseModel):
    """Response after adding a voice sample."""
    success: bool = Field(..., description="Whether sample was added successfully")
    sample_id: str = Field(..., description="Unique ID for this sample")
    samples_completed: int = Field(..., description="Number of samples collected so far")
    samples_required: int = Field(..., description="Total samples needed")
    is_complete: bool = Field(..., description="Whether enrollment can be completed")
    next_phrase: Optional[dict] = Field(None, description="Next phrase to read (if not complete)")
    quality_score: Optional[float] = Field(None, description="Audio quality score (0-1)")
    message: str = Field(..., description="Status message")


class CompleteEnrollmentRequest(BaseModel):
    """Request to finalize enrollment and create voiceprint."""
    user_id: UUID = Field(..., description="User UUID")
    enrollment_id: UUID = Field(..., description="Enrollment session ID")


class CompleteEnrollmentResponse(BaseModel):
    """Response after completing enrollment."""
    success: bool = Field(..., description="Whether voiceprint was created")
    user_id: str = Field(..., description="User ID")
    voiceprint_id: str = Field(..., description="Unique ID of created voiceprint")
    enrollment_quality: float = Field(..., description="Overall enrollment quality (0-1)", ge=0, le=1)
    samples_used: int = Field(..., description="Number of samples used")
    message: str = Field(..., description="Status message")


class EnrollmentStatusResponse(BaseModel):
    """Response with user's enrollment status."""
    user_id: str = Field(..., description="User ID")
    enrollment_id: Optional[str] = Field(None, description="Active enrollment session ID (if any)")
    is_enrolled: bool = Field(..., description="Whether user has a voiceprint")
    samples_count: int = Field(..., description="Samples collected in current session")
    required_samples: int = Field(..., description="Samples required for enrollment")
    phrases_used: List[dict] = Field(..., description="Phrases that have been read")
    created_at: Optional[str] = Field(None, description="Voiceprint creation timestamp (if enrolled)")
