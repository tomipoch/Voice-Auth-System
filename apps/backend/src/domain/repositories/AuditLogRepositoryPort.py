"""Audit log repository port (interface)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any

from ...shared.types.common_types import AuditAction


class AuditLogRepositoryPort(ABC):
    """Repository interface for audit logging."""
    
    @abstractmethod
    async def log_event(
        self,
        actor: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log an audit event."""
        pass
    
    @abstractmethod
    async def get_logs(
        self,
        actor: Optional[str] = None,
        action: Optional[AuditAction] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters."""
        pass
    
    @abstractmethod
    async def get_user_activity(
        self,
        user_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user."""
        pass
    
    @abstractmethod
    async def get_client_activity(
        self,
        client_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific client."""
        pass