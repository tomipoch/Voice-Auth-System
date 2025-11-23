"""FastAPI controller for phrase endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from uuid import UUID
import logging

from ..application.phrase_service import PhraseService
from ..application.dto.phrase_dto import PhraseDTO, PhraseStatsDTO
from ..infrastructure.config.dependencies import get_phrase_service as get_phrase_service_dep

logger = logging.getLogger(__name__)

# Constants
INTERNAL_SERVER_ERROR = "Internal server error"
PHRASE_NOT_FOUND = "Phrase not found"
INVALID_PHRASE_ID = "Invalid phrase ID format"

phrase_router = APIRouter()


# Dependency injection
async def get_phrase_service() -> PhraseService:
    """Get phrase service instance."""
    return await get_phrase_service_dep()


@phrase_router.get("/random", response_model=List[PhraseDTO])
async def get_random_phrases(
    count: int = Query(default=1, ge=1, le=10),
    user_id: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None, regex="^(easy|medium|hard)$"),
    language: str = Query(default='es'),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Get random phrases for enrollment or verification.
    
    - **count**: Number of phrases to return (1-10)
    - **user_id**: User ID to exclude recently used phrases (optional)
    - **difficulty**: Filter by difficulty: easy, medium, hard (optional)
    - **language**: Language code (default: es)
    """
    try:
        user_uuid = UUID(user_id) if user_id else None
        
        phrases = await phrase_service.get_random_phrases(
            user_id=user_uuid,
            count=count,
            difficulty=difficulty,
            language=language
        )
        
        if not phrases:
            raise HTTPException(
                status_code=404, 
                detail="No phrases available with the specified criteria"
            )
        
        return phrases
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random phrases: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.get("/stats", response_model=PhraseStatsDTO)
async def get_phrase_stats(
    language: str = Query(default='es'),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Get statistics about available phrases.
    
    - **language**: Language code (default: es)
    """
    try:
        stats = await phrase_service.get_phrase_stats(language=language)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting phrase stats: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.get("/list", response_model=List[PhraseDTO])
async def list_phrases(
    difficulty: Optional[str] = Query(default=None, regex="^(easy|medium|hard)$"),
    language: str = Query(default='es'),
    limit: Optional[int] = Query(default=100, ge=1, le=1000),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    List all active phrases with optional filters.
    
    - **difficulty**: Filter by difficulty: easy, medium, hard (optional)
    - **language**: Language code (default: es)
    - **limit**: Maximum number of phrases to return (1-1000)
    """
    try:
        phrases = await phrase_service.list_active_phrases(
            difficulty=difficulty,
            language=language,
            limit=limit
        )
        
        return phrases
        
    except Exception as e:
        logger.error(f"Error listing phrases: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.get("/{phrase_id}", response_model=PhraseDTO)
async def get_phrase(
    phrase_id: str,
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Get a specific phrase by ID.
    
    - **phrase_id**: UUID of the phrase
    """
    try:
        phrase_uuid = UUID(phrase_id)
        phrase = await phrase_service.get_phrase_by_id(phrase_uuid)
        
        if not phrase:
            raise HTTPException(status_code=404, detail=PHRASE_NOT_FOUND)
        
        return phrase
        
    except ValueError:
        raise HTTPException(status_code=400, detail=INVALID_PHRASE_ID)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting phrase: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.post("/{phrase_id}/record-usage")
async def record_phrase_usage(
    phrase_id: str,
    user_id: str = Query(...),
    used_for: str = Query(..., regex="^(enrollment|verification)$"),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Record that a user used a phrase.
    
    - **phrase_id**: UUID of the phrase used
    - **user_id**: UUID of the user
    - **used_for**: Purpose of usage (enrollment or verification)
    """
    try:
        phrase_uuid = UUID(phrase_id)
        user_uuid = UUID(user_id)
        
        await phrase_service.record_phrase_usage(
            phrase_id=phrase_uuid,
            user_id=user_uuid,
            used_for=used_for
        )
        
        return {
            "success": True,
            "message": "Phrase usage recorded successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error recording phrase usage: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.patch("/{phrase_id}/status")
async def update_phrase_status(
    phrase_id: str,
    is_active: bool = Query(...),
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Enable or disable a phrase (Admin only).
    
    - **phrase_id**: UUID of the phrase
    - **is_active**: New active status
    """
    try:
        phrase_uuid = UUID(phrase_id)
        
        success = await phrase_service.update_phrase_status(
            phrase_id=phrase_uuid,
            is_active=is_active
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=PHRASE_NOT_FOUND)
        
        return {
            "success": True,
            "message": f"Phrase {'activated' if is_active else 'deactivated'} successfully"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=INVALID_PHRASE_ID)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating phrase status: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@phrase_router.delete("/{phrase_id}")
async def delete_phrase(
    phrase_id: str,
    phrase_service: PhraseService = Depends(get_phrase_service)
):
    """
    Delete a phrase (Admin only).
    
    - **phrase_id**: UUID of the phrase to delete
    """
    try:
        phrase_uuid = UUID(phrase_id)
        
        success = await phrase_service.delete_phrase(phrase_uuid)
        
        if not success:
            raise HTTPException(status_code=404, detail=PHRASE_NOT_FOUND)
        
        return {
            "success": True,
            "message": "Phrase deleted successfully"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=INVALID_PHRASE_ID)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting phrase: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)
