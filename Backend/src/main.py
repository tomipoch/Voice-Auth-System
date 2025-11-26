"""Main application entry point."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import asyncpg

from .api.challenge_controller import challenge_router
from .api.auth_controller import auth_router
from .api.admin_controller import admin_router
from .api.phrase_controller import phrase_router
from .infrastructure.config.dependencies import close_db_pool, create_voice_biometric_engine

# Only import enrollment and verification routers if not in testing mode
if os.getenv("TESTING") != "True":
    from .api.enrollment_controller import router as enrollment_router
    from .api.verification_controller_v2 import router as verification_router_v2

# Load environment variables
# Only load from .env file if not already set in the environment (e.g., by Docker Compose)
env_path = Path(__file__).parent.parent / '.env'
if env_path.is_file():
    load_dotenv(env_path)

# Ensure essential environment variables are set, even if from .env
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"
if not os.getenv("DB_PORT"):
    os.environ["DB_PORT"] = "5432"
if not os.getenv("DB_NAME"):
    os.environ["DB_NAME"] = "voice_biometrics"
if not os.getenv("DB_USER"):
    os.environ["DB_USER"] = "voice_user"
if not os.getenv("DB_PASSWORD"):
    os.environ["DB_PASSWORD"] = "voice_password"
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "voice-biometrics-secret-key-change-in-production"
if not os.getenv("RATE_LIMIT"):
    os.environ["RATE_LIMIT"] = "100/minute"
if not os.getenv("CORS_ALLOWED_ORIGINS"):
    os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000"

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[os.getenv("RATE_LIMIT", "100/minute")])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None
_connection_error: Optional[str] = None

# Mock VoiceBiometricEngineFacade for testing
class MockVoiceBiometricEngineFacade:
    def enroll_speaker(self, audio_file: str, user_id: str) -> dict:
        return {"status": "mock_enrolled", "user_id": user_id}

    def verify_speaker(self, audio_file: str, user_id: str) -> dict:
        return {"status": "mock_verified", "user_id": user_id, "score": 0.9}

    def is_spoof(self, audio_file: str) -> dict:
        return {"status": "mock_anti_spoofing_passed", "score": 0.1}

    def transcribe_audio(self, audio_file: str) -> dict:
        return {"status": "mock_transcribed", "text": "mock transcription"}

    def get_speaker_embedding(self, audio_file: str) -> list:
        return [0.1] * 512 # Mock embedding

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Voice Biometrics API...")
    
    # Load ML models into memory
    if os.getenv("TESTING") != "True":
        app.state.biometric_engine = create_voice_biometric_engine()
    else:
        app.state.biometric_engine = MockVoiceBiometricEngineFacade() # Use mock engine for testing
    
    yield
    
    logger.info("Shutting down Voice Biometrics API...")
    # Cleanup resources
    await close_db_pool()
    logger.info("Database connection pool closed")


from .api.error_handlers import value_error_handler, generic_exception_handler

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Voice Biometrics API",
        description="Secure voice authentication and enrollment system",
        version="1.0.0",
        lifespan=lifespan, # Commented out for testing
        docs_url="/docs",
        redoc_url=None  # ReDoc deshabilitado permanentemente
    )
    
    # Add state for the limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "Voice Biometrics API",
            "version": "1.0.0",
            "status": "running",
            "documentation": "/docs",
            "health": "/health",
            "endpoints": {
                "authentication": "/api/auth",
                "enrollment": "/api/v1/enrollment",
                "verification": "/api/v1/verification",
                "phrases": "/api/phrases",
                "admin": "/api/admin",
                "challenges": "/api/challenges"
            }
        }
    
    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(admin_router, prefix="/api/admin", tags=["administration"])
    app.include_router(challenge_router, prefix="/api/challenges", tags=["challenges"])
    app.include_router(phrase_router, prefix="/api/phrases", tags=["phrases"])
    
    # Only include enrollment and verification routers if not in testing mode
    if os.getenv("TESTING") != "True":
        app.include_router(enrollment_router)
        app.include_router(verification_router_v2)
    
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