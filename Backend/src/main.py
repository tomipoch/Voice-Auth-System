"""Main application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.challenge_controller import challenge_router
from .api.auth_controller import auth_router
from .api.admin_controller import admin_router
from .api.phrase_controller import phrase_router

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


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
    
    # Try to initialize database connection pool (not critical at startup)
    from .infrastructure.config.dependencies import close_db_pool
    
    # In production, this would also:
    # - Load ML models into memory
    # - Initialize caches
    # - Set up monitoring
    
    yield
    
    logger.info("Shutting down Voice Biometrics API...")
    # Cleanup resources
    await close_db_pool()
    logger.info("Database connection pool closed")


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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(admin_router, prefix="/api/admin", tags=["administration"])
    app.include_router(challenge_router, prefix="/api/challenges", tags=["challenges"])
    app.include_router(phrase_router, prefix="/api/phrases", tags=["phrases"])
    
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