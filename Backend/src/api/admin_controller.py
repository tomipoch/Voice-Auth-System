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
    first_name: str
    last_name: str
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

from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository

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
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Get paginated list of users (admin only).
    Admins only see users from their company, superadmin sees all users.
    """
    # Filter users based on current user's role
    if current_user["role"] == "admin":
        # Admins can only see users from their company
        users, total = await user_repo.get_users_by_company(
            current_user["company"], page, limit
        )
    else:
        users, total = await user_repo.get_all_users(page, limit)
    
    return PaginatedUsers(
        users=users,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )

@admin_router.get("/stats", response_model=SystemStats)
async def get_system_stats(current_user: dict = Depends(require_admin)):
    """
    Get system statistics (admin only).
    """
    return mock_system_stats

@admin_router.get("/activity", response_model=List[ActivityLog])
async def get_recent_activity(
    limit: int = 10,
    current_user: dict = Depends(require_admin)
):
    """
    Get recent activity logs (admin only).
    """
    return mock_activity_logs[:limit]

@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Delete a user (admin only).
    """
    # Don't allow deleting yourself
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    await user_repo.delete_user(user_id)
    
    return {"message": "User deleted successfully"}

@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """
    Update user data (admin only).
    """
    await user_repo.update_user(user_id, user_data)
    
    return {
        "message": "User updated successfully",
    }


# =====================================================
# Phrase Quality Rules Endpoints
# =====================================================

class PhraseQualityRule(BaseModel):
    """Phrase quality rule model."""
    id: str
    rule_name: str
    rule_type: str
    value: float
    description: str
    unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UpdateRuleRequest(BaseModel):
    """Request to update a rule value."""
    value: float


from ..infrastructure.config.dependencies import get_phrase_quality_rules_service
from ..application.phrase_quality_rules_service import PhraseQualityRulesService


@admin_router.get("/phrase-rules", response_model=List[PhraseQualityRule])
async def get_phrase_quality_rules(
    include_inactive: bool = False,
    current_user: dict = Depends(require_admin),
    rules_service: PhraseQualityRulesService = Depends(get_phrase_quality_rules_service)
):
    """
    Get all phrase quality rules (admin only).
    
    - **include_inactive**: Include inactive rules in the response
    """
    try:
        rules = await rules_service.get_all_rules(include_inactive=include_inactive)
        
        # Transform to response model
        return [
            PhraseQualityRule(
                id=str(rule['id']),
                rule_name=rule['rule_name'],
                rule_type=rule['rule_type'],
                rule_value=float(rule['rule_value']),
                description=rule.get('description', ''),
                is_active=rule['is_active'],
                created_at=rule['created_at'],
                updated_at=rule['updated_at']
            )
            for rule in rules
        ]
    except Exception as e:
        logger.error(f"Error getting phrase quality rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get phrase quality rules"
        )


@admin_router.patch("/phrase-rules/{rule_name}")
async def update_phrase_quality_rule(
    rule_name: str,
    request: UpdateRuleRequest,
    current_user: dict = Depends(require_admin),
    rules_service: PhraseQualityRulesService = Depends(get_phrase_quality_rules_service)
):
    """
    Update a phrase quality rule value (admin only).
    
    - **rule_name**: Name of the rule to update
    - **value**: New numeric value for the rule
    """
    try:
        from uuid import UUID
        admin_id = UUID(current_user['id'])
        
        success = await rules_service.update_rule(
            rule_name=rule_name,
            new_value=request.value,
            admin_id=admin_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Rule '{rule_name}' updated to {request.value}",
            "rule_name": rule_name,
            "new_value": request.value
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating phrase quality rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update phrase quality rule"
        )


@admin_router.post("/phrase-rules/{rule_name}/toggle")
async def toggle_phrase_quality_rule(
    rule_name: str,
    is_active: bool,
    current_user: dict = Depends(require_admin),
    rules_service: PhraseQualityRulesService = Depends(get_phrase_quality_rules_service)
):
    """
    Enable or disable a phrase quality rule (admin only).
    
    - **rule_name**: Name of the rule to toggle
    - **is_active**: True to enable, False to disable
    """
    try:
        success = await rules_service.toggle_rule(rule_name, is_active)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Rule '{rule_name}' {'enabled' if is_active else 'disabled'}",
            "rule_name": rule_name,
            "is_active": is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling phrase quality rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle phrase quality rule"
        )