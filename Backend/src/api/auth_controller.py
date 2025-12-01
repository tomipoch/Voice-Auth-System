"""FastAPI controller for authentication endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from datetime import datetime, timedelta
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
    user: dict

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company: str
    created_at: datetime
    voice_template: Optional[dict] = None



from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """Get current user from JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "role": user.get("role", "user")}, expires_delta=access_token_expires
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
        "voice_template": None  # Will be populated when user enrolls
    }
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
    return UserProfile(
        id=str(current_user["id"]),
        name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        email=current_user["email"],
        role=current_user.get("role", "user"),
        company=current_user.get("company", ""),
        created_at=current_user["created_at"],
        voice_template=None  # Will be populated when user enrolls
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
        "company": current_user["company"]
    }