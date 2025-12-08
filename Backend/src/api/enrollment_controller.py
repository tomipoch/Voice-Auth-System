"""Voice biometric enrollment API endpoints with dynamic phrase support."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Optional
from uuid import UUID
import numpy as np
import io
import soundfile as sf
import logging

from ..application.enrollment_service import EnrollmentService
from ..infrastructure.biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade
from ..application.dto.enrollment_dto import (
    StartEnrollmentRequest,
    StartEnrollmentResponse,
    AddEnrollmentSampleResponse,
    CompleteEnrollmentResponse,
    EnrollmentStatusResponse
)
from ..infrastructure.config.dependencies import (
    get_enrollment_service,
    get_voice_biometric_engine
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["enrollment"])


@router.post("/start", response_model=StartEnrollmentResponse)
async def start_enrollment(
    external_ref: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    difficulty: str = Form("medium"),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Start enrollment process and get phrases for user.
    
    - **external_ref**: External reference for the user (optional)
    - **user_id**: User UUID (optional, will be created if not provided)
    - **difficulty**: Phrase difficulty level (easy/medium/hard)
    
    Returns enrollment_id, user_id, and list of phrases to read.
    """
    user_uuid = UUID(user_id) if user_id else None
    
    result = await enrollment_service.start_enrollment(
        user_id=user_uuid,
        external_ref=external_ref,
        difficulty=difficulty
    )
    
    return StartEnrollmentResponse(
        success=True,
        enrollment_id=result["enrollment_id"],
        user_id=result["user_id"],
        phrases=result["challenges"],  # Challenges contain phrase info
        required_samples=result["required_samples"],
        message="Enrollment started successfully"
    )


@router.post("/add-sample", response_model=AddEnrollmentSampleResponse)
async def add_enrollment_sample(
    enrollment_id: str = Form(...),
    challenge_id: str = Form(...),
    audio_file: UploadFile = File(...),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    voice_engine: VoiceBiometricEngineFacade = Depends(get_voice_biometric_engine)
):
    """
    Add an enrollment sample with challenge validation.
    
    - **enrollment_id**: The enrollment session ID from /start
    - **challenge_id**: The challenge ID that was read
    - **audio_file**: Audio file (WAV, MP3, FLAC, etc.)
    
    Returns sample_id, progress, and next challenge if available.
    """
    # Validate IDs
    enrollment_uuid = UUID(enrollment_id)
    challenge_uuid = UUID(challenge_id)
    
    # Read audio file
    audio_bytes = await audio_file.read()
    
    # Validate audio quality
    quality_info = voice_engine.validate_audio_quality(audio_bytes, audio_file.content_type)
    if not quality_info["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=quality_info.get('reason', 'Invalid audio')
        )
    
    # Extract embedding
    embedding = voice_engine.extract_embedding_only(audio_bytes, audio_file.content_type)
    snr_db = quality_info.get('snr_db')
    duration_sec = quality_info.get('duration_sec')
    
    # Add enrollment sample
    sample_result = await enrollment_service.add_enrollment_sample(
        enrollment_id=enrollment_uuid,
        challenge_id=challenge_uuid,
        embedding=embedding,
        snr_db=snr_db,
        duration_sec=duration_sec
    )
    
    return AddEnrollmentSampleResponse(
        success=True,
        sample_id=sample_result["sample_id"],
        samples_completed=sample_result["samples_completed"],
        samples_required=sample_result["samples_required"],
        is_complete=sample_result["is_complete"],
        next_phrase=sample_result.get("next_challenge"),  # Map to next_phrase for compatibility
        message="Sample added successfully"
    )



@router.post("/complete", response_model=CompleteEnrollmentResponse)
async def complete_enrollment(
    enrollment_id: str = Form(...),
    speaker_model_id: Optional[int] = Form(None),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Complete enrollment and create final voiceprint.
    
    - **enrollment_id**: The enrollment session ID
    - **speaker_model_id**: Optional speaker model ID for training
    
    Returns voiceprint_id and quality score.
    """
    enrollment_uuid = UUID(enrollment_id)
    
    result = await enrollment_service.complete_enrollment(
        enrollment_id=enrollment_uuid,
        speaker_model_id=speaker_model_id
    )
    
    return CompleteEnrollmentResponse(
        success=True,
        voiceprint_id=result["voiceprint_id"],
        user_id=result["user_id"],
        enrollment_quality=result["quality_score"],
        samples_used=result["samples_used"],
        message="Enrollment completed successfully"
    )


@router.get("/status/{user_id}", response_model=EnrollmentStatusResponse)
async def get_enrollment_status(
    user_id: str,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Get enrollment status for a user.
    
    - **user_id**: User UUID
    
    Returns enrollment status, samples collected, and phrases used.
    """
    user_uuid = UUID(user_id)
    result = await enrollment_service.get_enrollment_status(user_uuid)
    
    return EnrollmentStatusResponse(**result)
