"""PostgreSQL implementation of PhraseQualityRulesRepositoryPort."""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ...domain.repositories.PhraseQualityRulesRepositoryPort import PhraseQualityRulesRepositoryPort

logger = logging.getLogger(__name__)


class PostgresPhraseQualityRulesRepository(PhraseQualityRulesRepositoryPort):
    """PostgreSQL implementation of phrase quality rules repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule by name."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, rule_name, rule_type, rule_value, is_active, 
                       created_at, updated_at, created_by
                FROM phrase_quality_rules
                WHERE rule_name = $1
                """,
                rule_name
            )
            
            if row:
                return dict(row)
            return None
    
    async def get_all_rules(self, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get all rules, optionally filtered by active status."""
        async with self._pool.acquire() as conn:
            if is_active:
                rows = await conn.fetch(
                    """
                    SELECT id, rule_name, rule_type, rule_value, is_active,
                           created_at, updated_at, created_by
                    FROM phrase_quality_rules
                    WHERE is_active = TRUE
                    ORDER BY rule_type, rule_name
                    """
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, rule_name, rule_type, rule_value, is_active,
                           created_at, updated_at, created_by
                    FROM phrase_quality_rules
                    ORDER BY rule_type, rule_name
                    """
                )
            
            return [dict(row) for row in rows]
    
    async def get_rules_by_type(self, rule_type: str, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get all rules of a specific type."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, rule_name, rule_type, rule_value, is_active,
                       created_at, updated_at, created_by
                FROM phrase_quality_rules
                WHERE rule_type = $1 AND ($2 = FALSE OR is_active = TRUE)
                ORDER BY rule_name
                """,
                rule_type,
                is_active
            )
            
            return [dict(row) for row in rows]
    
    async def update_rule(
        self, 
        rule_name: str, 
        new_value: float,
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update a rule's value. Returns True if successful."""
        async with self._pool.acquire() as conn:
            # Check if rule exists
            current_rule = await self.get_rule(rule_name)
            if not current_rule:
                logger.warning(f"Rule '{rule_name}' not found")
                return False
            
            # Update the numeric value directly
            result = await conn.execute(
                """
                UPDATE phrase_quality_rules
                SET rule_value = $1,
                    updated_at = now()
                WHERE rule_name = $2
                """,
                new_value,
                rule_name
            )
            
            # Log the update
            logger.info(f"Rule '{rule_name}' updated to {new_value} by {updated_by or 'system'}")
            
            return result == "UPDATE 1"

    
    async def toggle_rule(self, rule_name: str, is_active: bool) -> bool:
        """Enable or disable a rule. Returns True if successful."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE phrase_quality_rules
                SET is_active = $1,
                    updated_at = now()
                WHERE rule_name = $2
                """,
                is_active,
                rule_name
            )
            
            logger.info(f"Rule '{rule_name}' {'enabled' if is_active else 'disabled'}")
            
            return result == "UPDATE 1"
    
    async def get_rule_value(self, rule_name: str, default: float = 0.0) -> float:
        """Get just the numeric value of a rule, with a default fallback."""
        rule = await self.get_rule(rule_name)
        
        if not rule or not rule.get('is_active'):
            logger.warning(f"Rule '{rule_name}' not found or inactive, using default: {default}")
            return default
        
        try:
            # rule_value is already a numeric value, not a dict
            value = rule['rule_value']
            return float(value)
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing rule value for '{rule_name}': {e}, using default: {default}")
            return default

