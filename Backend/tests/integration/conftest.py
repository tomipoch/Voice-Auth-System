"""Pytest fixtures for integration tests."""

import pytest
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from test.env
env_path = Path(__file__).parent.parent.parent / 'test.env'
load_dotenv(env_path)

@pytest.fixture(scope="session")
async def db_pool():
    """Fixture for a test database connection pool."""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'voice_biometrics_test')
    db_user = os.getenv('DB_USER', 'voice_user')
    db_password = os.getenv('DB_PASSWORD', 'voice_password')

    pool = await asyncpg.create_pool(
        host=db_host,
        port=int(db_port),
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5,
        timeout=5
    )
    yield pool
    await pool.close()
