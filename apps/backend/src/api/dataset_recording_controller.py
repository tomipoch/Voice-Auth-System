"""
Dataset Recording API Controller

Endpoints para controlar la grabación de audios para dataset.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from evaluation.dataset_recorder import dataset_recorder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dataset-recording", tags=["dataset"])


class StartRecordingRequest(BaseModel):
    """Request model for starting dataset recording."""
    session_name: str


class RecordingStatusResponse(BaseModel):
    """Response model for recording status."""
    enabled: bool
    session_id: Optional[str]
    session_dir: Optional[str]
    total_users: int
    total_enrollment_audios: int
    total_verification_audios: int


@router.post("/start")
async def start_dataset_recording(request: StartRecordingRequest):
    """
    Inicia grabación de audios para dataset.
    
    Mientras está activo, todos los audios de enrollment y verification
    se guardan automáticamente en evaluation/dataset/recordings/<session_name>/
    """
    try:
        session_id = dataset_recorder.start_recording(request.session_name)
        
        logger.info(f"Started dataset recording: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "session_dir": str(dataset_recorder.session_dir),
            "message": f"Dataset recording started. Audios will be saved to: {dataset_recorder.session_dir}"
        }
    except Exception as e:
        logger.error(f"Failed to start dataset recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start dataset recording: {str(e)}"
        )


@router.post("/stop")
async def stop_dataset_recording():
    """
    Detiene grabación de audios para dataset.
    """
    try:
        stopped_dir = dataset_recorder.stop_recording()
        
        if stopped_dir:
            logger.info(f"Stopped dataset recording: {stopped_dir}")
            return {
                "success": True,
                "message": f"Dataset recording stopped",
                "session_dir": str(stopped_dir)
            }
        else:
            return {
                "success": False,
                "message": "No active recording session"
            }
    except Exception as e:
        logger.error(f"Failed to stop dataset recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop dataset recording: {str(e)}"
        )


@router.get("/status", response_model=RecordingStatusResponse)
async def get_recording_status():
    """
    Obtiene estado actual de grabación de dataset.
    """
    try:
        summary = dataset_recorder.get_session_summary()
        
        return RecordingStatusResponse(
            enabled=summary.get("enabled", False),
            session_id=summary.get("session_id"),
            session_dir=summary.get("session_dir"),
            total_users=summary.get("total_users", 0),
            total_enrollment_audios=summary.get("total_enrollment_audios", 0),
            total_verification_audios=summary.get("total_verification_audios", 0)
        )
    except Exception as e:
        logger.error(f"Failed to get recording status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recording status: {str(e)}"
        )
