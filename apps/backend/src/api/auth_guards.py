"""Authorization helpers for endpoint protection."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status

from src.api.auth_controller import get_current_user

__all__ = ["get_current_user", "enforce_user_scope", "require_admin_user"]


def _is_admin(user: dict) -> bool:
    return user.get("role") in ("admin", "superadmin")


async def enforce_user_scope(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency that ensures the current user can act on ``user_id``.

    - Admins and superadmins can act on any user.
    - Regular users can only act on their own user_id.

    Returns the current user dict on success.
    """
    if _is_admin(current_user):
        return current_user

    token_user_id = str(current_user.get("id") or current_user.get("user_id") or "")
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources",
        )
    return current_user


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
