"""FastAPI controller for authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging
from datetime import datetime, timedelta, timezone
import jwt

from src.utils.validators import validate_rut, format_rut
from src.config import SECRET_KEY, ALGORITHM
from src.application.auth_service import AuthService, AuthError
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.repositories.audit_log_repository_port import AuditLogRepositoryPort
from src.infrastructure.config.dependencies import (
    get_user_repository,
    get_audit_log_repository,
)
from src.shared.types.common_types import AuditAction
from .rate_limit import limiter, login_limit, refresh_limit

logger = logging.getLogger(__name__)

auth_router = APIRouter()
security = HTTPBearer()

MAX_FAILED_ATTEMPTS = AuthService.MAX_FAILED_ATTEMPTS
LOCKOUT_MINUTES = AuthService.LOCKOUT_MINUTES
ACCESS_TOKEN_EXPIRE_MINUTES = AuthService.ACCESS_TOKEN_EXPIRE_MINUTES


# Pydantic models with OpenAPI documentation
class UserLoginRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", min_length=8)

    model_config = {"json_schema_extra": {"examples": [{"email": "user@example.com", "password": "SecurePass123"}]}}


class UserRegisterRequest(BaseModel):
    """Request body for user registration."""
    first_name: str = Field(..., description="User's first name", min_length=1, max_length=50)
    last_name: str = Field(..., description="User's last name", min_length=1, max_length=50)
    rut: Optional[str] = Field(None, description="Chilean RUT (optional)", pattern=r"^\d{7,8}-[\dkK]$")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password (min 8 chars, 1 uppercase, 1 lowercase, 1 number)", min_length=8)
    company: Optional[str] = Field(None, description="Company name (optional)")


class TokenResponse(BaseModel):
    """Response containing authentication tokens."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token for obtaining new access tokens")
    user: dict = Field(..., description="User profile data")


class ProfileUpdateRequest(BaseModel):
    """Request body for updating user profile."""
    first_name: Optional[str] = Field(None, description="New first name")
    last_name: Optional[str] = Field(None, description="New last name")
    rut: Optional[str] = Field(None, description="Chilean RUT")
    settings: Optional[dict] = Field(None, description="User settings object")


class PasswordChangeRequest(BaseModel):
    """Request body for changing password."""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., description="New password (must meet strength requirements)")


class UserProfile(BaseModel):
    id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    role: str
    company: Optional[str] = None
    rut: Optional[str] = None
    created_at: datetime
    voice_template: Optional[dict] = None
    settings: Optional[dict] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """Get current user from JWT token."""
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise auth_error
    except jwt.PyJWTError:
        raise auth_error

    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise auth_error
    return user


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    """
    import re

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    import bcrypt
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


async def get_auth_service(
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, audit_repo=audit_repo)


def _auth_error_to_http(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail, headers=exc.headers or None)


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit(login_limit)
async def login(
    request: Request,
    user_data: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return access token."""
    ip = request.client.host if request.client else "unknown"
    try:
        result = await auth_service.login(
            email=user_data.email, password=user_data.password, ip=ip
        )
    except AuthError as exc:
        raise _auth_error_to_http(exc)

    return TokenResponse(**result)


@auth_router.post("/refresh", response_model=TokenResponse)
@limiter.limit(refresh_limit)
async def refresh_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    try:
        result = await auth_service.refresh(refresh_token=refresh_token)
    except AuthError as exc:
        raise _auth_error_to_http(exc)
    return TokenResponse(**result)


@auth_router.post("/register")
async def register(
    user_data: UserRegisterRequest,
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
):
    """Register a new user."""
    if user_data.rut:
        if not validate_rut(user_data.rut):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid RUT format. Use format: 12345678-9 (without dots)"
            )

    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    existing = await user_repo.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    import bcrypt
    hashed = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_dict = {
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "rut": user_data.rut,
        "email": user_data.email,
        "password": hashed,
        "company": user_data.company,
        "role": "user",
    }
    new_user = await user_repo.create_user(user_dict)

    await audit_repo.log_event(
        actor=str(new_user["id"]),
        action=AuditAction.USER_REGISTERED,
        entity_type="user",
        entity_id=str(new_user["id"]),
        success=True,
        metadata={"email": user_data.email, "message": "User registered"},
    )

    return {"success": True, "user_id": str(new_user["id"]), "email": new_user["email"]}


@auth_router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserProfile(
        id=str(current_user["id"]),
        name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        email=current_user["email"],
        role=current_user.get("role", "user"),
        company=current_user.get("company"),
        rut=current_user.get("rut"),
        created_at=current_user["created_at"],
        voice_template=None,
        settings=current_user.get("settings"),
    )


@auth_router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
):
    """Update current user's profile."""
    update_data = {k: v for k, v in profile_data.dict(exclude_unset=True).items() if v is not None}
    if "rut" in update_data and update_data["rut"]:
        if not validate_rut(update_data["rut"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid RUT format"
            )
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await user_repo.update_user(current_user["id"], update_data)
    await audit_repo.log_event(
        actor=str(current_user["id"]),
        action=AuditAction.PROFILE_UPDATED,
        entity_type="user",
        entity_id=str(current_user["id"]),
        success=True,
        metadata={"updated_fields": list(update_data.keys())},
    )
    return {"success": True, "message": "Profile updated"}


@auth_router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
):
    """Change current user's password."""
    if not verify_password(request.current_password, current_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    import bcrypt
    hashed = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await user_repo.update_user(current_user["id"], {"password": hashed})
    await audit_repo.log_event(
        actor=str(current_user["id"]),
        action=AuditAction.PASSWORD_CHANGED,
        entity_type="user",
        entity_id=str(current_user["id"]),
        success=True,
        metadata={"message": "Password changed"},
    )
    return {"success": True, "message": "Password changed"}
