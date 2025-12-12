"""Configuration settings for the voice biometrics application."""

import os
from typing import Dict

# Challenge expiration timeouts (in seconds) based on difficulty
CHALLENGE_TIMEOUT: Dict[str, int] = {
    'easy': 120,      # 2 minutes
    'medium': 180,    # 3 minutes  
    'hard': 240      # 4 minutes
}

# Cleanup job interval (in seconds)
CHALLENGE_CLEANUP_INTERVAL = 30  # Run cleanup every 30 seconds

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voice_biometrics')
DB_USER = os.getenv('DB_USER', 'voice_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'voice_password')

# Biometric thresholds
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.60"))
ANTI_SPOOFING_THRESHOLD = float(os.getenv("ANTI_SPOOFING_THRESHOLD", "0.5"))
