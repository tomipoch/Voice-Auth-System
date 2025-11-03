"""Policy selector for choosing appropriate risk policies."""

from typing import Optional, Dict, Any

from ...domain.policies.RiskPolicyStrategy import (
    RiskPolicyStrategy,
    DefaultRiskPolicyStrategy,
    ClientBasedRiskPolicyStrategy,
    AdaptiveRiskPolicyStrategy,
    TimeBasedRiskPolicyStrategy
)
from ...domain.model.ThresholdPolicy import ThresholdPolicy
from ...shared.types.common_types import UserId, ClientId


class PolicySelector:
    """Selects appropriate policies using Strategy Pattern."""
    
    def __init__(self):
        self._strategies = {
            'default': DefaultRiskPolicyStrategy(),
            'client_based': ClientBasedRiskPolicyStrategy(),
            'adaptive': AdaptiveRiskPolicyStrategy(),
            'time_based': TimeBasedRiskPolicyStrategy(),
        }
        self._default_strategy = 'adaptive'
    
    def register_strategy(self, name: str, strategy: RiskPolicyStrategy):
        """Register a new policy selection strategy."""
        self._strategies[name] = strategy
    
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None,
        strategy_name: Optional[str] = None
    ) -> ThresholdPolicy:
        """
        Select appropriate policy for the given context.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            context: Additional context for policy selection
            strategy_name: Specific strategy to use (optional)
            
        Returns:
            Selected threshold policy
        """
        # Use specified strategy or default
        strategy_name = strategy_name or self._default_strategy
        strategy = self._strategies.get(strategy_name, self._strategies[self._default_strategy])
        
        return strategy.select_policy(user_id, client_id, context)
    
    def get_available_strategies(self) -> list[str]:
        """Get list of available strategy names."""
        return list(self._strategies.keys())