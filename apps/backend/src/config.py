"""Configuration settings for the voice biometrics application."""

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load .env from Backend/ (parent of src/) so JWT settings are read consistently
# regardless of CWD when this module is imported.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _BACKEND_DIR / ".env"
if _ENV_PATH.is_file():
    load_dotenv(_ENV_PATH)

# Challenge expiration timeouts (in seconds) based on difficulty
CHALLENGE_TIMEOUT: Dict[str, int] = {
    'easy': 120,      # 2 minutes
    'medium': 180,    # 3 minutes
    'hard': 240       # 4 minutes
}

# Cleanup job interval (in seconds)
CHALLENGE_CLEANUP_INTERVAL = 30  # Run cleanup every 30 seconds

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voice_biometrics')
DB_USER = os.getenv('DB_USER', 'voice_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'voice_password')

# JWT configuration
# Single source of truth for SECRET_KEY and ALGORITHM. Both auth_controller
# and the admin dependency import these directly so the layer inversion
# (api ← infrastructure) is broken.
ALGORITHM = "HS256"

# Python evaluates function defaults at module import time; using
# os.environ.setdefault keeps the unified default in this single file.
if "SECRET_KEY" not in os.environ or not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "dev-secret-key-change-in-production"
SECRET_KEY = os.environ["SECRET_KEY"]

ENV = os.getenv("ENV", "development")

# Validate SECRET_KEY in production
if ENV == "production":
    if SECRET_KEY == "dev-secret-key-change-in-production" or not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY must be set to a strong random value in production. "
            "Do not use the default development key!"
        )

# Biometric thresholds (single source of truth)
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.60"))
ANTI_SPOOFING_THRESHOLD = float(os.getenv("ANTI_SPOOFING_THRESHOLD", "0.5"))
