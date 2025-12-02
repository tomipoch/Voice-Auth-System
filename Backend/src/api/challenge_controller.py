"""FastAPI controller for challenge endpoints."""

from fastapi import APIRouter, HTTPException, Form, Depends
from typing import Optional
from uuid import UUID
import logging

from ..application.challenge_service import ChallengeService

logger = logging.getLogger(__name__)

# Constants
INTERNAL_SERVER_ERROR = "Internal server error"

challenge_router = APIRouter()


# Dependency injection
from ..infrastructure.config.dependencies import get_challenge_service


@challenge_router.post("/create")
async def create_challenge(
    user_id: UUID = Form(...),
    difficulty: Optional[str] = Form(None),
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Create a new voice challenge for a user.
    
    - **user_id**: User UUID
    - **difficulty**: Optional difficulty level (easy/medium/hard)
    """
    try:
        challenge = await challenge_service.create_challenge(
            user_id=user_id,
            difficulty=difficulty
        )
        
        return {
            "success": True,
            "challenge": challenge,
            "message": "Challenge created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating challenge: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.post("/create-batch")
async def create_challenge_batch(
    user_id: UUID = Form(...),
    count: int = Form(3),
    difficulty: Optional[str] = Form(None),
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Create multiple challenges at once (optimized).
    
    - **user_id**: User UUID
    - **count**: Number of challenges to create (default: 3)
    - **difficulty**: Optional difficulty level (easy/medium/hard)
    """
    try:
        challenges = await challenge_service.create_challenge_batch(
            user_id=user_id,
            count=count,
            difficulty=difficulty
        )
        
        return {
            "success": True,
            "challenges": challenges,
            "count": len(challenges),
            "message": f"Created {len(challenges)} challenges successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating challenge batch: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.get("/{challenge_id}")
async def get_challenge(
    challenge_id: UUID,
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Get challenge details by ID.
    """
    try:
        challenge = await challenge_service.get_challenge(challenge_id)
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        return {
            "success": True,
            "challenge": challenge
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting challenge: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.get("/user/{user_id}/active")
async def get_active_challenge(
    user_id: UUID,
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Get the most recent active challenge for a user.
    """
    try:
        challenge = await challenge_service.get_active_challenge(user_id)
        
        if not challenge:
            return {
                "success": True,
                "challenge": None,
                "message": "No active challenge found"
            }
        
        return {
            "success": True,
            "challenge": challenge
        }
        
    except Exception as e:
        logger.error(f"Error getting active challenge: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.post("/validate")
async def validate_challenge(
    challenge_id: UUID = Form(...),
    user_id: UUID = Form(...),
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Validate a challenge (strict validation).
    
    - **challenge_id**: Challenge UUID
    - **user_id**: User UUID
    """
    try:
        is_valid, reason = await challenge_service.validate_challenge_strict(
            challenge_id=challenge_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "is_valid": is_valid,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Error validating challenge: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.post("/cleanup")
async def cleanup_expired_challenges(
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Clean up expired challenges (admin endpoint).
    """
    try:
        deleted_count = await challenge_service.cleanup_expired_challenges()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} expired challenges"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up challenges: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)


@challenge_router.post("/generate-test-phrase")
async def generate_test_phrase(
    phrase_type: str = Form("mixed"),  # "words", "numbers", "mixed"
    challenge_service: ChallengeService = Depends(get_challenge_service)
):
    """
    Generate a test phrase (for testing/demo purposes).
    """
    try:
        phrase = challenge_service.generate_test_phrase(phrase_type)
        
        return {
            "success": True,
            "phrase": phrase,
            "phrase_type": phrase_type
        }
        
    except Exception as e:
        logger.error(f"Error generating test phrase: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)