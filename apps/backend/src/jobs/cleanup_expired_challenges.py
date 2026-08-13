"""Background job for cleaning up expired challenges."""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def cleanup_expired_challenges_job(challenge_repo, interval_seconds: int = 30):
    """
    Background job that periodically deletes expired challenges.

    Args:
        challenge_repo: Challenge repository instance
        interval_seconds: How often to run cleanup (default: 30 seconds)
    """
    logger.info(
        f"Starting expired challenges cleanup job (interval: {interval_seconds}s)"
    )

    while True:
        try:
            deleted = await challenge_repo.cleanup_expired_challenges(
                older_than_hours=1
            )
            if deleted > 0:
                logger.info(f"Deleted {deleted} expired challenges")
        except Exception as exc:
            logger.error(f"Error in cleanup job: {exc}", exc_info=True)

        await asyncio.sleep(interval_seconds)
