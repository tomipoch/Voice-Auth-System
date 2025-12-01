"""PostgreSQL implementation of audit log repository."""

import json
import asyncpg
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from ...domain.repositories.AuditLogRepositoryPort import AuditLogRepositoryPort
from ...shared.types.common_types import AuditAction


def convert_to_json_serializable(obj: Any) -> Any:
    """Convert numpy types and other non-JSON-serializable types to native Python types."""
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


class PostgresAuditLogRepository(AuditLogRepositoryPort):
    """PostgreSQL implementation of audit log repository."""
    
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
    
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
        query = """
        INSERT INTO audit_log (actor, action, entity_type, entity_id, success, metadata, error_message)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        # Convert numpy types to native Python types
        if metadata:
            metadata = convert_to_json_serializable(metadata)
        
        # Ensure success is a native Python bool, not numpy bool
        success = bool(success)
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                query,
                actor,
                action.value if isinstance(action, AuditAction) else action,
                entity_type,
                entity_id,
                success,
                json.dumps(metadata) if metadata else None,
                error_message
            )
    
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
        conditions = []
        params = []
        param_count = 1
        
        if actor:
            conditions.append(f"actor = ${param_count}")
            params.append(actor)
            param_count += 1
        
        if action:
            conditions.append(f"action = ${param_count}")
            params.append(action.value if isinstance(action, AuditAction) else action)
            param_count += 1
        
        if entity_type:
            conditions.append(f"entity_type = ${param_count}")
            params.append(entity_type)
            param_count += 1
        
        if entity_id:
            conditions.append(f"entity_id = ${param_count}")
            params.append(entity_id)
            param_count += 1
        
        if start_time:
            conditions.append(f"timestamp >= ${param_count}")
            params.append(start_time)
            param_count += 1
        
        if end_time:
            conditions.append(f"timestamp <= ${param_count}")
            params.append(end_time)
            param_count += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
        SELECT id, actor, action, entity_type, entity_id, success, metadata, error_message, timestamp
        FROM audit_log
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ${param_count}
        """
        params.append(limit)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_user_activity(
        self,
        user_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user."""
        from datetime import timezone
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = """
        SELECT id, actor, action, entity_type, entity_id, success, metadata, error_message, timestamp
        FROM audit_log
        WHERE (actor = $1 OR entity_id = $1 OR metadata->>'user_id' = $1)
          AND timestamp >= $2
        ORDER BY timestamp DESC
        LIMIT $3
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, since, limit)
            return [dict(row) for row in rows]
    async def get_client_activity(
        self,
        client_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific client."""
        from datetime import timezone
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = """
        SELECT id, actor, action, entity_type, entity_id, success, metadata, error_message, timestamp
        FROM audit_log
        WHERE (metadata->>'client_id' = $1)
          AND timestamp >= $2
        ORDER BY timestamp DESC
        LIMIT $3
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, client_id, since, limit)
            return [dict(row) for row in rows]
