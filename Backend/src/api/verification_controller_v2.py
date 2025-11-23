"""Voice biometric verification API endpoints with dynamic phrase support."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Optional
from uuid import UUID
import io
import soundfile as sf
import logging

from ..application.verification_service_v2 import VerificationServiceV2
from ..infrastructure.biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade
from ..application.dto.verification_dto import (
    StartVerificationResponse,
    VerifyVoiceResponse
)
from ..infrastructure.config.dependencies import (
    get_verification_service_v2,
    get_voice_biometric_engine
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


@router.post("/start", response_model=StartVerificationResponse)
async def start_verification(
    user_id: str = Form(...),
    difficulty: str = Form("medium"),
    verification_service: VerificationServiceV2 = Depends(get_verification_service_v2)
):
    """
    Start verification process and get a phrase for the user.
    
    - **user_id**: User UUID who wants to verify
    - **difficulty**: Phrase difficulty level (easy/medium/hard)
    
    Returns verification_id, user_id, and phrase to read.
    """
    try:
        user_uuid = UUID(user_id)
        
        result = await verification_service.start_verification(
            user_id=user_uuid,
            difficulty=difficulty
        )
        
        return StartVerificationResponse(
            verification_id=result["verification_id"],
            user_id=result["user_id"],
            phrase=result["phrase"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error in start_verification: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in start_verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start verification"
        )


@router.post("/verify", response_model=VerifyVoiceResponse)
async def verify_voice(
    verification_id: str = Form(...),
    phrase_id: str = Form(...),
    audio_file: UploadFile = File(...),
    verification_service: VerificationServiceV2 = Depends(get_verification_service_v2),
    voice_engine: VoiceBiometricEngineFacade = Depends(get_voice_biometric_engine)
):
    """
    Verify voice with phrase validation.
    
    - **verification_id**: The verification session ID from /start
    - **phrase_id**: The phrase ID that was read
    - **audio_file**: Audio file (WAV, MP3, FLAC, etc.)
    
    Returns verification result with scores and decision.
    """
    try:
        # Validate IDs
        verification_uuid = UUID(verification_id)
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
        anti_spoofing_score = result.get('anti_spoofing_score')
        
        # Verify voice
        verify_result = await verification_service.verify_voice(
            verification_id=verification_uuid,
            phrase_id=phrase_uuid,
            embedding=embedding,
            anti_spoofing_score=anti_spoofing_score
        )
        
        return VerifyVoiceResponse(
            verification_id=verify_result["verification_id"],
            user_id=verify_result["user_id"],
            is_verified=verify_result["is_verified"],
            confidence_score=verify_result["confidence_score"],
            similarity_score=verify_result["similarity_score"],
            anti_spoofing_score=verify_result.get("anti_spoofing_score"),
            phrase_match=verify_result["phrase_match"],
            is_live=verify_result["is_live"],
            threshold_used=verify_result["threshold_used"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error in verify_voice: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in verify_voice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify voice"
        )


@router.post("/quick-verify", response_model=VerifyVoiceResponse)
async def quick_verify(
    user_id: str = Form(...),
    audio_file: UploadFile = File(...),
    verification_service: VerificationServiceV2 = Depends(get_verification_service_v2),
    voice_engine: VoiceBiometricEngineFacade = Depends(get_voice_biometric_engine)
):
    """
    Quick verification without phrase management (for simple use cases).
    
    - **user_id**: User UUID to verify
    - **audio_file**: Audio file (WAV, MP3, FLAC, etc.)
    
    Returns verification result with scores.
    """
    try:
        user_uuid = UUID(user_id)
        
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
        anti_spoofing_score = result.get('anti_spoofing_score')
        
        # Quick verify
        verify_result = await verification_service.quick_verify(
            user_id=user_uuid,
            embedding=embedding,
            anti_spoofing_score=anti_spoofing_score
        )
        
        return VerifyVoiceResponse(
            verification_id=None,
            user_id=verify_result["user_id"],
            is_verified=verify_result["is_verified"],
            confidence_score=verify_result["confidence_score"],
            similarity_score=verify_result["similarity_score"],
            anti_spoofing_score=verify_result.get("anti_spoofing_score"),
            phrase_match=None,
            is_live=verify_result["is_live"],
            threshold_used=verify_result["threshold_used"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error in quick_verify: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in quick_verify: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to quick verify"
        )


@router.get("/history/{user_id}")
async def get_verification_history(
    user_id: str,
    limit: int = 10,
    verification_service: VerificationServiceV2 = Depends(get_verification_service_v2)
):
    """
    Get verification history for a user.
    
    - **user_id**: User UUID
    - **limit**: Maximum number of recent attempts to return (default: 10)
    
    Returns list of recent verification attempts.
    """
    try:
        user_uuid = UUID(user_id)
        result = await verification_service.get_verification_history(user_uuid, limit)
        return result
    
    except ValueError as e:
        logger.error(f"Validation error in get_verification_history: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_verification_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verification history"
        )
