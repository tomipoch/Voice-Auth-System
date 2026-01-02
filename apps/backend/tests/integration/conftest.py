"""Pytest configuration for integration tests."""

import pytest
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

# Import the FastAPI app
import sys
# The following line is already present in the original code, but the instruction implies adding it.
# To avoid duplication, I'll ensure it's there.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Let's re-evaluate the sys.path.insert. The original code does not have it.
# The instruction adds it. So it should be added.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.main import create_app


# Load environment variables from test.env
env_path = Path(__file__).parent.parent.parent / 'test.env'
load_dotenv(env_path)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client(event_loop) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


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
