"""Puerto de repositorio de clientes de la API (client_app + api_key)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class ClientAppRepositoryPort(ABC):
    """Gestión de clientes externos de la API y sus API keys (solo hash persistido)."""

    @abstractmethod
    async def create_client(self, name: str, contact_email: Optional[str] = None) -> tuple[UUID, str]:
        """Crea un cliente con una API key nueva; devuelve (client_id, raw_key)."""

    @abstractmethod
    async def get_client_by_api_key(self, key_hash: str) -> Optional[dict]:
        """Devuelve el cliente asociado a un key_hash (no revocado) o None."""

    @abstractmethod
    async def list_clients(self) -> list[dict]:
        """Lista clientes (sin key_hash)."""

    @abstractmethod
    async def rotate_api_key(self, client_id: UUID) -> Optional[str]:
        """Revoca la key actual y emite una nueva; devuelve la raw_key o None."""

    @abstractmethod
    async def revoke_api_key(self, client_id: UUID) -> None:
        """Revoca la key actual del cliente."""
