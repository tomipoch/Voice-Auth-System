"""Custom exception handlers for the FastAPI application."""

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any other unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
