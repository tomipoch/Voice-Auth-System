"""Service for managing phrase quality rules."""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ..domain.repositories.PhraseQualityRulesRepositoryPort import PhraseQualityRulesRepositoryPort

logger = logging.getLogger(__name__)


class PhraseQualityRulesService:
    """Service for managing configurable phrase quality rules."""
    
    def __init__(self, rules_repo: PhraseQualityRulesRepositoryPort):
        self._rules_repo = rules_repo
        # Cache for frequently accessed rules
        self._cache: Dict[str, float] = {}
    
    async def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule with all its metadata."""
        return await self._rules_repo.get_rule(rule_name)
    
    async def get_all_rules(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all rules, optionally including inactive ones."""
        return await self._rules_repo.get_all_rules(is_active=not include_inactive)
    
    async def get_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """Get all rules of a specific type (threshold, rate_limit, cleanup)."""
        if rule_type not in ['threshold', 'rate_limit', 'cleanup']:
            raise ValueError(f"Invalid rule_type: {rule_type}. Must be 'threshold', 'rate_limit', or 'cleanup'")
        
        return await self._rules_repo.get_rules_by_type(rule_type)
    
    async def update_rule(
        self, 
        rule_name: str, 
        new_value: float,
        admin_id: Optional[UUID] = None
    ) -> bool:
        """
        Update a rule's value (admin only).
        
        Args:
            rule_name: Name of the rule to update
            new_value: New numeric value
            admin_id: UUID of the admin making the change
            
        Returns:
            True if successful, False otherwise
        """
        # Validate the new value
        if new_value < 0:
            raise ValueError(f"Rule value cannot be negative: {new_value}")
        
        # Specific validations per rule
        if rule_name in ['min_success_rate', 'min_asr_score', 'min_phrase_ok_rate']:
            if not (0.0 <= new_value <= 1.0):
                raise ValueError(f"Percentage values must be between 0.0 and 1.0, got: {new_value}")
        
        success = await self._rules_repo.update_rule(rule_name, new_value, admin_id)
        
        if success:
            # Invalidate cache for this rule
            self._cache.pop(rule_name, None)
            logger.info(f"Rule '{rule_name}' updated to {new_value} by admin {admin_id}")
        
        return success
    
    async def toggle_rule(self, rule_name: str, is_active: bool) -> bool:
        """Enable or disable a rule."""
        success = await self._rules_repo.toggle_rule(rule_name, is_active)
        
        if success:
            self._cache.pop(rule_name, None)
        
        return success
    
    async def get_rule_value(self, rule_name: str, default: float = 0.0) -> float:
        """
        Get just the numeric value of a rule.
        Uses cache for performance.
        
        Args:
            rule_name: Name of the rule
            default: Default value if rule not found
            
        Returns:
            The rule's numeric value
        """
        # Check cache first
        if rule_name in self._cache:
            return self._cache[rule_name]
        
        # Fetch from repository
        value = await self._rules_repo.get_rule_value(rule_name, default)
        
        # Cache it
        self._cache[rule_name] = value
        
        return value
    
    async def get_threshold_rules(self) -> Dict[str, float]:
        """Get all threshold rules as a dictionary of name: value."""
        rules = await self.get_rules_by_type('threshold')
        return {
            rule['rule_name']: float(rule['rule_value']['value'])
            for rule in rules
        }
    
    async def get_rate_limit_rules(self) -> Dict[str, int]:
        """Get all rate limit rules as a dictionary of name: value."""
        rules = await self.get_rules_by_type('rate_limit')
        return {
            rule['rule_name']: int(rule['rule_value']['value'])
            for rule in rules
        }
    
    async def get_cleanup_rules(self) -> Dict[str, int]:
        """Get all cleanup rules as a dictionary of name: value."""
        rules = await self.get_rules_by_type('cleanup')
        return {
            rule['rule_name']: int(rule['rule_value']['value'])
            for rule in rules
        }
    
    def clear_cache(self):
        """Clear the rules cache. Useful after bulk updates."""
        self._cache.clear()
        logger.info("Rules cache cleared")
