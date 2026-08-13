"""Application service for authentication (login, refresh, lockout, audit)."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from ..config import ALGORITHM, SECRET_KEY
from ..domain.repositories.audit_log_repository_port import AuditLogRepositoryPort
from ..domain.repositories.user_repository_port import UserRepositoryPort
from ..shared.types.common_types import AuditAction

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Domain-level authentication error with HTTP-relevant status."""

    def __init__(self, status_code: int, detail: str, headers: Optional[dict] = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}


class AuthService:
    """Encapsulates login, refresh, and lockout business logic.

    Controllers remain thin: they translate AuthError into HTTP responses
    and handle request-scoped concerns (IP, user agent).
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Increased from 30 to 120 minutes
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
    ):
        self._user_repo = user_repo
        self._audit_repo = audit_repo

    # -- token helpers -------------------------------------------------

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # -- user response shape ------------------------------------------

    @staticmethod
    def user_to_response(user: dict) -> dict:
        """Build the public user dict returned to clients."""
        return {
            "id": str(user["id"]),
            "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            "email": user["email"],
            "role": user.get("role", "user"),
            "company": user.get("company", ""),
            "created_at": user["created_at"].isoformat(),
            "voice_template": None,
            "settings": user.get("settings", {}),
        }

    # -- login ---------------------------------------------------------

    async def login(self, email: str, password: str, ip: str) -> dict:
        """Authenticate a user and return tokens + user dict.

        Raises AuthError on bad credentials or locked account.
        """
        user = await self._user_repo.get_user_by_email(email)
        logger.info(
            "Login attempt for email=%s, found user_id=%s",
            email,
            user["id"] if user else None,
        )

        if not user:
            logger.warning(
                "Failed login attempt for non-existent user: %s from IP: %s",
                email,
                ip,
            )
            raise AuthError(
                status_code=401,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Lockout check
        locked_until = user.get("locked_until")
        if locked_until and locked_until > datetime.now(timezone.utc):
            logger.warning(
                "Login attempt for locked account: %s from IP: %s",
                email,
                ip,
            )
            raise AuthError(
                status_code=403,
                detail=(
                    f"Account is locked due to multiple failed login attempts. "
                    f"Please try again after {self.LOCKOUT_MINUTES} minutes."
                ),
            )

        # Password check
        if not bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            await self._user_repo.increment_failed_auth_attempts(user["id"])
            failed_attempts = user.get("failed_auth_attempts", 0) + 1
            logger.warning(
                "Failed login attempt for user: %s (attempt %d/%d) from IP: %s",
                email,
                failed_attempts,
                self.MAX_FAILED_ATTEMPTS,
                ip,
            )
            if failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                await self._user_repo.lock_user_account(
                    user["id"], timedelta(minutes=self.LOCKOUT_MINUTES)
                )
                logger.error(
                    "User account user_id=%s, email=%s locked due to too many failed attempts.",
                    user["id"],
                    email,
                )
            raise AuthError(
                status_code=401,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Success: reset failed attempts
        await self._user_repo.reset_failed_auth_attempts(user["id"])
        logger.info(
            "Successful login for user: %s (ID: %s) from IP: %s",
            email,
            user["id"],
            ip,
        )

        access_token = self.create_access_token(
            data={
                "sub": user["email"],
                "user_id": str(user["id"]),
                "role": user.get("role", "user"),
            }
        )
        refresh_token = self.create_access_token(
            data={
                "sub": user["email"],
                "user_id": str(user["id"]),
                "type": "refresh",
            },
            expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        logger.info("Login successful for user_id=%s, email=%s", user["id"], email)

        await self._audit_repo.log_event(
            actor=str(user["id"]),
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=str(user["id"]),
            success=True,
            metadata={
                "email": email,
                "message": "User logged in successfully",
                "ip_address": ip,
            },
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": self.user_to_response(user),
        }

    # -- refresh -------------------------------------------------------

    async def refresh(self, refresh_token: str) -> dict:
        """Validate a refresh token and issue a new access token.

        Raises AuthError on invalid token or locked account.
        """
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
        except jwt.PyJWTError as exc:
            logger.warning("Invalid refresh token: %s", exc)
            raise AuthError(status_code=401, detail="Invalid refresh token")

        if email is None or token_type != "refresh":
            raise AuthError(status_code=401, detail="Invalid refresh token")

        user = await self._user_repo.get_user_by_email(email)
        if user is None:
            logger.warning("Refresh token for non-existent user: %s", email)
            raise AuthError(status_code=401, detail="Invalid refresh token")

        locked_until = user.get("locked_until")
        if locked_until and locked_until > datetime.now(timezone.utc):
            raise AuthError(
                status_code=403,
                detail=f"Account locked. Try again after {locked_until}.",
            )

        new_access_token = self.create_access_token(
            data={
                "sub": user["email"],
                "user_id": str(user["id"]),
                "role": user.get("role", "user"),
            }
        )
        logger.info("Token refreshed for user_id=%s, email=%s", user["id"], email)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": self.user_to_response(user),
        }
