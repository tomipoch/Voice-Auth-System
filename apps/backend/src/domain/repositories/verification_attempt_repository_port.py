"""Puerto de repositorio de intentos de verificación (auth_attempt + scores + audio_blob)."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class VerificationAttemptRepositoryPort(ABC):
    """Persistencia de decisiones de verificación, señales técnicas y audio de evidencia."""

    @abstractmethod
    async def save_audio_blob(self, content: bytes, mime: str = "audio/wav") -> UUID:
        """Persiste un audio crudo (evidencia) y devuelve su id."""

    @abstractmethod
    async def record_attempt(
        self,
        *,
        user_id: UUID,
        accept: bool,
        reason: str,
        similarity: float,
        spoof_prob: float,
        phrase_match: float,
        phrase_ok: bool,
        client_id: Optional[UUID] = None,
        challenge_id: Optional[UUID] = None,
        audio_id: Optional[UUID] = None,
        policy_id: Optional[str] = None,
        total_latency_ms: Optional[int] = None,
        inference_ms: Optional[int] = None,
        speaker_model_id: Optional[int] = None,
        antispoof_model_id: Optional[int] = None,
        asr_model_id: Optional[int] = None,
    ) -> UUID:
        """Persiste un intento en auth_attempt + scores; devuelve el id del intento."""

    @abstractmethod
    async def get_history(self, user_id: UUID, limit: int = 50) -> list[dict]:
        """Devuelve intentos de un usuario ordenados por recencia (con scores)."""

    @abstractmethod
    async def count_by_user(self, user_id: UUID) -> int:
        """Cuenta los intentos de un usuario."""
