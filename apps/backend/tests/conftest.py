"""Pytest configuration and fixtures for voice biometrics tests.

Column names match the real schema in infra/db/init.sql (after Fase 1
self-contained fix): email, password (bcrypt), first_name, last_name, role,
company, settings.
"""

import os
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import asyncpg
import pytest
from dotenv import load_dotenv

load_dotenv()

# Set testing environment
os.environ["TESTING"] = "True"

# Test DB name. Falls back to the main DB if TEST_DB_NAME is not set.
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "voice_biometrics_test")
DB_NAME = os.getenv("DB_NAME", "voice_biometrics")


def _db_params(database: str) -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": database,
        "user": os.getenv("DB_USER", "voice_user"),
        "password": os.getenv("DB_PASSWORD", "voice_password"),
    }


async def _ensure_test_db() -> None:
    """Create the test database if it does not exist, then run init.sql.

    Connects to the default ``postgres`` database to issue CREATE DATABASE,
    then to the new test DB to apply infra/db/init.sql. Idempotent.
    """
    admin_params = _db_params("postgres")
    conn = await asyncpg.connect(**admin_params)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()

    # Locate infra/db/init.sql relative to this conftest (Backend/tests/conftest.py).
    # Tests live at Backend/tests/, project root is two levels up.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    init_sql_path = os.path.join(project_root, "..", "infra", "db", "init.sql")
    if not os.path.isfile(init_sql_path):
        # Fallback: search upward for any init.sql (legacy Backend/init.sql).
        here = os.path.dirname(__file__)
        for _ in range(6):
            cand = os.path.join(here, "init.sql")
            if os.path.isfile(cand):
                init_sql_path = cand
                break
            here = os.path.dirname(here)
    if os.path.isfile(init_sql_path):
        with open(init_sql_path) as f:
            sql = f.read()
        conn = await asyncpg.connect(**_db_params(TEST_DB_NAME))
        try:
            await conn.execute(sql)
        finally:
            await conn.close()

    # Aplica migraciones pendientes con el mismo runner de producción, para que
    # la BD de pruebas quede idéntica a una BD real.
    import subprocess
    import sys

    runner = Path(project_root).parent / "infra" / "db" / "apply_migrations.py"
    if runner.is_file():
        env = dict(os.environ)
        env.pop("DATABASE_URL", None)
        env["DB_NAME"] = TEST_DB_NAME
        subprocess.run([sys.executable, str(runner)], env=env, check=True)


# Bootstrap is performed lazily inside the async db_pool fixture, on the same
# event loop pytest-asyncio uses for the tests. Running it in a separate
# asyncio.run() creates a different loop and trips pytest-asyncio 1.4's
# "attached to a different loop" guard when asyncpg connections are then
# used from the test loop.
_bootstrap_done = False


@pytest.fixture(scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Create a database connection pool for tests against the test DB."""
    global _bootstrap_done
    if not _bootstrap_done:
        await _ensure_test_db()
        _bootstrap_done = True
    pool = await asyncpg.create_pool(min_size=1, max_size=5, **_db_params(TEST_DB_NAME))
    yield pool
    await pool.close()


@pytest.fixture
async def db_connection(db_pool):
    """Provide a database connection for a test (rolled back after)."""
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            yield connection


@pytest.fixture
async def test_user(db_connection):
    """Create a test user with the real schema columns."""
    from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION

    user_id = await db_connection.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        f"user-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Test",
        "User",
        "user",
        "acme",
        "{}",
    )
    return user_id


@pytest.fixture
async def test_admin(db_connection):
    """Create a test admin user with the real schema columns."""
    admin_id = await db_connection.fetchval(
        """
        INSERT INTO "user" (email, password, first_name, last_name, role, company, settings)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        f"admin-{uuid.uuid4().hex[:8]}@example.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC",
        "Admin",
        "User",
        "admin",
        "acme",
        "{}",
    )
    return admin_id


@pytest.fixture
async def test_phrase(db_connection):
    """Create a test phrase."""
    phrase_id = await db_connection.fetchval(
        """
        INSERT INTO phrase (text, difficulty, source, language, word_count, char_count,
                            is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, TRUE, $7)
        RETURNING id
        """,
        "Esta es una frase de prueba para testing",
        "medium",
        "test",
        "es",
        8,
        41,
        datetime.now(timezone.utc),
    )
    return phrase_id


@pytest.fixture
async def test_challenge(db_connection, test_user, test_phrase):
    """Create a test challenge."""
    challenge_id = await db_connection.fetchval(
        """
        INSERT INTO challenge (user_id, phrase, phrase_id, expires_at)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        test_user,
        "Esta es una frase de prueba para testing",
        test_phrase,
        datetime.now(timezone.utc) + timedelta(seconds=90),
    )
    return challenge_id


@pytest.fixture
def sample_audio_bytes():
    """Provide sample audio bytes for testing (minimal WAV, silence)."""
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


@pytest.fixture
def mock_embedding():
    """Provide a mock voice embedding of the configured dimension."""
    import numpy as np
    from src.shared.constants.biometric_constants import EMBEDDING_DIMENSION
    return np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
