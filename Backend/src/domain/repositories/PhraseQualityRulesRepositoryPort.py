"""Repository port for phrase quality rules."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID


class PhraseQualityRulesRepositoryPort(ABC):
    """Repository interface for phrase quality rules."""
    
    @abstractmethod
    async def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule by name."""
        pass
    
    @abstractmethod
    async def get_all_rules(self, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get all rules, optionally filtered by active status."""
        pass
    
    @abstractmethod
    async def get_rules_by_type(self, rule_type: str, is_active: bool = True) -> List[Dict[str, Any]]:
        """Get all rules of a specific type."""
        pass
    
    @abstractmethod
    async def update_rule(
        self, 
        rule_name: str, 
        new_value: float,
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update a rule's value. Returns True if successful."""
        pass
    
    @abstractmethod
    async def toggle_rule(self, rule_name: str, is_active: bool) -> bool:
        """Enable or disable a rule. Returns True if successful."""
        pass
    
    @abstractmethod
    async def get_rule_value(self, rule_name: str, default: float = 0.0) -> float:
        """Get just the numeric value of a rule, with a default fallback."""
        pass
