"""Main application entry point."""

import logging
import os
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Suppress third-party library warnings that don't affect functionality
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="speechbrain")
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=UserWarning, module="s3prl")
warnings.filterwarnings("ignore", message=".*set_audio_backend.*")
warnings.filterwarnings("ignore", message=".*weight_norm.*")
warnings.filterwarnings("ignore", message=".*custom_fwd.*")

from .api.admin_controller import admin_router
from .api.auth_controller import auth_router
from .api.challenge_controller import challenge_router
from .api.dataset_recording_controller import router as dataset_recording_router
from .api.enrollment_controller import router as enrollment_router
from .api.evaluation_controller import router as evaluation_router
from .api.phrase_controller import router as phrase_router
from .api.verification_controller import router as verification_router
from .infrastructure.config.dependencies import (
    close_db_pool,
    get_voice_biometric_engine,
    init_biometric_engine_async,
    init_db_pool,
    is_ready,
)

# Load environment variables
# Only load from .env file if not already set in the environment (e.g., by Docker Compose)
env_path = Path(__file__).parent.parent / ".env"
if env_path.is_file():
    load_dotenv(env_path)

# Set defaults for non-sensitive configuration
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "voice_biometrics")
os.environ.setdefault("DB_USER", "voice_user")
os.environ.setdefault("RATE_LIMIT", "100/minute")
os.environ.setdefault(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
)

# Validate required secrets exist (no defaults for security)
ENV = os.getenv("ENV", "development")

if ENV == "production":
    required_secrets = ["DB_PASSWORD", "SECRET_KEY", "EMBEDDING_ENCRYPTION_KEY"]
    missing = [s for s in required_secrets if not os.getenv(s)]
    if missing:
        raise EnvironmentError(
            f"Missing required secrets for production: {', '.join(missing)}. "
            "Set these in your .env file or environment."
        )
else:
    # Development: no hardcoded secrets. Use .env.example as a template and
    # copy to .env, or set the variables in the environment.
    if not os.getenv("DB_PASSWORD"):
        logging.warning(
            "DB_PASSWORD not set. Copy apps/backend/.env.example to .env or set it "
            "in your environment. Server will fail to start until it is configured."
        )
    if not os.getenv("EMBEDDING_ENCRYPTION_KEY"):
        logging.warning(
            "EMBEDDING_ENCRYPTION_KEY not set. Generate one with: "
            'python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"'
        )

# Rate limiter
from .api.rate_limit import limiter

# Configure logging - only show essential application logs
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Suppress verbose logging from third-party libraries
logging.getLogger("speechbrain").setLevel(logging.WARNING)
logging.getLogger("s3prl").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

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
        from .shared.constants.biometric_constants import EMBEDDING_DIMENSION

        return [0.1] * EMBEDDING_DIMENSION  # Mock embedding

    def validate_audio_quality(self, audio_data: bytes, audio_format: str) -> dict:
        """Mock equivalent of SpeakerEmbeddingAdapter.validate_audio_quality."""
        return {
            "quality": "good",
            "duration": 1.0,
            "has_silence": False,
            "is_valid": True,
        }

    def extract_embedding_only(
        self, audio_data: bytes, audio_format: str = "wav"
    ) -> "list":
        """Mock equivalent of SpeakerEmbeddingAdapter.extract_embedding_only."""
        # BiometricValidator.is_valid_embedding checks the shape,
        # so the mock must hand back a numpy array rather than a
        # bare Python list. The real adapter returns a 1-D ndarray.
        import numpy as np

        from .shared.constants.biometric_constants import EMBEDDING_DIMENSION

        return np.full(EMBEDDING_DIMENSION, 0.1, dtype=np.float32)

    def extract_features(self, audio_data: bytes, audio_format: str) -> dict:
        """Mock equivalent of VoiceBiometricEngineFacade.extract_features."""
        import numpy as np

        from .shared.constants.biometric_constants import EMBEDDING_DIMENSION

        return {
            "embedding": np.full(EMBEDDING_DIMENSION, 0.1, dtype=np.float32),
            "anti_spoofing_score": 0.1,
            "transcribed_text": "mock transcription",
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with optimized startup."""
    import asyncio

    logger.info("Starting Voice Biometrics API...")

    # 1. Initialize database pool FIRST (blocking - required for cleanup job)
    if os.getenv("TESTING") != "True":
        try:
            await init_db_pool()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Continue anyway - health check will report degraded status

    # 2. Load ML models in background (non-blocking)
    model_loading_task = None
    if os.getenv("TESTING") != "True":
        model_loading_task = asyncio.create_task(init_biometric_engine_async())
        logger.info("ML model loading started in background...")
    else:
        from .infrastructure.config import dependencies as _deps

        mock_engine = MockVoiceBiometricEngineFacade()
        app.state.biometric_engine = mock_engine
        # The dependency in src/infrastructure/config/dependencies.py
        # reads from a module-level _biometric_engine global, so we
        # must also wire that — without this, get_voice_biometric_engine()
        # returns None in TESTING mode and every enrollment/verification
        # call hits `voice_engine.<method>` on None.
        _deps._biometric_engine = mock_engine
        _deps._models_loaded = True

    # 3. Start background cleanup job for expired challenges
    from .config import CHALLENGE_CLEANUP_INTERVAL
    from .infrastructure.config.dependencies import get_db_pool
    from .infrastructure.persistence.postgres_challenge_repository import (
        PostgresChallengeRepository,
    )
    from .jobs.cleanup_expired_challenges import cleanup_expired_challenges_job

    cleanup_task = None
    if os.getenv("TESTING") != "True":
        try:
            pool = await get_db_pool()
            challenge_repo = PostgresChallengeRepository(pool)
            cleanup_task = asyncio.create_task(
                cleanup_expired_challenges_job(
                    challenge_repo, CHALLENGE_CLEANUP_INTERVAL
                )
            )
            logger.info(
                f"Challenge cleanup job started (interval: {CHALLENGE_CLEANUP_INTERVAL}s)"
            )
        except Exception as e:
            logger.warning(f"Could not start cleanup job: {e}")

    # Wait for models to finish loading before accepting requests
    if model_loading_task:
        try:
            await model_loading_task
            app.state.biometric_engine = get_voice_biometric_engine()
            logger.info("✅ Application fully ready")
        except Exception as e:
            logger.error(f"Model loading failed: {e}")

    # 4. Registrar versiones de modelos ML en model_version (trazabilidad forense).
    #    Mapea model_type='antispoofing' (interno) al CHECK del enum model_version.kind='antispoof'.
    if os.getenv("TESTING") != "True":
        try:
            from .infrastructure.biometrics.model_manager import ModelManager
            from .infrastructure.persistence.postgres_model_version_repository import (
                PostgresModelVersionRepository,
            )

            pool = await get_db_pool()
            model_repo = PostgresModelVersionRepository(pool)
            manager = ModelManager(models_dir=os.getenv("MODEL_CACHE_DIR", "models"))
            registry = [
                {
                    "kind": (
                        "antispoof"
                        if cfg.model_type == "antispoofing"
                        else cfg.model_type
                    ),
                    "name": key,
                    "version": cfg.version,
                }
                for key, cfg in manager.models.items()
            ]
            await model_repo.register_models(registry)
            logger.info(
                f"Registered {len(registry)} ML model versions in model_version"
            )
        except Exception as exc:
            logger.warning(f"Could not register model versions: {exc}")

    # 5. Restaurar la sesión de dataset recording si estaba activa antes del reinicio
    if os.getenv("TESTING") != "True":
        try:
            from evaluation.dataset_recorder import dataset_recorder

            from .infrastructure.persistence.postgres_system_settings_repository import (
                PostgresSystemSettingsRepository,
            )

            pool = await get_db_pool()
            settings_repo = PostgresSystemSettingsRepository(pool)
            stored = await settings_repo.get("dataset_recording")
            if stored and stored.get("enabled"):
                session_dir = stored.get("session_dir")
                if session_dir:
                    from pathlib import Path

                    dataset_recorder.current_session = stored.get("session_id")
                    dataset_recorder.session_dir = Path(session_dir)
                    dataset_recorder.enabled = True
                    logger.info(
                        f"Restored dataset recording session {stored.get('session_id')}"
                    )
        except Exception as exc:
            logger.warning(f"Could not restore dataset recording: {exc}")

    yield

    logger.info("Shutting down Voice Biometrics API...")

    # Cancel cleanup task
    if cleanup_task and not cleanup_task.done():
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Cleanup job cancelled")

    # Cleanup resources
    await close_db_pool()
    logger.info("Database connection pool closed")


from .api.error_handlers import generic_exception_handler, value_error_handler


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Voice Biometrics API",
        description="Secure voice authentication and enrollment system",
        version="1.0.0",
        lifespan=lifespan,  # Commented out for testing
        docs_url="/docs",
        redoc_url=None,  # ReDoc deshabilitado permanentemente
    )

    # Add state for the limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS (only in production)
        env = os.getenv("ENV", "development")
        if env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    # Add CORS middleware
    origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    env = os.getenv("ENV", "development")

    # Add common development ports in development mode
    if env == "development":
        dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        for origin in dev_origins:
            if origin not in origins:
                origins.append(origin)

    # Configure CORS - more restrictive in production
    if env == "production":
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        allowed_headers = ["Content-Type", "Authorization"]
    else:
        allowed_methods = ["*"]
        allowed_headers = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
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
                "enrollment": "/api/enrollment",
                "verification": "/api/verification",
                "phrases": "/api/phrases",
                "admin": "/api/admin",
                "challenges": "/api/challenges",
            },
        }

    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(admin_router, prefix="/api/admin", tags=["administration"])
    app.include_router(phrase_router, prefix="/api/phrases", tags=["phrases"])
    app.include_router(challenge_router, prefix="/api/challenges", tags=["challenges"])
    app.include_router(enrollment_router, prefix="/api/enrollment", tags=["enrollment"])
    app.include_router(
        verification_router, prefix="/api/verification", tags=["verification"]
    )
    app.include_router(evaluation_router)  # Already has prefix defined in router
    app.include_router(dataset_recording_router)  # Dataset recording endpoints

    # Health check endpoint with readiness status
    @app.get("/health")
    async def health_check():
        readiness = is_ready()
        status = "healthy" if readiness["ready"] else "starting"
        return {
            "status": status,
            "service": "voice-biometrics-api",
            "version": "1.0.0",
            "components": {
                "database": "up" if readiness["database"] else "down",
                "models": "loaded" if readiness["models"] else "loading",
            },
        }

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
