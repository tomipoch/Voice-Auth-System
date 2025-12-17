"""
Evaluation Controller

API endpoints for managing evaluation sessions.
Allows starting/stopping evaluation sessions for manual frontend testing.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

from evaluation.evaluation_logger import evaluation_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class StartSessionRequest(BaseModel):
    """Request model for starting an evaluation session."""
    session_name: str


class StartSessionResponse(BaseModel):
    """Response model for starting an evaluation session."""
    session_id: str
    message: str


class SessionSummaryResponse(BaseModel):
    """Response model for session summary."""
    session_id: str
    stats: Dict


@router.post("/start-session", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_evaluation_session(request: StartSessionRequest):
    """
    Start a new evaluation session.
    
    All subsequent enrollment and verification operations will be logged
    until the session is stopped.
    """
    try:
        session_id = evaluation_logger.start_session(request.session_name)
        
        logger.info(f"Started evaluation session: {session_id}")
        
        return StartSessionResponse(
            session_id=session_id,
            message=f"Evaluation session started. All operations will be logged."
        )
    except Exception as e:
        logger.error(f"Failed to start evaluation session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start evaluation session: {str(e)}"
        )


@router.post("/stop-session")
async def stop_evaluation_session(session_id: Optional[str] = None):
    """
    Stop an evaluation session.
    
    If no session_id provided, stops the current active session.
    """
    try:
        stopped_id = evaluation_logger.stop_session(session_id)
        
        if stopped_id:
            logger.info(f"Stopped evaluation session: {stopped_id}")
            return {"message": f"Evaluation session {stopped_id} stopped", "session_id": stopped_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found"
            )
    except Exception as e:
        logger.error(f"Failed to stop evaluation session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop evaluation session: {str(e)}"
        )


@router.get("/export-session/{session_id}")
async def export_evaluation_session(session_id: str):
    """
    Export evaluation session data to JSON file.
    
    Returns the file path where data was saved.
    """
    try:
        filepath = evaluation_logger.export_session(session_id)
        
        if filepath:
            return {
                "message": "Session exported successfully",
                "session_id": session_id,
                "filepath": str(filepath)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
    except Exception as e:
        logger.error(f"Failed to export session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export session: {str(e)}"
        )


@router.get("/sessions", response_model=List[str])
async def list_evaluation_sessions():
    """List all active evaluation sessions."""
    try:
        sessions = evaluation_logger.list_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/session-summary/{session_id}", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: str):
    """Get summary statistics for a session."""
    try:
        summary = evaluation_logger.get_session_summary(session_id)
        
        if summary:
            return SessionSummaryResponse(session_id=session_id, stats=summary)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
    except Exception as e:
        logger.error(f"Failed to get session summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session summary: {str(e)}"
        )


@router.get("/status")
async def get_evaluation_status():
    """Get current evaluation system status."""
    try:
        return {
            "enabled": evaluation_logger.enabled,
            "current_session": evaluation_logger.current_session_id,
            "active_sessions": len(evaluation_logger.active_sessions)
        }
    except Exception as e:
        logger.error(f"Failed to get evaluation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evaluation status: {str(e)}"
        )
