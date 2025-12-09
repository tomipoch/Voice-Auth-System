"""Background job for cleaning up expired challenges."""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def cleanup_expired_challenges_job(challenge_repo, interval_seconds: int = 30):
    """
    Background job that periodically cleans up expired challenges.
    
    Args:
        challenge_repo: Challenge repository instance
        interval_seconds: How often to run cleanup (default: 30 seconds)
    """
    logger.info(f"Starting expired challenges cleanup job (interval: {interval_seconds}s)")
    
    while True:
        try:
            # Update expired challenges to 'expired' status
            result = await challenge_repo.mark_expired_challenges()
            
            if result > 0:
                logger.info(f"Marked {result} challenges as expired")
            
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}", exc_info=True)
        
        # Wait for next interval
        await asyncio.sleep(interval_seconds)
