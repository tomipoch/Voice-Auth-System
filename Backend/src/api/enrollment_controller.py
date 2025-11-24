"""Voice biometric enrollment API endpoints with dynamic phrase support."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Optional
from uuid import UUID
import numpy as np
import io
import soundfile as sf
import logging

from ..application.enrollment_service import EnrollmentService
from ..infrastructure.services.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade
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
router = APIRouter(prefix="/api/v1/enrollment", tags=["enrollment"])


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
    try:
        user_uuid = UUID(user_id) if user_id else None
        
        result = await enrollment_service.start_enrollment(
            user_id=user_uuid,
            external_ref=external_ref,
            difficulty=difficulty
        )
        
        return StartEnrollmentResponse(
            enrollment_id=result["enrollment_id"],
            user_id=result["user_id"],
            phrases=result["phrases"],
            required_samples=result["required_samples"]
        )
    except ValueError as e:
        logger.error(f"Validation error in start_enrollment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in start_enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start enrollment"
        )


@router.post("/add-sample", response_model=AddEnrollmentSampleResponse)
async def add_enrollment_sample(
    enrollment_id: str = Form(...),
    phrase_id: str = Form(...),
    audio_file: UploadFile = File(...),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    voice_engine: VoiceBiometricEngineFacade = Depends(get_voice_biometric_engine)
):
    """
    Add an enrollment sample with phrase validation.
    
    - **enrollment_id**: The enrollment session ID from /start
    - **phrase_id**: The phrase ID that was read
    - **audio_file**: Audio file (WAV, MP3, FLAC, etc.)
    
    Returns sample_id, progress, and next phrase if available.
    """
    try:
        # Validate IDs
        enrollment_uuid = UUID(enrollment_id)
        phrase_uuid = UUID(phrase_id)
        
        # Read audio file
        audio_bytes = await audio_file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
        
        # Process audio and extract embedding
        result = voice_engine.process_audio(
            audio_data=audio_data,
            sample_rate=sample_rate
        )
        
        if not result['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Invalid audio')
            )
        
        embedding = result['embedding']
        snr_db = result.get('snr_db')
        duration_sec = result.get('duration_sec')
        
        # Add enrollment sample
        sample_result = await enrollment_service.add_enrollment_sample(
            enrollment_id=enrollment_uuid,
            phrase_id=phrase_uuid,
            embedding=embedding,
            snr_db=snr_db,
            duration_sec=duration_sec
        )
        
        return AddEnrollmentSampleResponse(
            sample_id=sample_result["sample_id"],
            samples_completed=sample_result["samples_completed"],
            samples_required=sample_result["samples_required"],
            is_complete=sample_result["is_complete"],
            next_phrase=sample_result.get("next_phrase")
        )
    
    except ValueError as e:
        logger.error(f"Validation error in add_enrollment_sample: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in add_enrollment_sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add enrollment sample"
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
    try:
        enrollment_uuid = UUID(enrollment_id)
        
        result = await enrollment_service.complete_enrollment(
            enrollment_id=enrollment_uuid,
            speaker_model_id=speaker_model_id
        )
        
        return CompleteEnrollmentResponse(
            voiceprint_id=result["voiceprint_id"],
            user_id=result["user_id"],
            quality_score=result["quality_score"],
            samples_used=result["samples_used"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error in complete_enrollment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in complete_enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete enrollment"
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
    try:
        user_uuid = UUID(user_id)
        result = await enrollment_service.get_enrollment_status(user_uuid)
        
        return EnrollmentStatusResponse(**result)
    
    except ValueError as e:
        logger.error(f"Validation error in get_enrollment_status: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_enrollment_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enrollment status"
        )
