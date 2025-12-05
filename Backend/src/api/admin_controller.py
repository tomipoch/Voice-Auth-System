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
    total_enrollments: int
    total_verifications: int
    success_rate: float  # 0.0 to 1.0
    active_users_24h: int
    failed_verifications_24h: int

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

# Mock data for activity logs (TODO: replace with real data)
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
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository, get_audit_log_repository

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
    
    # Transform users to match UserInfo model
    transformed_users = []
    for user in users:
        transformed_users.append({
            "id": str(user["id"]),  # Convert UUID to string
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "company": user.get("company", ""),
            "status": "active" if user.get("is_active", True) else "inactive",
            "enrollment_status": "enrolled" if user.get("has_voiceprint", False) else "pending",
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "voice_template": None  # Not exposing this in list view
        })
    
    return PaginatedUsers(
        users=transformed_users,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )

@admin_router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository)
):
    """
    Get system statistics (admin only).
    """
    from datetime import datetime, timedelta
    
    # Get total users (use high limit to get all)
    all_users_result = await user_repo.get_all_users(page=1, limit=10000)
    all_users = all_users_result[0]  # First element is the list of users
    total_users = all_users_result[1]  # Second element is the total count
    
    # Get total enrollments (users with voiceprints)
    users_with_voiceprints = [u for u in all_users if u.get('has_voiceprint', False)]
    total_enrollments = len(users_with_voiceprints)
    
    # Get audit logs for the last 24 hours
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    # Get recent logs (last 24h)
    recent_logs = await audit_repo.get_logs(
        start_time=last_24h,
        limit=10000  # High limit to get all recent logs
    )
    
    # Get all verification logs (for overall success rate)
    all_verification_logs = await audit_repo.get_logs(
        action='VERIFICATION',
        limit=10000
    )
    
    # Count verifications in last 24h
    verification_logs_24h = [log for log in recent_logs if log.get('action') == 'VERIFICATION']
    
    # Count successful and failed verifications in last 24h
    successful_24h = [log for log in verification_logs_24h if log.get('success', False)]
    failed_verifications_24h = len(verification_logs_24h) - len(successful_24h)
    
    # Calculate overall success rate
    if all_verification_logs:
        all_successful = [log for log in all_verification_logs if log.get('success', False)]
        success_rate = len(all_successful) / len(all_verification_logs)
    else:
        success_rate = 0.0
    
    # Count active users in last 24h (users who performed any action)
    active_user_ids = set(log.get('actor') for log in recent_logs if log.get('actor'))
    active_users_24h = len(active_user_ids)
    
    return SystemStats(
        total_users=total_users,
        total_enrollments=total_enrollments,
        total_verifications=len(all_verification_logs),
        success_rate=success_rate,
        active_users_24h=active_users_24h,
        failed_verifications_24h=failed_verifications_24h
    )

@admin_router.get("/activity", response_model=List[ActivityLog])
async def get_recent_activity(
    limit: int = 100,
    action: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository)
):
    """
    Get recent activity logs (admin only).
    """
    try:
        # Get logs from repository
        logs = await audit_repo.get_logs(
            action=action,
            limit=limit
        )
        
        # Transform to ActivityLog model
        activity_logs = []
        for log in logs:
            # Determine user name from actor
            user_name = log.get('actor', 'system')
            if '@' not in user_name and user_name != 'system':
                user_name = f"user-{user_name[:8]}"  # Truncate UUID
            
            activity_logs.append(ActivityLog(
                id=str(log.get('id', '')),
                user_id=log.get('actor', 'system'),
                user_name=user_name,
                action=log.get('action', 'UNKNOWN'),
                timestamp=log.get('timestamp', datetime.utcnow()),
                details=log.get('metadata', {}).get('message', '') or str(log.get('metadata', {}))
            ))
        
        return activity_logs
    except Exception as e:
        logger.error(f"Error getting activity logs: {e}")
        # Return empty list on error instead of raising exception
        return []


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
    rule_value: float  # Changed from 'value' to 'rule_value'
    description: str
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
        transformed_rules = []
        for rule in rules:
            # Handle rule_value which might be a JSON string or a float
            rule_value = rule['rule_value']
            if isinstance(rule_value, str):
                try:
                    import json
                    parsed_value = json.loads(rule_value)
                    # If it's a dict with 'value' key, extract it
                    if isinstance(parsed_value, dict) and 'value' in parsed_value:
                        rule_value = float(parsed_value['value'])
                    else:
                        rule_value = float(parsed_value)
                except (json.JSONDecodeError, ValueError, TypeError):
                    # If parsing fails, try direct conversion
                    rule_value = float(rule_value)
            else:
                rule_value = float(rule_value)
            
            transformed_rules.append(PhraseQualityRule(
                id=str(rule['id']),
                rule_name=rule['rule_name'],
                rule_type=rule['rule_type'],
                rule_value=rule_value,
                description=rule.get('description', ''),
                is_active=rule['is_active'],
                created_at=rule['created_at'],
                updated_at=rule['updated_at']
            ))
        
        return transformed_rules
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