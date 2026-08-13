"""Tests del runner de migraciones contra la BD de pruebas (voice_biometrics_test).

El runner se ejecuta como subproceso para probar la CLI real.
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[4] / "infra" / "db" / "apply_migrations.py"
# apps/backend/tests/unit -> apps/backend/tests -> apps/backend -> apps -> repo_root (parents[4])


def _runner_env() -> dict:
    """Entorno para el subproceso: apunta a la BD de pruebas y quita DATABASE_URL."""
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    env["DB_HOST"] = os.getenv("DB_HOST", "localhost")
    env["DB_PORT"] = os.getenv("DB_PORT", "5432")
    env["DB_USER"] = os.getenv("DB_USER", "voice_user")
    env["DB_PASSWORD"] = os.getenv("DB_PASSWORD", "voice_password")
    env["DB_NAME"] = os.getenv("TEST_DB_NAME", "voice_biometrics_test")
    return env


def _run_runner(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        capture_output=True,
        text=True,
        env=_runner_env(),
        cwd=Path(__file__).resolve().parents[4],
    )


@pytest.mark.asyncio
async def test_schema_migrations_table_exists(db_pool):
    """Tras el arranque del conftest, la tabla de control existe."""
    exists = await db_pool.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations')"
    )
    assert exists is True


def test_runner_is_idempotent():
    """Ejecutar dos veces no aplica nada la segunda vez."""
    first = _run_runner()
    assert first.returncode == 0, first.stderr
    second = _run_runner()
    assert second.returncode == 0, second.stderr
    assert "Sin migraciones pendientes" in second.stdout


@pytest.mark.asyncio
async def test_runner_applies_and_tracks_new_migration(tmp_path, db_pool):
    """Una migración nueva se aplica y queda registrada con checksum."""
    name = f"001_temporal_{uuid.uuid4().hex[:8]}.sql"
    migration = tmp_path / name
    migration.write_text("SELECT 1;", encoding="utf-8")

    result = _run_runner("--dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert name in result.stdout

    row = await db_pool.fetchrow(
        "SELECT checksum FROM schema_migrations WHERE filename = $1", name
    )
    assert row is not None
    assert len(row["checksum"]) == 64  # sha256 hex

    await db_pool.execute("DELETE FROM schema_migrations WHERE filename = $1", name)


def test_runner_rejects_modified_applied_migration(tmp_path):
    """Editar una migración ya aplicada produce error (checksum)."""
    name = f"002_temporal_{uuid.uuid4().hex[:8]}.sql"
    migration = tmp_path / name
    migration.write_text("SELECT 1;", encoding="utf-8")

    first = _run_runner("--dir", str(tmp_path))
    assert first.returncode == 0, first.stderr

    migration.write_text("SELECT 2;", encoding="utf-8")
    second = _run_runner("--dir", str(tmp_path))
    assert second.returncode == 1
    assert "checksum" in second.stderr.lower()


def test_runner_dry_run_applies_nothing(tmp_path):
    """--dry-run reporta la pendiente pero no la aplica ni la registra."""
    name = f"003_temporal_{uuid.uuid4().hex[:8]}.sql"
    (tmp_path / name).write_text("SELECT 1;", encoding="utf-8")

    result = _run_runner("--dry-run", "--dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert name in result.stdout
    assert "[dry-run]" in result.stdout
