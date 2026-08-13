"""PostgreSQL implementation of ClientAppRepositoryPort."""

import hashlib
import secrets
from typing import Optional
from uuid import UUID, uuid4

import asyncpg

from ...domain.repositories.client_app_repository_port import ClientAppRepositoryPort


class PostgresClientAppRepository(ClientAppRepositoryPort):
    """Gestión de client_app y api_key en PostgreSQL."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    @staticmethod
    def hash_api_key(raw_key: str) -> str:
        """Hash SHA-256 de la key cruda (nunca se persiste la key)."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_api_key() -> str:
        return secrets.token_urlsafe(32)

    async def create_client(
        self, name: str, contact_email: Optional[str] = None
    ) -> tuple[UUID, str]:
        client_id = uuid4()
        raw_key = self._generate_api_key()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO client_app (id, name, contact_email) VALUES ($1, $2, $3)",
                    client_id,
                    name,
                    contact_email,
                )
                await conn.execute(
                    "INSERT INTO api_key (id, client_id, key_hash, created_at) VALUES ($1, $2, $3, now())",
                    uuid4(),
                    client_id,
                    self.hash_api_key(raw_key),
                )
        return client_id, raw_key

    async def get_client_by_api_key(self, key_hash: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT c.id, c.name, c.contact_email, k.revoked_at
                FROM api_key k
                JOIN client_app c ON c.id = k.client_id
                WHERE k.key_hash = $1 AND k.revoked_at IS NULL
                """,
                key_hash,
            )
            if not row:
                return None
            result = dict(row)
            result["id"] = str(result["id"])
            return result

    async def list_clients(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT c.id, c.name, c.contact_email,
                       k.created_at AS key_created_at, k.revoked_at
                FROM client_app c
                LEFT JOIN api_key k ON k.client_id = c.id
                ORDER BY c.name ASC
                """)
            clients = []
            for row in rows:
                client = dict(row)
                client["id"] = str(client["id"])
                clients.append(client)
            return clients

    async def rotate_api_key(self, client_id: UUID) -> Optional[str]:
        raw_key = self._generate_api_key()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.execute(
                    "UPDATE api_key SET revoked_at = now() WHERE client_id = $1 AND revoked_at IS NULL",
                    client_id,
                )
                # asyncpg returns "UPDATE n"; n=0 => no se revocó nada (cliente inexistente o sin key activa)
                if result.endswith(" 0"):
                    return None
                await conn.execute(
                    "INSERT INTO api_key (id, client_id, key_hash, created_at) VALUES ($1, $2, $3, now())",
                    uuid4(),
                    client_id,
                    self.hash_api_key(raw_key),
                )
        return raw_key

    async def revoke_api_key(self, client_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE api_key SET revoked_at = now() WHERE client_id = $1 AND revoked_at IS NULL",
                client_id,
            )
