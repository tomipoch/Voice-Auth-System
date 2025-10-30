"""FastAPI controller for verification endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional
from uuid import UUID
import logging

from ..application.verification_service import VerificationService
from ..application.dto.VerificationRequestDTO import VerificationRequestDTO
from ..application.dto.VerificationResponseDTO import VerificationResponseDTO

logger = logging.getLogger(__name__)

# Constants
INTERNAL_SERVER_ERROR = "Internal server error"

verification_router = APIRouter()


# Dependency injection placeholder
async def get_verification_service() -> VerificationService:
    """Get verification service instance."""
    # This would be implemented with proper DI container
    raise NotImplementedError("Dependency injection not implemented in demo")


@verification_router.post("/verify", response_model=dict)
async def verify_voice(
    audio_file: UploadFile = File(...),
    user_id: Optional[UUID] = Form(None),
    external_user_ref: Optional[str] = Form(None),
    challenge_id: Optional[UUID] = Form(None),
    expected_phrase: Optional[str] = Form(None),
    client_id: Optional[UUID] = Form(None),
    include_scores: bool = Form(False),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Verify voice authentication.
    
    This is the main endpoint for voice biometric verification.
    Implements the complete flow described in the proposal.
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio_file.read()
        audio_format = audio_file.content_type.split('/')[-1]
        
        # Create request DTO
        request_dto = VerificationRequestDTO(
            audio_data=audio_data,
            audio_format=audio_format,
            user_id=user_id,
            external_user_ref=external_user_ref,
            challenge_id=challenge_id,
            expected_phrase=expected_phrase,
            client_id=client_id,
            context={
                "user_agent": None,  # Would get from request headers
                "ip_address": None,  # Would get from request
                "timestamp": None    # Would be added by middleware
            }
        )
        
        # Validate request
        validation_errors = request_dto.validate()
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail={"errors": validation_errors}
            )
        
        # Perform verification
        response = await verification_service.verify_voice(
            request_dto, 
            include_scores_in_response=include_scores
        )
        
        # Convert to dict for JSON response
        return {
            "success": response.success,
            "request_id": str(response.request_id),
            "reason": response.reason.value,
            "total_latency_ms": response.total_latency_ms,
            "processed_at": response.processed_at.isoformat(),
            "scores": {
                "similarity": response.scores.similarity,
                "spoof_probability": response.scores.spoof_probability,
                "phrase_match": response.scores.phrase_match,
                "phrase_ok": response.scores.phrase_ok,
                "inference_latency_ms": response.scores.inference_latency_ms
            } if response.scores and include_scores else None,
            "policy_used": response.policy_used,
            "metadata": response.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice verification: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@verification_router.post("/verify-simple")
async def verify_voice_simple(
    audio_file: UploadFile = File(...),
    user_id: UUID = Form(...),
    expected_phrase: str = Form(...),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Simplified verification endpoint for basic use cases.
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio_file.read()
        audio_format = audio_file.content_type.split('/')[-1]
        
        # Create simplified request
        request_dto = VerificationRequestDTO(
            audio_data=audio_data,
            audio_format=audio_format,
            user_id=user_id,
            expected_phrase=expected_phrase
        )
        
        # Perform verification
        response = await verification_service.verify_voice(request_dto)
        
        # Return simplified response
        return {
            "authenticated": response.success,
            "confidence": response.scores.similarity if response.scores else 0.0,
            "reason": response.reason.value,
            "request_id": str(response.request_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple verification: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@verification_router.get("/attempt/{attempt_id}")
async def get_verification_attempt(
    attempt_id: UUID,
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get details of a previous verification attempt.
    """
    try:
        # In a real implementation, this would query the auth attempt repository
        return {
            "success": True,
            "attempt_id": str(attempt_id),
            "message": "Attempt lookup not implemented in demo"
        }
        
    except Exception as e:
        logger.error(f"Error getting verification attempt: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@verification_router.get("/user/{user_id}/history")
async def get_user_verification_history(
    user_id: UUID,
    limit: int = 10,
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get verification history for a user.
    """
    try:
        # In a real implementation, this would query the repository
        return {
            "success": True,
            "user_id": str(user_id),
            "history": [],
            "message": "History lookup not implemented in demo"
        }
        
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)