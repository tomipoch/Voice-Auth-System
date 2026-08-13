"""PostgreSQL implementation of SystemSettingsRepositoryPort."""

import json
import asyncpg
from typing import Optional

from ...domain.repositories.system_settings_repository_port import SystemSettingsRepositoryPort


class PostgresSystemSettingsRepository(SystemSettingsRepositoryPort):
    """Persistencia de system_settings en PostgreSQL."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def get(self, key: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM system_settings WHERE key = $1", key
            )
            if not row:
                return None
            value = row["value"]
            if isinstance(value, str):
                return json.loads(value)
            return dict(value)

    async def set(self, key: str, value: dict, updated_by: Optional[str] = None) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO system_settings (key, value, updated_at, updated_by)
                VALUES ($1, $2, now(), $3)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = now(),
                    updated_by = EXCLUDED.updated_by
                """,
                key, json.dumps(value, ensure_ascii=False), updated_by,
            )
