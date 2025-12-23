"""DTOs for enrollment module."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class StartEnrollmentRequest(BaseModel):
    """Request to start enrollment process."""
    user_id: Optional[UUID] = None
    external_ref: Optional[str] = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class StartEnrollmentResponse(BaseModel):
    """Response after starting enrollment."""
    success: bool
    user_id: str
    enrollment_id: str
    challenges: List[dict]  # Changed from phrases to match frontend
    required_samples: int
    message: str
    voiceprint_exists: bool = False  # Indicates if user already has a voiceprint


class AddEnrollmentSampleRequest(BaseModel):
    """Request to add enrollment sample."""
    user_id: UUID
    enrollment_id: UUID
    phrase_id: UUID
    # audio_file se maneja como UploadFile en el controller


class AddEnrollmentSampleResponse(BaseModel):
    """Response after adding sample."""
    success: bool
    sample_id: str
    samples_completed: int
    samples_required: int
    is_complete: bool
    next_phrase: Optional[dict] = None
    quality_score: Optional[float] = None
    message: str


class CompleteEnrollmentRequest(BaseModel):
    """Request to complete enrollment."""
    user_id: UUID
    enrollment_id: UUID


class CompleteEnrollmentResponse(BaseModel):
    """Response after completing enrollment."""
    success: bool
    user_id: str
    voiceprint_id: str
    enrollment_quality: float
    samples_used: int
    message: str


class EnrollmentStatusResponse(BaseModel):
    """Response with enrollment status."""
    user_id: str
    enrollment_id: Optional[str]
    is_enrolled: bool
    samples_count: int
    required_samples: int
    phrases_used: List[dict]
    created_at: Optional[str]
