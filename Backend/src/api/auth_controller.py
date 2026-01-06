"""FastAPI controller for authentication endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt

logger = logging.getLogger(__name__)

auth_router = APIRouter()

# Security
security = HTTPBearer()

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "voice-biometrics-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# Pydantic models
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: dict

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    settings: Optional[dict] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserProfile(BaseModel):
    id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    role: str
    company: Optional[str] = None
    created_at: datetime
    voice_template: Optional[dict] = None
    settings: Optional[dict] = None


from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@auth_router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLoginRequest,
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Authenticate user and return access token.
    """
    
    user = await user_repo.get_user_by_email(user_data.email)
    logger.info(f"Login attempt for email={user_data.email}, found user_id={user['id'] if user else None}")
    
    if user and user.get("locked_until") and user["locked_until"] > datetime.now():
        logger.warning(f"Login failed for email={user_data.email}: Account locked until {user['locked_until']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked. Try again after {user['locked_until']}.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user or not verify_password(user_data.password, user["password"]):
        if user:
            await user_repo.increment_failed_auth_attempts(user["id"])
            logger.warning(f"Login failed for user_id={user['id']}, email={user_data.email}: Invalid credentials. Failed attempts: {user['failed_auth_attempts'] + 1}")
            if user["failed_auth_attempts"] + 1 >= MAX_FAILED_ATTEMPTS:
                await user_repo.lock_user_account(user["id"], timedelta(minutes=LOCKOUT_MINUTES))
                logger.error(f"User account user_id={user['id']}, email={user_data.email} locked due to too many failed attempts.")
        else:
            logger.warning(f"Login failed for email={user_data.email}: User not found or invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reset failed attempts on successful login
    await user_repo.reset_failed_auth_attempts(user["id"])
    
    # Create access token with email as subject (standard practice)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],  # Use email as subject for consistency
            "user_id": str(user["id"]),
            "role": user.get("role", "user")
        },
        expires_delta=access_token_expires
    )
    
    # Create refresh token (longer expiration)
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["id"]),
            "type": "refresh"
        },
        expires_delta=refresh_token_expires
    )
    
    logger.info(f"Login successful for user_id={user['id']}, email={user_data.email}")
    
    # Remove sensitive data
    user_response = {
        "id": str(user["id"]),
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        "email": user["email"],
        "role": user.get("role", "user"),
        "company": user.get("company", ""),
        "created_at": user["created_at"].isoformat(),
        "voice_template": None,  # Will be populated when user enrolls
        "settings": user.get("settings", {})
    }
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        user=user_response
    )

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Refresh access token using refresh token.
    Returns a new access token if the refresh token is valid.
    """
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and validate refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise auth_error
            
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid refresh token: {e}")
        raise auth_error
    
    # Get user from database
    user = await user_repo.get_user_by_email(email)
    if user is None:
        logger.warning(f"Refresh token for non-existent user: {email}")
        raise auth_error
    
    # Check if account is locked
    if user.get("locked_until") and user["locked_until"] > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked. Try again after {user['locked_until']}.",
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["id"]),
            "role": user.get("role", "user")
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"Token refreshed for user_id={user['id']}, email={email}")
    
    # Prepare user response
    user_response = {
        "id": str(user["id"]),
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        "email": user["email"],
        "role": user.get("role", "user"),
        "company": user.get("company", ""),
        "created_at": user["created_at"].isoformat(),
        "voice_template": None,
        "settings": user.get("settings", {})
    }
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,  # Return same refresh token
        user=user_response
    )

@auth_router.post("/register")
async def register(
    user_data: UserRegisterRequest,
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Register a new user.
    """
    # Check if user already exists
    if await user_repo.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create new user
    user_id = await user_repo.create_user(
        email=user_data.email,
        password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        company=user_data.company
    )
    
    return {
        "message": "User registered successfully",
        "user_id": str(user_id)
    }

@auth_router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    """
    # Parse settings if it's a string
    settings = current_user.get("settings", {})
    if isinstance(settings, str):
        import json
        try:
            settings = json.loads(settings) if settings else {}
        except (json.JSONDecodeError, ValueError):
            settings = {}
    
    return UserProfile(
        id=str(current_user["id"]),
        name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        email=current_user["email"],
        role=current_user.get("role", "user"),
        company=current_user.get("company", ""),
        created_at=current_user["created_at"],
        voice_template=None,  # Will be populated when user enrolls
        settings=settings
    )

@auth_router.post("/logout")
async def logout():
    """
    Logout user (in a stateless JWT system, this is mainly for client-side cleanup).
    """
    return {"message": "Successfully logged out"}

@auth_router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "company": current_user["company"],
        "settings": current_user.get("settings", {})
    }

@auth_router.patch("/profile", response_model=UserProfile)
async def update_profile(
    user_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Update current user profile.
    """
    # Convert Pydantic model to dict, excluding None values
    update_data = user_data.model_dump(exclude_none=True)
        
    await user_repo.update_user(current_user["id"], update_data)
    
    # Get updated user
    updated_user = await user_repo.get_user(current_user["id"])
    
    # Parse settings if it's a string
    settings = updated_user.get("settings", {})
    if isinstance(settings, str):
        import json
        try:
            settings = json.loads(settings) if settings else {}
        except (json.JSONDecodeError, ValueError):
            settings = {}
    
    return UserProfile(
        id=str(updated_user["id"]),
        name=f"{updated_user.get('first_name', '')} {updated_user.get('last_name', '')}".strip(),
        first_name=updated_user.get("first_name"),
        last_name=updated_user.get("last_name"),
        email=updated_user["email"],
        role=updated_user.get("role", "user"),
        company=updated_user.get("company", ""),
        created_at=updated_user["created_at"],
        voice_template=None,
        settings=settings
    )

@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Change user password.
    Requires current password for verification.
    """
    # Get user from database
    user = await user_repo.get_user(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password (field is 'password' not 'password_hash')
    if not verify_password(password_data.current_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password length
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash new password
    new_password_hash = bcrypt.hashpw(
        password_data.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Update password in database (field is 'password')
    await user_repo.update_user(current_user["id"], {"password": new_password_hash})
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Password changed successfully"
        }
    )