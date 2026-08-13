"""PostgreSQL implementation of ModelVersionRepositoryPort."""

import asyncpg
from typing import Optional

from ...domain.repositories.model_version_repository_port import ModelVersionRepositoryPort


class PostgresModelVersionRepository(ModelVersionRepositoryPort):
    """Registro y consulta de model_version en PostgreSQL."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def register_models(self, models: list[dict]) -> dict[str, Optional[int]]:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for model in models:
                    await conn.execute(
                        """
                        INSERT INTO model_version (kind, name, version)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (kind, name, version) DO NOTHING
                        """,
                        model["kind"], model["name"], model["version"],
                    )
            by_kind: dict[str, Optional[int]] = {}
            for model in models:
                kind = model["kind"]
                if kind not in by_kind:
                    by_kind[kind] = await conn.fetchval(
                        """
                        SELECT id FROM model_version
                        WHERE kind = $1 ORDER BY name LIMIT 1
                        """,
                        kind,
                    )
            return by_kind

    async def get_model_id(self, kind: str) -> Optional[int]:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT id FROM model_version WHERE kind = $1 ORDER BY name LIMIT 1", kind
            )
