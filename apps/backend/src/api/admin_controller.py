"""FastAPI controller for admin endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
import logging
import json
from datetime import datetime, timedelta

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
    daily_verifications: List[dict]  # [{"date": "2023-10-27", "count": 12}, ...]

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

from ..domain.repositories.UserRepositoryPort import UserRepositoryPort
from ..domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository, get_audit_log_repository


# Helper functions to reduce cognitive complexity
def _parse_metadata(metadata):
    """Parse metadata from JSON string if needed."""
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    return metadata if metadata else {}


def _belongs_to_company(log, company_user_ids: set, company_emails: set) -> bool:
    """Check if a log belongs to the company (used for admin filtering)."""
    actor = log.get('actor', '')
    # Direct match: actor is a user_id or email from company
    if actor in company_user_ids or actor in company_emails:
        return True
    # System logs: check metadata for user_id
    if actor == 'system':
        metadata = _parse_metadata(log.get('metadata'))
        user_id_in_meta = metadata.get('user_id')
        if user_id_in_meta and str(user_id_in_meta) in company_user_ids:
            return True
    return False


def _filter_logs_by_company(logs: list, company_user_ids: set, company_emails: set) -> list:
    """Filter logs to only include those belonging to company users."""
    return [log for log in logs if _belongs_to_company(log, company_user_ids, company_emails)]


def _count_verifications(logs: list, verification_actions: set, verification_types: set, since_time=None):
    """Count verification logs, optionally filtering by time."""
    result = []
    for log in logs:
        if log.get('action') not in verification_actions:
            continue
        if log.get('entity_type') not in verification_types:
            continue
        if since_time and log.get('timestamp') < since_time:
            continue
        result.append(log)
    return result


def _calculate_daily_stats(logs: list, verification_actions: set, verification_types: set, days: int = 7):
    """Calculate daily verification counts for the last N days."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    daily_stats = {}
    for i in range(days):
        date_key = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_stats[date_key] = 0
    
    for log in logs:
        if log.get('action') in verification_actions and log.get('entity_type') in verification_types:
            log_date = log.get('timestamp').strftime('%Y-%m-%d')
            if log_date in daily_stats:
                daily_stats[log_date] += 1
    
    return [{" date": date, "count": count} for date, count in sorted(daily_stats.items())]


def _transform_log_to_activity(log, default_timestamp) -> dict:
    """Transform a raw log to ActivityLog format."""
    user_name = log.get('actor', 'system')
    if '@' not in user_name and user_name != 'system':
        user_name = f"user-{user_name[:8]}"
    
    metadata = _parse_metadata(log.get('metadata', {}))
    details = metadata.get('message', '') if isinstance(metadata, dict) else str(metadata)
    if not details:
        details = str(metadata) if metadata else ''
    
    return {
        "id": str(log.get('id', '')),
        "user_id": log.get('actor', 'system'),
        "user_name": user_name,
        "action": log.get('action', 'UNKNOWN'),
        "timestamp": log.get('timestamp', default_timestamp),
        "details": details
    }


def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin or superadmin role."""
    if current_user["role"] not in ["admin", "superadmin"]:
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
    Admins only see regular users from their company (no admins/superadmins).
    Superadmin sees all users.
    """
    # Filter users based on current user's role
    if current_user["role"] == "admin":
        # Admins can only see users from their company
        users, total = await user_repo.get_users_by_company(
            current_user["company"], page, limit
        )
        # Filter out admin and superadmin users
        users = [u for u in users if u.get("role") == "user"]
        total = len(users)  # Update total count after filtering
    else:
        # Superadmin sees all users
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
        total_pages=(total + limit - 1) // limit if total > 0 else 0
    )


from ..domain.repositories.VoiceSignatureRepositoryPort import VoiceSignatureRepositoryPort
from ..infrastructure.config.dependencies import get_user_repository, get_audit_log_repository, get_voice_signature_repository

@admin_router.get("/users/{user_id}", response_model=UserInfo)
async def get_user_details(
    user_id: str,
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    voice_repo: VoiceSignatureRepositoryPort = Depends(get_voice_signature_repository)
):
    """
    Get single user details (admin only).
    Admins can only see users from their company.
    """
    user = await user_repo.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permission for admin (not superadmin)
    if current_user["role"] == "admin" and user.get("company") != current_user["company"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get voiceprint details if exists
    voice_template = None
    if user.get("has_voiceprint"):
        # We need to fetch the voiceprint to get its ID and creation date
        # Note: user_id implies we should find it.
        try:
            # We import UUID to cast string user_id
            from uuid import UUID
            vp = await voice_repo.get_voiceprint_by_user(UUID(user_id))
            if vp:
                voice_template = {
                    "id": str(vp.id),
                    "created_at": vp.created_at,
                    "model_type": "ECAPA-TDNN", # Hardcoded for now as it's the standard
                    "sample_count": 3 # Placeholder, or retrieve from history/metadata if available
                }
        except Exception as e:
            logger.warning(f"Failed to fetch voiceprint details for user {user_id}: {e}")

    return UserInfo(
        id=str(user["id"]),
        first_name=user.get("first_name", ""),
        last_name=user.get("last_name", ""),
        email=user.get("email", ""),
        role=user.get("role", "user"),
        company=user.get("company", ""),
        status="active" if user.get("is_active", True) else "inactive",
        enrollment_status="enrolled" if user.get("has_voiceprint", False) else "pending",
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
        voice_template=voice_template
    )

@admin_router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository)
):
    """
    Get system statistics (admin only).
    Admins see stats for their company only, superadmin sees all.
    """
    # Get users based on role
    if current_user["role"] == "admin":
        # Admins only see their company's users
        all_users_result = await user_repo.get_users_by_company(
            current_user["company"], 
            page=1, 
            limit=10000
        )
    else:
        # Superadmin sees all users
        all_users_result = await user_repo.get_all_users(page=1, limit=10000)
    
    all_users = all_users_result[0]  # First element is the list of users
    total_users = all_users_result[1]  # Second element is the total count
    
    # Get total enrollments (users with voiceprints)
    users_with_voiceprints = [u for u in all_users if u.get('has_voiceprint', False)]
    total_enrollments = len(users_with_voiceprints)
    
    # Get audit logs for the last 24 hours
    from datetime import timezone
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7_days = now - timedelta(days=7)
    
    # Get recent logs (last 7 days for trends, filtering done later)
    # Get recent logs (last 7 days for trends, but we'll also use this for all-time stats)
    # To get all-time verification stats, we need a separate query without time limit
    recent_logs = await audit_repo.get_logs(
        start_time=last_7_days,
        limit=10000  # High limit to get all recent logs
    )
    
    # Get ALL verification logs for all-time stats (no time filter)
    all_logs = await audit_repo.get_logs(
        limit=50000  # Very high limit for all-time data
    )
    
    # If admin, filter logs to only include users from their company
    if current_user["role"] == "admin":
        company_user_ids = {str(u["id"]) for u in all_users}
        company_emails = {str(u.get("email")) for u in all_users if u.get("email")}
        recent_logs = _filter_logs_by_company(recent_logs, company_user_ids, company_emails)
        all_logs = _filter_logs_by_company(all_logs, company_user_ids, company_emails)
    
    # Count verifications (only results, ignore starts)
    # Action matches AuditAction.VERIFY ('VERIFY') or legacy 'VERIFICATION'
    verification_actions = {'VERIFY', 'VERIFICATION'}
    verification_types = {'verification_result', 'quick_verification', 'multi_verification_complete'}
    
    verification_logs_24h = [
        log for log in recent_logs 
        if log.get('action') in verification_actions
        and log.get('entity_type') in verification_types
        and log.get('timestamp') >= last_24h
    ]
    
    # Count successful and failed verifications in last 24h
    successful_24h = [log for log in verification_logs_24h if log.get('success', False)]
    failed_verifications_24h = len(verification_logs_24h) - len(successful_24h)

    # Calculate daily verifications for the last 7 days
    daily_stats = {}
    for i in range(7):
        date_key = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_stats[date_key] = 0
    
    # Populate counts from logs
    for log in recent_logs:
        if log.get('action') in verification_actions and log.get('entity_type') in verification_types:
            log_date = log.get('timestamp').strftime('%Y-%m-%d')
            if log_date in daily_stats:
                daily_stats[log_date] += 1
    
    # Convert to list sorted by date (oldest to newest)
    daily_verifications = [
        {"date": date, "count": count} 
        for date, count in sorted(daily_stats.items())
    ]
    
    # Calculate overall success rate from ALL logs (all-time)
    all_verification_logs = [
        log for log in all_logs
        if log.get('action') in verification_actions
        and log.get('entity_type') in verification_types
    ]
    
    if all_verification_logs:
        all_successful = [log for log in all_verification_logs if log.get('success', False)]
        success_rate = len(all_successful) / len(all_verification_logs)
        total_verifications_count = len(all_verification_logs)
    else:
        success_rate = 0.0
        total_verifications_count = 0
    
    # Count active users in last 24h (users who performed any action)
    active_user_ids = {log.get('actor') for log in recent_logs if log.get('actor')}
    active_users_24h = len(active_user_ids)
    
    return SystemStats(
        total_users=total_users,
        total_enrollments=total_enrollments,
        total_verifications=total_verifications_count,
        success_rate=success_rate,
        active_users_24h=active_users_24h,
        failed_verifications_24h=failed_verifications_24h,
        daily_verifications=daily_verifications
    )

@admin_router.get("/activity", response_model=List[ActivityLog])
async def get_recent_activity(
    limit: int = 100,
    action: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository)
):
    """
    Get recent activity logs (admin only).
    Admins see only logs from their company, superadmin sees all.
    """
    try:
        # Get logs from repository
        logs = await audit_repo.get_logs(
            action=action,
            limit=limit * 10  # Get more to filter by company
        )
        
        # If admin (not superadmin), filter by company
        if current_user["role"] == "admin":
            # Get all users from the admin's company
            company_users, _ = await user_repo.get_users_by_company(
                current_user["company"], 
                page=1, 
                limit=10000
            )
            company_user_ids = {str(u["id"]) for u in company_users}
            company_user_emails = {str(u.get("email", "")).lower() for u in company_users}
            
            # Filter logs to only include actors/entities from this company
            filtered_logs = []
            for log in logs:
                actor = str(log.get('actor', ''))
                entity_id = str(log.get('entity_id', ''))
                metadata = log.get('metadata') or {}
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                metadata_user_id = str(metadata.get('user_id', ''))
                
                # Check if any identifier matches a company user
                is_company_log = (
                    actor in company_user_ids or
                    actor.lower() in company_user_emails or
                    entity_id in company_user_ids or
                    metadata_user_id in company_user_ids
                )
                
                if is_company_log:
                    filtered_logs.append(log)
                    if len(filtered_logs) >= limit:
                        break
            logs = filtered_logs
        else:
            # Superadmin sees all logs, just limit
            logs = logs[:limit]
        
        # Transform to ActivityLog model using helper function
        default_timestamp = datetime.now(timezone.utc)
        activity_logs = [
            ActivityLog(**_transform_log_to_activity(log, default_timestamp))
            for log in logs
        ]
        
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
                    parsed_value = json.loads(rule_value)
                    # If it's a dict with 'value' key, extract it
                    if isinstance(parsed_value, dict) and 'value' in parsed_value:
                        rule_value = float(parsed_value['value'])
                    else:
                        rule_value = float(parsed_value)
                except json.JSONDecodeError:
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


# =====================================================
# Notifications / Alerts
# =====================================================

class AlertNotification(BaseModel):
    """Alert notification for admin."""
    id: str
    type: str  # 'warning', 'error', 'info'
    title: str
    message: str
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    is_read: bool = False


@admin_router.get("/notifications", response_model=List[AlertNotification])
async def get_notifications(
    limit: int = 20,
    current_user: dict = Depends(require_admin),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository)
):
    """
    Get notifications/alerts for admin dashboard.
    Shows failed verifications, suspicious activity, etc.
    """
    from datetime import timezone
    
    try:
        notifications = []
        
        # Get company users if admin
        company_user_ids = set()
        if current_user["role"] == "admin":
            company_users, _ = await user_repo.get_users_by_company(
                current_user["company"], page=1, limit=10000
            )
            company_user_ids = {str(u["id"]) for u in company_users}
        
        # Get recent logs with failures or suspicious activity
        logs = await audit_repo.get_logs(limit=500)
        
        for log in logs:
            # Filter by company if admin
            if current_user["role"] == "admin":
                actor = log.get('actor', '')
                if actor not in company_user_ids:
                    continue
            
            action = log.get('action', '')
            success = log.get('success', True)
            metadata = log.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Failed verifications
            if action in ['VERIFICATION', 'VERIFY', 'multi_verification_complete'] and not success:
                notifications.append(AlertNotification(
                    id=str(log.get('id', '')),
                    type='warning',
                    title='Verificación Fallida',
                    message=f"Usuario no pudo verificarse. Razón: {metadata.get('reason', 'Desconocida')}",
                    timestamp=log.get('timestamp', datetime.now(timezone.utc)),
                    user_id=log.get('actor'),
                    user_email=metadata.get('email'),
                    is_read=False
                ))
            
            # Failed logins
            if action == 'LOGIN' and not success:
                notifications.append(AlertNotification(
                    id=str(log.get('id', '')),
                    type='error',
                    title='Login Fallido',
                    message=f"Intento de login fallido desde {metadata.get('ip_address', 'IP desconocida')}",
                    timestamp=log.get('timestamp', datetime.now(timezone.utc)),
                    user_email=metadata.get('email'),
                    is_read=False
                ))
            
            # Suspicious activity (spoof detected)
            if metadata.get('spoof_probability', 0) > 0.7:
                notifications.append(AlertNotification(
                    id=str(log.get('id', '')) + '_spoof',
                    type='error',
                    title='Posible Suplantación',
                    message=f"Probabilidad de spoofing detectada: {metadata.get('spoof_probability', 0):.0%}",
                    timestamp=log.get('timestamp', datetime.now(timezone.utc)),
                    user_id=log.get('actor'),
                    is_read=False
                ))
            
            if len(notifications) >= limit:
                break
        
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)[:limit]
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []


# =====================================================
# Reset Voiceprint
# =====================================================

@admin_router.post("/users/{user_id}/reset-voiceprint")
async def reset_user_voiceprint(
    user_id: str,
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    voice_repo: VoiceSignatureRepositoryPort = Depends(get_voice_signature_repository),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository)
):
    """
    Reset a user's voiceprint, allowing them to re-enroll.
    """
    try:
        from uuid import UUID
        
        # Verify user exists and belongs to company
        user = await user_repo.find_by_id(UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Admin can only reset users from their company
        if current_user["role"] == "admin" and user.get("company") != current_user["company"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot reset voiceprint for user from another company"
            )
        
        # Delete the voiceprint
        await voice_repo.delete_by_user_id(UUID(user_id))
        
        # Update user enrollment status
        await user_repo.update(UUID(user_id), {"enrollment_status": "not_started"})
        
        # Log the action
        await audit_repo.log_event(
            actor=str(current_user["id"]),
            action="RESET_VOICEPRINT",
            entity_type="user",
            entity_id=user_id,
            metadata={
                "reset_by": current_user["email"],
                "user_email": user.get("email")
            }
        )
        
        logger.info(f"Voiceprint reset for user {user_id} by {current_user['email']}")
        
        return {
            "success": True,
            "message": f"Voiceprint eliminado exitosamente. El usuario puede volver a registrar su voz."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting voiceprint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset voiceprint: {str(e)}"
        )


# =====================================================
# Chart Data - Detailed verification history
# =====================================================

class ChartDataPoint(BaseModel):
    """Data point for charts."""
    date: str
    verifications: int
    successful: int
    failed: int


@admin_router.get("/stats/chart-data", response_model=List[ChartDataPoint])
async def get_chart_data(
    days: int = 30,
    current_user: dict = Depends(require_admin),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository)
):
    """
    Get detailed chart data for verification trends.
    """
    from datetime import timezone
    from collections import defaultdict
    
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get company users if admin
        company_user_ids = set()
        if current_user["role"] == "admin":
            company_users, _ = await user_repo.get_users_by_company(
                current_user["company"], page=1, limit=10000
            )
            company_user_ids = {str(u["id"]) for u in company_users}
        
        # Get logs
        logs = await audit_repo.get_logs(limit=5000)
        
        # Aggregate by date
        daily_stats = defaultdict(lambda: {"verifications": 0, "successful": 0, "failed": 0})
        verification_actions = {'VERIFICATION', 'VERIFY', 'multi_verification_complete'}
        
        for log in logs:
            action = log.get('action', '')
            if action not in verification_actions:
                continue
            
            # Filter by company if admin
            if current_user["role"] == "admin":
                actor = log.get('actor', '')
                if actor not in company_user_ids:
                    continue
            
            timestamp = log.get('timestamp')
            if not timestamp or timestamp < start_date:
                continue
            
            date_str = timestamp.strftime('%Y-%m-%d')
            daily_stats[date_str]["verifications"] += 1
            
            if log.get('success', False):
                daily_stats[date_str]["successful"] += 1
            else:
                daily_stats[date_str]["failed"] += 1
        
        # Fill in missing dates
        result = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            stats = daily_stats.get(date_str, {"verifications": 0, "successful": 0, "failed": 0})
            result.append(ChartDataPoint(
                date=date_str,
                verifications=stats["verifications"],
                successful=stats["successful"],
                failed=stats["failed"]
            ))
            current += timedelta(days=1)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return []


# =====================================================
# Export Report
# =====================================================

@admin_router.get("/export/users")
async def export_users_csv(
    current_user: dict = Depends(require_admin),
    user_repo: UserRepositoryPort = Depends(get_user_repository)
):
    """
    Export users data as CSV.
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    try:
        # Get users
        if current_user["role"] == "superadmin":
            users, _ = await user_repo.list_all(page=1, limit=10000)
        else:
            users, _ = await user_repo.get_users_by_company(
                current_user["company"], page=1, limit=10000
            )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Email', 'Nombre', 'Apellido', 'Empresa', 
            'Rol', 'Estado', 'Estado Enrollment', 'Fecha Registro', 'Último Login'
        ])
        
        # Data
        for user in users:
            writer.writerow([
                str(user.get('id', '')),
                user.get('email', ''),
                user.get('first_name', ''),
                user.get('last_name', ''),
                user.get('company', ''),
                user.get('role', ''),
                user.get('status', ''),
                user.get('enrollment_status', ''),
                str(user.get('created_at', ''))[:10],
                str(user.get('last_login', ''))[:10] if user.get('last_login') else ''
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=usuarios_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export users: {str(e)}"
        )


@admin_router.get("/export/activity")
async def export_activity_csv(
    days: int = 30,
    current_user: dict = Depends(require_admin),
    audit_repo: AuditLogRepositoryPort = Depends(get_audit_log_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository)
):
    """
    Export activity logs as CSV.
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    try:
        # Get logs
        logs = await audit_repo.get_logs(limit=5000)
        
        # Filter by company if admin
        company_user_ids = set()
        if current_user["role"] == "admin":
            company_users, _ = await user_repo.get_users_by_company(
                current_user["company"], page=1, limit=10000
            )
            company_user_ids = {str(u["id"]) for u in company_users}
            logs = [l for l in logs if l.get('actor', '') in company_user_ids]
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Fecha', 'Hora', 'Actor', 'Acción', 'Tipo Entidad', 
            'ID Entidad', 'Éxito', 'Detalles'
        ])
        
        # Data
        for log in logs:
            timestamp = log.get('timestamp', datetime.now())
            metadata = log.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            writer.writerow([
                timestamp.strftime('%Y-%m-%d'),
                timestamp.strftime('%H:%M:%S'),
                log.get('actor', ''),
                log.get('action', ''),
                log.get('entity_type', ''),
                log.get('entity_id', ''),
                'Sí' if log.get('success', True) else 'No',
                str(metadata.get('message', ''))[:100]
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=actividad_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export activity: {str(e)}"
        )