#!/usr/bin/env python3
"""Aplica migraciones SQL pendientes en orden y las registra en schema_migrations.

Uso:
    python infra/db/apply_migrations.py [--dry-run] [--dir PATH]

Variables de entorno: DATABASE_URL (prioritaria) o DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.
Cada migración se aplica en una transacción propia y se registra con su checksum;
editar una migración ya aplicada produce error. Los subdirectorios se ignoran.
"""

import argparse
import asyncio
import hashlib
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import asyncpg

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _checksum(sql: str) -> str:
    """SHA-256 del contenido de la migración."""
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _db_connection_params() -> dict:
    """Parámetros de conexión desde DATABASE_URL o variables DB_*."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": (parsed.path or "/voice_biometrics").lstrip("/"),
            "user": parsed.username or "voice_user",
            "password": parsed.password or "voice_password",
        }
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "voice_biometrics"),
        "user": os.getenv("DB_USER", "voice_user"),
        "password": os.getenv("DB_PASSWORD", "voice_password"),
    }


async def _ensure_tracking_table(conn: asyncpg.Connection) -> None:
    """Crea schema_migrations si no existe (idempotente)."""
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


async def apply_pending_migrations(
    migrations_dir: Path = MIGRATIONS_DIR,
    dry_run: bool = False,
) -> list[str]:
    """Aplica las migraciones pendientes y devuelve los nombres aplicados.

    Lanza RuntimeError si una migración ya aplicada fue modificada.
    """
    files = sorted(p for p in migrations_dir.glob("*.sql") if p.is_file())
    conn = await asyncpg.connect(**_db_connection_params())
    try:
        await _ensure_tracking_table(conn)
        applied_rows = await conn.fetch(
            "SELECT filename, checksum FROM schema_migrations"
        )
        applied = {row["filename"]: row["checksum"] for row in applied_rows}

        pending: list[tuple[Path, str]] = []
        for path in files:
            sql = path.read_text(encoding="utf-8")
            checksum = _checksum(sql)
            previous = applied.get(path.name)
            if previous is not None:
                if previous != checksum:
                    raise RuntimeError(
                        f"Migración {path.name} ya aplicada con checksum distinto. "
                        f"¿Fue editada tras aplicarse? Registrada: {previous}, actual: {checksum}"
                    )
                continue
            pending.append((path, checksum))

        if not pending:
            print(f"Sin migraciones pendientes ({len(files)} ya aplicadas).")
            return []

        for path, checksum in pending:
            print(f"{'[dry-run] ' if dry_run else ''}Aplicando {path.name}...")
            if dry_run:
                continue
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute(
                    "INSERT INTO schema_migrations (filename, checksum) VALUES ($1, $2)",
                    path.name,
                    checksum,
                )
        return [path.name for path, _ in pending]
    finally:
        await conn.close()


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra qué se aplicaría")
    parser.add_argument("--dir", type=Path, default=MIGRATIONS_DIR, help="Directorio de migraciones")
    args = parser.parse_args()

    try:
        applied = await apply_pending_migrations(args.dir, dry_run=args.dry_run)
        if applied:
            print(f"{len(applied)} migración(es) aplicada(s): {', '.join(applied)}")
        return 0
    except Exception as exc:  # noqa: BLE001 - el runner reporta y sale con código 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
