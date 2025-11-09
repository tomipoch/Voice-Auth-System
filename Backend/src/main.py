"""Main application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.challenge_controller import challenge_router
from .api.auth_controller import auth_router
from .api.admin_controller import admin_router
# Middleware commented for testing - would need proper implementation
# from .api.middleware.auth_middleware import AuthMiddleware
# from .api.middleware.audit_trace_middleware import AuditTraceMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Voice Biometrics API...")
    
    # Initialize database connections, load ML models, etc.
    # In production, this would:
    # - Connect to PostgreSQL
    # - Load ML models into memory
    # - Initialize caches
    # - Set up monitoring
    
    yield
    
    logger.info("Shutting down Voice Biometrics API...")
    # Cleanup resources


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Voice Biometrics API",
        description="Secure voice authentication and enrollment system",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None  # ReDoc deshabilitado permanentemente
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware (commented for testing)
    # app.add_middleware(AuditTraceMiddleware)
    # app.add_middleware(AuthMiddleware)
    
    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(admin_router, prefix="/api/admin", tags=["administration"])
    # app.include_router(enrollment_router, prefix="/api/enrollment", tags=["enrollment"])
    app.include_router(challenge_router, prefix="/api/challenges", tags=["challenges"])
    # app.include_router(verification_router, prefix="/api/verification", tags=["verification"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "voice-biometrics-api",
            "version": "1.0.0"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )