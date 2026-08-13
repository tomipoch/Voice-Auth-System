"""Puerto de repositorio de sesiones de enrolamiento persistentes."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID


class EnrollmentSessionRepositoryPort(ABC):
    """Persistencia de sesiones de enrolamiento (sobreviven reinicios)."""

    @abstractmethod
    async def upsert(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        challenges: list,
        samples_collected: int,
        challenge_index: int,
        expires_at: datetime,
    ) -> None:
        """Crea o actualiza la sesión activa del usuario (UNIQUE por user_id)."""

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[dict]:
        """Devuelve la sesión por id si existe y no está completada."""

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> Optional[dict]:
        """Devuelve la sesión activa de un usuario."""

    @abstractmethod
    async def mark_completed(self, session_id: UUID) -> None:
        """Marca la sesión como completada (completed_at = now())."""
