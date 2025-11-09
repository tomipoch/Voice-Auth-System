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

# JWT Configuration
SECRET_KEY = "voice-biometrics-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic models
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

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

# Mock users database (in production this would be a real database)
mock_users = {
    # SuperAdmin - Acceso completo al sistema
    "superadmin@voicebio.com": {
        "id": "superadmin-001",
        "name": "Super Administrador",
        "email": "superadmin@voicebio.com",
        "hashed_password": bcrypt.hashpw("SuperAdmin2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "superadmin",
        "company": "VoiceBio System",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-superadmin-001",
            "created_at": datetime.now(),
            "samples_count": 5,
            "quality_score": 0.98
        }
    },
    
    # Admin de Empresa A
    "admin@empresaa.com": {
        "id": "admin-001",
        "name": "Administrador Empresa A",
        "email": "admin@empresaa.com",
        "hashed_password": bcrypt.hashpw("AdminEmpresa2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "admin",
        "company": "Empresa A",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-admin-001",
            "created_at": datetime.now(),
            "samples_count": 5,
            "quality_score": 0.96
        }
    },
    
    # Admin de Empresa B
    "admin@empresab.com": {
        "id": "admin-002",
        "name": "Administrador Empresa B",
        "email": "admin@empresab.com",
        "hashed_password": bcrypt.hashpw("AdminEmpresa2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "admin",
        "company": "Empresa B",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-admin-002",
            "created_at": datetime.now(),
            "samples_count": 4,
            "quality_score": 0.94
        }
    },
    
    # Usuarios de Empresa A
    "juan.perez@empresaa.com": {
        "id": "user-001",
        "name": "Juan Carlos Pérez",
        "email": "juan.perez@empresaa.com",
        "hashed_password": bcrypt.hashpw("User2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "company": "Empresa A",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-user-001",
            "created_at": datetime.now(),
            "samples_count": 3,
            "quality_score": 0.89
        }
    },
    
    "maria.garcia@empresaa.com": {
        "id": "user-002",
        "name": "María García López",
        "email": "maria.garcia@empresaa.com",
        "hashed_password": bcrypt.hashpw("User2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "company": "Empresa A",
        "created_at": datetime.now(),
        "voice_template": None
    },
    
    # Usuarios de Empresa B
    "carlos.rodriguez@empresab.com": {
        "id": "user-003",
        "name": "Carlos Rodríguez Silva",
        "email": "carlos.rodriguez@empresab.com",
        "hashed_password": bcrypt.hashpw("User2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "company": "Empresa B",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-user-003",
            "created_at": datetime.now(),
            "samples_count": 2,
            "quality_score": 0.85
        }
    },
    
    "ana.martinez@empresab.com": {
        "id": "user-004",
        "name": "Ana Martínez Ruiz",
        "email": "ana.martinez@empresab.com",
        "hashed_password": bcrypt.hashpw("User2024!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "company": "Empresa B",
        "created_at": datetime.now(),
        "voice_template": None
    },
    
    # Usuarios de desarrollo (mantener compatibilidad)
    "dev@test.com": {
        "id": "dev-user-1",
        "name": "Usuario Desarrollo",
        "email": "dev@test.com",
        "hashed_password": bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "company": "Test Company",
        "created_at": datetime.now(),
        "voice_template": None
    },
    "admin@test.com": {
        "id": "admin-dev-1",
        "name": "Admin Desarrollo",
        "email": "admin@test.com",
        "hashed_password": bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "admin",
        "company": "Test Company",
        "created_at": datetime.now(),
        "voice_template": {
            "id": "vt-admin-dev",
            "created_at": datetime.now(),
            "samples_count": 5,
            "quality_score": 0.95
        }
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    """Get user by email from mock database."""
    return mock_users.get(email)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@auth_router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLoginRequest):
    """
    Authenticate user and return access token.
    """
    try:
        user = get_user_by_email(user_data.email)
        if not user or not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        # Remove sensitive data
        user_response = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "company": user["company"],
            "created_at": user["created_at"].isoformat(),
            "voice_template": user["voice_template"]
        }
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/register")
async def register(user_data: UserRegisterRequest):
    """
    Register a new user.
    """
    try:
        # Check if user already exists
        if get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = {
            "id": f"user-{len(mock_users) + 1}",
            "name": user_data.name,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "role": "user",
            "created_at": datetime.now(),
            "voice_template": None
        }
        
        # Add to mock database
        mock_users[user_data.email] = new_user
        
        return {
            "message": "User registered successfully",
            "user_id": new_user["id"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    """
    try:
        return UserProfile(
            id=current_user["id"],
            name=current_user["name"],
            email=current_user["email"],
            role=current_user["role"],
            company=current_user["company"],
            created_at=current_user["created_at"],
            voice_template=current_user["voice_template"]
        )
    
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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