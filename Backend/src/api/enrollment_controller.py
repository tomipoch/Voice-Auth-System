"""FastAPI controller for enrollment endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from uuid import UUID
import logging

from ..application.enrollment_service import EnrollmentService
from ..infrastructure.biometrics.VoiceBiometricEngineFacade import VoiceBiometricEngineFacade

logger = logging.getLogger(__name__)

# Constants
INTERNAL_SERVER_ERROR = "Internal server error"

enrollment_router = APIRouter()


# Dependency injection placeholders
# In production, these would be properly injected
async def get_enrollment_service() -> EnrollmentService:
    """Get enrollment service instance."""
    # This would be implemented with proper DI container
    raise NotImplementedError("Dependency injection not implemented in demo")


async def get_biometric_engine() -> VoiceBiometricEngineFacade:
    """Get biometric engine instance."""
    # This would be implemented with proper DI container
    raise NotImplementedError("Dependency injection not implemented in demo")


@enrollment_router.post("/start")
async def start_enrollment(
    external_ref: Optional[str] = Form(None),
    user_id: Optional[UUID] = Form(None),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Start enrollment process for a user.
    
    Either external_ref or user_id should be provided.
    """
    try:
        user_id = await enrollment_service.start_enrollment(
            user_id=user_id,
            external_ref=external_ref
        )
        
        return {
            "success": True,
            "user_id": str(user_id),
            "message": "Enrollment started successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting enrollment: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@enrollment_router.post("/add-sample")
async def add_enrollment_sample(
    user_id: UUID = Form(...),
    audio_file: UploadFile = File(...),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
    biometric_engine: VoiceBiometricEngineFacade = Depends(get_biometric_engine)
):
    """
    Add an enrollment voice sample for a user.
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio_file.read()
        audio_format = audio_file.content_type.split('/')[-1]
        
        # Validate audio quality
        quality_info = biometric_engine.validate_audio_quality(audio_data, audio_format)
        if not quality_info.get("is_valid", False):
            raise HTTPException(
                status_code=400, 
                detail=f"Audio quality insufficient: {quality_info.get('reason', 'Unknown')}"
            )
        
        # Extract embedding
        embedding = biometric_engine.extract_embedding_only(audio_data, audio_format)
        
        # Add sample
        sample_id = await enrollment_service.add_enrollment_sample(
            user_id=user_id,
            embedding=embedding,
            snr_db=quality_info.get("snr_db"),
            duration_sec=quality_info.get("duration_sec")
        )
        
        return {
            "success": True,
            "sample_id": str(sample_id),
            "quality_info": quality_info,
            "message": "Enrollment sample added successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding enrollment sample: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@enrollment_router.post("/complete")
async def complete_enrollment(
    user_id: UUID = Form(...),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Complete enrollment process by creating final voiceprint.
    """
    try:
        voiceprint = await enrollment_service.complete_enrollment(user_id)
        
        return {
            "success": True,
            "voiceprint_id": str(voiceprint.id),
            "created_at": voiceprint.created_at.isoformat(),
            "message": "Enrollment completed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing enrollment: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@enrollment_router.get("/status/{user_id}")
async def get_enrollment_status(
    user_id: UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Get enrollment status for a user.
    """
    try:
        status = await enrollment_service.get_enrollment_status(user_id)
        
        return {
            "success": True,
            "user_id": str(user_id),
            "enrollment_status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting enrollment status: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@enrollment_router.delete("/{user_id}")
async def delete_enrollment(
    user_id: UUID,
    enrollment_service: EnrollmentService = Depends(get_enrollment_service)
):
    """
    Delete user enrollment (GDPR compliance).
    """
    try:
        # In a real implementation, this would:
        # 1. Delete voiceprint
        # 2. Delete enrollment samples
        # 3. Mark user as deleted
        # 4. Log the deletion for audit
        
        return {
            "success": True,
            "user_id": str(user_id),
            "message": "Enrollment deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting enrollment: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)