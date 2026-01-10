"""
Dataset Recording API Controller

Endpoints para controlar la grabación de audios para dataset.
Incluye persistencia en base de datos para sobrevivir reinicios del servidor.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import json

from evaluation.dataset_recorder import dataset_recorder
from ..infrastructure.config.dependencies import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dataset-recording", tags=["dataset"])


class StartRecordingRequest(BaseModel):
    """Request model for starting dataset recording."""
    session_name: str


class RecordingStatusResponse(BaseModel):
    """Response model for recording status."""
    enabled: bool
    session_id: Optional[str] = None
    session_dir: Optional[str] = None
    total_users: int = 0
    total_enrollment_audios: int = 0
    total_verification_audios: int = 0
    users: dict = {}


@router.post("/start")
async def start_dataset_recording(
    request: StartRecordingRequest,
    pool = Depends(get_db_pool)
):
    """
    Inicia grabación de audios para dataset.
    
    Mientras está activo, todos los audios de enrollment y verification
    se guardan automáticamente en evaluation/dataset/recordings/<session_name>/
    El estado persiste en la base de datos.
    """
    try:
        if dataset_recorder.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset recording is already active"
            )
        
        session_id = dataset_recorder.start_recording(request.session_name)
        
        # Persist state to database
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES ('dataset_recording', $1::jsonb, NOW())
                    ON CONFLICT (key) DO UPDATE 
                    SET value = $1::jsonb, updated_at = NOW()
                """, json.dumps({"enabled": True, "session_id": session_id}))
        except Exception as db_error:
            logger.warning(f"Could not persist dataset state to DB: {db_error}")
        
        logger.info(f"Started dataset recording: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "session_dir": str(dataset_recorder.session_dir),
            "message": f"Dataset recording started. Audios will be saved to: {dataset_recorder.session_dir}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start dataset recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start dataset recording: {str(e)}"
        )


@router.post("/stop")
async def stop_dataset_recording(
    pool = Depends(get_db_pool)
):
    """
    Detiene grabación de audios para dataset.
    """
    try:
        if not dataset_recorder.enabled:
            return {
                "success": False,
                "message": "No active recording session"
            }
        
        stopped_dir = dataset_recorder.stop_recording()
        
        # Update state in database
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES ('dataset_recording', '{"enabled": false}'::jsonb, NOW())
                    ON CONFLICT (key) DO UPDATE 
                    SET value = '{"enabled": false}'::jsonb, updated_at = NOW()
                """)
        except Exception as db_error:
            logger.warning(f"Could not persist dataset state to DB: {db_error}")
        
        logger.info(f"Stopped dataset recording: {stopped_dir}")
        return {
            "success": True,
            "message": f"Dataset recording stopped",
            "session_dir": str(stopped_dir) if stopped_dir else None
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
            total_verification_audios=summary.get("total_verification_audios", 0),
            users=summary.get("users", {})
        )
    except Exception as e:
        logger.error(f"Failed to get recording status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recording status: {str(e)}"
        )


async def restore_dataset_state(pool):
    """
    Restore dataset recording state from database on startup.
    Called during application lifespan startup.
    """
    try:
        async with pool.acquire() as conn:
            # First ensure table exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_by VARCHAR(255)
                )
            """)
            
            row = await conn.fetchrow("""
                SELECT value FROM system_settings WHERE key = 'dataset_recording'
            """)
            
            if row and row['value']:
                state = row['value'] if isinstance(row['value'], dict) else json.loads(row['value'])
                if state.get('enabled'):
                    session_id = state.get('session_id', 'restored_session')
                    # Extract session name from session_id (format: name_timestamp)
                    session_name = session_id.rsplit('_', 2)[0] if '_' in session_id else session_id
                    dataset_recorder.start_recording(session_name + "_restored")
                    logger.info(f"Restored dataset recording state from DB")
                    
    except Exception as e:
        logger.warning(f"Could not restore dataset recording state: {e}")
