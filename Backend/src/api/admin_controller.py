"""FastAPI controller for admin endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from .auth_controller import get_current_user

logger = logging.getLogger(__name__)

admin_router = APIRouter()

# Pydantic models
class UserInfo(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company: str
    status: str
    enrollment_status: str
    created_at: datetime
    last_login: Optional[datetime] = None
    voice_template: Optional[dict] = None

class SystemStats(BaseModel):
    total_users: int
    active_users: int
    total_verifications_today: int
    successful_verifications_today: int
    success_rate: float
    avg_response_time: int
    enrollment_completion_rate: float
    system_uptime: float

class ActivityLog(BaseModel):
    id: str
    user_id: str
    user_name: str
    action: str
    timestamp: datetime
    details: str

class PaginatedUsers(BaseModel):
    users: List[UserInfo]
    total: int
    page: int
    limit: int
    total_pages: int

# Mock data
mock_system_stats = SystemStats(
    total_users=156,
    active_users=143,
    total_verifications_today=89,
    successful_verifications_today=84,
    success_rate=94.2,
    avg_response_time=142,
    enrollment_completion_rate=78.5,
    system_uptime=99.8
)

mock_activity_logs = [
    ActivityLog(
        id="act-1",
        user_id="user-2",
        user_name="María García",
        action="verification_success",
        timestamp=datetime.now(),
        details="Verificación exitosa desde dispositivo móvil"
    ),
    ActivityLog(
        id="act-2",
        user_id="user-3",
        user_name="Carlos López",
        action="enrollment_started",
        timestamp=datetime.now(),
        details="Iniciado proceso de enrollment"
    ),
    ActivityLog(
        id="act-3",
        user_id="dev-user-1",
        user_name="Usuario Desarrollo",
        action="login",
        timestamp=datetime.now(),
        details="Inicio de sesión exitoso"
    ),
    ActivityLog(
        id="act-4",
        user_id="user-2",
        user_name="María García",
        action="verification_failed",
        timestamp=datetime.now(),
        details="Verificación fallida - ruido ambiental detectado"
    )
]

# Import mock users from auth controller
from .auth_controller import mock_users

def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@admin_router.get("/users", response_model=PaginatedUsers)
async def get_users(
    page: int = 1,
    limit: int = 10,
    current_user: dict = Depends(require_admin)
):
    """
    Get paginated list of users (admin only).
    Admins only see users from their company, superadmin sees all users.
    """
    try:
        # Import mock_users from auth_controller
        from .auth_controller import mock_users
        
        # Convert mock_users to list and add additional fields
        users_list = []
        for email, user_data in mock_users.items():
            user_info = UserInfo(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                company=user_data["company"],
                status="active",
                enrollment_status="completed" if user_data["voice_template"] else "pending",
                created_at=user_data["created_at"],
                last_login=user_data["created_at"],  # Mock last_login
                voice_template=user_data["voice_template"]
            )
            users_list.append(user_info)
        
        # Filter users based on current user's role
        if current_user["role"] == "admin":
            # Admins can only see users from their company
            users_list = [u for u in users_list if u.company == current_user["company"]]
        # Superadmins see all users (no filtering needed)
        
        # Apply pagination
        
        # Implement pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_users = users_list[start_index:end_index]
        
        return PaginatedUsers(
            users=paginated_users,
            total=len(users_list),
            page=page,
            limit=limit,
            total_pages=(len(users_list) + limit - 1) // limit
        )
    
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@admin_router.get("/stats", response_model=SystemStats)
async def get_system_stats(current_user: dict = Depends(require_admin)):
    """
    Get system statistics (admin only).
    """
    try:
        return mock_system_stats
    
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@admin_router.get("/activity", response_model=List[ActivityLog])
async def get_recent_activity(
    limit: int = 10,
    current_user: dict = Depends(require_admin)
):
    """
    Get recent activity logs (admin only).
    """
    try:
        return mock_activity_logs[:limit]
    
    except Exception as e:
        logger.error(f"Error getting activity logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete a user (admin only).
    """
    try:
        # Find user in mock_users
        user_to_delete = None
        email_to_delete = None
        
        for email, user_data in mock_users.items():
            if user_data["id"] == user_id:
                user_to_delete = user_data
                email_to_delete = email
                break
        
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't allow deleting yourself
        if user_id == current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete user
        del mock_users[email_to_delete]
        
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: dict = Depends(require_admin)
):
    """
    Update user data (admin only).
    """
    try:
        # Find user in mock_users
        user_to_update = None
        email_to_update = None
        
        for email, existing_user in mock_users.items():
            if existing_user["id"] == user_id:
                user_to_update = existing_user
                email_to_update = email
                break
        
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update allowed fields
        allowed_fields = ["name", "role"]
        for field in allowed_fields:
            if field in user_data:
                user_to_update[field] = user_data[field]
        
        return {
            "message": "User updated successfully",
            "user": {
                "id": user_to_update["id"],
                "name": user_to_update["name"],
                "email": user_to_update["email"],
                "role": user_to_update["role"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )