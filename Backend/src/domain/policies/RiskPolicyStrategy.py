"""Risk policy strategies using Strategy Pattern."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..model.ThresholdPolicy import ThresholdPolicy, PolicyTemplates
from ...shared.types.common_types import RiskLevel, UserId, ClientId


class RiskPolicyStrategy(ABC):
    """Abstract strategy for selecting risk policies."""
    
    @abstractmethod
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdPolicy:
        """Select appropriate policy based on context."""
        pass


class DefaultRiskPolicyStrategy(RiskPolicyStrategy):
    """Default policy selection strategy."""
    
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdPolicy:
        """Return standard policy by default."""
        return PolicyTemplates.get_standard()


class ClientBasedRiskPolicyStrategy(RiskPolicyStrategy):
    """Policy selection based on client configuration."""
    
    def __init__(self):
        self._client_policies = {
            # Example client policy mappings
            # In real implementation, this would come from database
        }
    
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdPolicy:
        """Select policy based on client requirements."""
        if client_id and client_id in self._client_policies:
            return self._client_policies[client_id]
        
        # Check context for client hints
        if context:
            client_type = context.get('client_type', '')
            if 'bank' in client_type.lower():
                return PolicyTemplates.get_bank_strict()
            elif 'demo' in client_type.lower():
                return PolicyTemplates.get_demo_relaxed()
        
        return PolicyTemplates.get_standard()


class AdaptiveRiskPolicyStrategy(RiskPolicyStrategy):
    """Adaptive policy selection based on user history and context."""
    
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdPolicy:
        """Select policy adaptively based on multiple factors."""
        context = context or {}
        
        # Start with default
        base_policy = PolicyTemplates.get_standard()
        
        # Analyze context for risk factors
        risk_score = self._calculate_risk_score(context)
        
        if risk_score >= 0.8:
            # High risk - use strict policy
            return PolicyTemplates.get_bank_strict()
        elif risk_score <= 0.3:
            # Low risk - can use relaxed policy
            return PolicyTemplates.get_demo_relaxed()
        else:
            # Medium risk - use standard policy
            return base_policy
    
    def _calculate_risk_score(self, context: Dict[str, Any]) -> float:
        """Calculate risk score based on context factors."""
        risk_score = 0.5  # Base risk
        
        # Time-based factors
        hour = context.get('hour_of_day', 12)
        if hour < 6 or hour > 22:  # Night hours
            risk_score += 0.1
        
        # Location factors (if available)
        is_known_location = context.get('known_location', True)
        if not is_known_location:
            risk_score += 0.2
        
        # Recent failure history
        recent_failures = context.get('recent_failures', 0)
        risk_score += min(recent_failures * 0.1, 0.3)
        
        # Device factors
        is_known_device = context.get('known_device', True)
        if not is_known_device:
            risk_score += 0.15
        
        return min(max(risk_score, 0.0), 1.0)  # Clamp to [0, 1]


class TimeBasedRiskPolicyStrategy(RiskPolicyStrategy):
    """Policy selection based on time of day and day of week."""
    
    def select_policy(
        self,
        user_id: Optional[UserId] = None,
        client_id: Optional[ClientId] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ThresholdPolicy:
        """Select policy based on temporal factors."""
        context = context or {}
        
        hour = context.get('hour_of_day', 12)
        day_of_week = context.get('day_of_week', 1)
        
        # Business hours: more relaxed
        if 9 <= hour <= 17 and 1 <= day_of_week <= 5:
            return PolicyTemplates.get_standard()
        
        # Night hours or weekends: more strict
        elif hour < 6 or hour > 22 or day_of_week > 5:
            return PolicyTemplates.get_bank_strict()
        
        # Other hours: standard
        else:
            return PolicyTemplates.get_standard()