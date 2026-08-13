"""Authorization helpers for endpoint protection."""

import hashlib
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from src.api.auth_controller import get_current_user

__all__ = [
    "get_current_user",
    "enforce_user_scope",
    "require_admin_user",
    "get_optional_client",
]


def _is_admin(user: dict) -> bool:
    return user.get("role") in ("admin", "superadmin")


def check_user_scope_or_admin(target_user_id: UUID, current_user: dict) -> dict:
    """Ensure ``current_user`` can act on ``target_user_id``.

    - Admins and superadmins can act on any user.
    - Regular users can only act on their own user_id.

    Returns ``current_user`` on success. Raises ``HTTPException`` 403 otherwise.
    Reusable for endpoints where ``target_user_id`` comes from a request body
    rather than a path parameter (e.g. ``/verification/start``).
    """
    if _is_admin(current_user):
        return current_user

    token_user_id = str(current_user.get("id") or current_user.get("user_id") or "")
    if token_user_id != str(target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources",
        )
    return current_user


async def enforce_user_scope(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency that ensures the current user can act on ``user_id``.

    Use as ``Depends(enforce_user_scope)`` on path-param endpoints.
    For body-param endpoints, call ``check_user_scope_or_admin`` directly.
    """
    return check_user_scope_or_admin(user_id, current_user)


async def require_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency that requires an admin or superadmin user."""
    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_optional_client(
    x_api_key: Optional[str] = Header(default=None),
) -> Optional[dict]:
    """Dependency opcional: si llega X-API-Key válida, devuelve el cliente; si no, None.

    La autenticación por usuario (JWT) sigue funcionando igual; esta dependency
    permite a clientes externos usar la API con su propia key.
    """
    if not x_api_key:
        return None
    from src.domain.repositories.client_app_repository_port import (
        ClientAppRepositoryPort,
    )
    from src.infrastructure.config.dependencies import get_client_app_repository

    repo: ClientAppRepositoryPort = await get_client_app_repository()
    key_hash = hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()
    client = await repo.get_client_by_api_key(key_hash)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return client
