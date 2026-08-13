"""Puerto de repositorio de versiones de modelos ML (trazabilidad forense)."""

from abc import ABC, abstractmethod
from typing import Optional


class ModelVersionRepositoryPort(ABC):
    """Registro y consulta de versiones de modelos en model_version."""

    @abstractmethod
    async def register_models(self, models: list[dict]) -> dict[str, Optional[int]]:
        """Registra modelos [{kind, name, version}] y devuelve {kind: id} (primero por kind)."""

    @abstractmethod
    async def get_model_id(self, kind: str) -> Optional[int]:
        """Devuelve el id del modelo registrado de un kind ('speaker'|'antispoof'|'asr')."""
