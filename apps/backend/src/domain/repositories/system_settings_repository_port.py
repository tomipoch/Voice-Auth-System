"""Puerto de repositorio de configuración global del sistema."""

from abc import ABC, abstractmethod
from typing import Optional


class SystemSettingsRepositoryPort(ABC):
    """Lectura y escritura de system_settings (JSONB)."""

    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        """Devuelve el value JSONB de una clave o None."""

    @abstractmethod
    async def set(self, key: str, value: dict, updated_by: Optional[str] = None) -> None:
        """Upsert del value JSONB de una clave."""
