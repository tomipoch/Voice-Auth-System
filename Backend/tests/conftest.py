"""Pytest configuration and fixtures for voice biometrics tests."""

import pytest
import asyncio
from typing import AsyncGenerator
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Set testing environment
os.environ["TESTING"] = "True"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Create a database connection pool for tests."""
    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "voice_biometrics"),
        user=os.getenv("DB_USER", "voice_user"),
        password=os.getenv("DB_PASSWORD", "voice_password"),
        min_size=1,
        max_size=5,
    )
    yield pool
    await pool.close()


@pytest.fixture
async def db_connection(db_pool):
    """Provide a database connection for a test."""
    async with db_pool.acquire() as connection:
        # Start a transaction
        async with connection.transaction():
            yield connection
            # Transaction will be rolled back automatically


@pytest.fixture
async def test_user(db_connection):
    """Create a test user."""
    user_id = await db_connection.fetchval(
        """
        INSERT INTO "user" (email, password_hash, name, role)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        "test@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",  # "password"
        "Test User",
        "user"
    )
    return user_id


@pytest.fixture
async def test_admin(db_connection):
    """Create a test admin user."""
    admin_id = await db_connection.fetchval(
        """
        INSERT INTO "user" (email, password_hash, name, role)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        "admin@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Admin User",
        "admin"
    )
    return admin_id


@pytest.fixture
async def test_phrase(db_connection):
    """Create a test phrase."""
    phrase_id = await db_connection.fetchval(
        """
        INSERT INTO phrase (text, difficulty, source, book_id)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        "Esta es una frase de prueba para testing",
        "medium",
        "test",
        None
    )
    return phrase_id


@pytest.fixture
async def test_challenge(db_connection, test_user, test_phrase):
    """Create a test challenge."""
    from datetime import datetime, timedelta
    
    challenge_id = await db_connection.fetchval(
        """
        INSERT INTO challenge (user_id, phrase, phrase_id, expires_at)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        test_user,
        "Esta es una frase de prueba para testing",
        test_phrase,
        datetime.now() + timedelta(seconds=90)
    )
    return challenge_id


@pytest.fixture
def sample_audio_bytes():
    """Provide sample audio bytes for testing."""
    # Minimal WAV file (silence)
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


@pytest.fixture
def mock_embedding():
    """Provide a mock voice embedding."""
    import numpy as np
    return np.random.rand(192).astype(np.float32)
