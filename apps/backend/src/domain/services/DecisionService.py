"""Decision service using Strategy Pattern for different risk policies."""

from abc import ABC, abstractmethod
from typing import Optional

from ..model.AuthAttemptResult import BiometricScores
from ..model.ThresholdPolicy import ThresholdPolicy
from ...shared.types.common_types import AuthReason


class DecisionStrategy(ABC):
    """Abstract strategy for making authentication decisions."""
    
    @abstractmethod
    def decide(
        self,
        scores: BiometricScores,
        policy: ThresholdPolicy,
        context: Optional[dict] = None
    ) -> tuple[bool, AuthReason]:
        """
        Make an authentication decision based on scores and policy.
        
        Returns:
            tuple: (accept: bool, reason: AuthReason)
        """
        pass


class StandardDecisionStrategy(DecisionStrategy):
    """Standard decision strategy with simple threshold checks."""
    
    def decide(
        self,
        scores: BiometricScores,
        policy: ThresholdPolicy,
        context: Optional[dict] = None
    ) -> tuple[bool, AuthReason]:
        """Apply standard decision logic."""
        
        # Check for spoofing first (highest priority)
        if scores.spoof_probability > policy.spoof_threshold:
            return False, AuthReason.SPOOF
        
        # Check phrase correctness
        if not scores.phrase_ok:
            return False, AuthReason.BAD_PHRASE
        
        # Check similarity threshold
        if scores.similarity < policy.similarity_threshold:
            return False, AuthReason.LOW_SIMILARITY
        
        # Check phrase match quality
        if scores.phrase_match < policy.phrase_match_threshold:
            return False, AuthReason.BAD_PHRASE
        
        # All checks passed
        return True, AuthReason.OK


class BankingDecisionStrategy(DecisionStrategy):
    """Enhanced decision strategy for banking with additional security checks."""
    
    def decide(
        self,
        scores: BiometricScores,
        policy: ThresholdPolicy,
        context: Optional[dict] = None
    ) -> tuple[bool, AuthReason]:
        """Apply banking-specific decision logic with additional checks."""
        
        # First apply standard checks
        standard_strategy = StandardDecisionStrategy()
        accept, reason = standard_strategy.decide(scores, policy, context)
        
        if not accept:
            return accept, reason
        
        # Additional banking-specific checks
        context = context or {}
        
        # Check for recent failed attempts (if provided in context)
        recent_failures = context.get('recent_failures', 0)
        if recent_failures >= 3:
            return False, AuthReason.ERROR  # Too many recent failures
        
        # More strict similarity requirement for banking
        banking_similarity_boost = 0.05
        if scores.similarity < (policy.similarity_threshold + banking_similarity_boost):
            return False, AuthReason.LOW_SIMILARITY
        
        # Check inference latency (potential system compromise indicator)
        if scores.inference_latency_ms > policy.max_inference_latency_ms:
            return False, AuthReason.ERROR
        
        # Extra spoofing vigilance - lower threshold
        banking_spoof_reduction = 0.1
        if scores.spoof_probability > (policy.spoof_threshold - banking_spoof_reduction):
            return False, AuthReason.SPOOF
        
        return True, AuthReason.OK


class DemoDecisionStrategy(DecisionStrategy):
    """Relaxed decision strategy for demos and testing."""
    
    def decide(
        self,
        scores: BiometricScores,
        policy: ThresholdPolicy,
        context: Optional[dict] = None
    ) -> tuple[bool, AuthReason]:
        """Apply relaxed decision logic for demos."""
        
        # Very basic checks for demo purposes
        if scores.spoof_probability > 0.8:  # Only reject obvious spoofing
            return False, AuthReason.SPOOF
        
        if scores.similarity < 0.6:  # Very low threshold
            return False, AuthReason.LOW_SIMILARITY
        
        # Don't be too strict about phrase matching in demos
        if scores.phrase_match < 0.5:
            return False, AuthReason.BAD_PHRASE
        
        return True, AuthReason.OK


class DecisionService:
    """Service that uses Strategy Pattern to make authentication decisions."""
    
    def __init__(self):
        self._strategies = {
            'standard': StandardDecisionStrategy(),
            'banking': BankingDecisionStrategy(),
            'demo': DemoDecisionStrategy(),
        }
        self._default_strategy = 'standard'
    
    def register_strategy(self, name: str, strategy: DecisionStrategy):
        """Register a new decision strategy."""
        self._strategies[name] = strategy
    
    def decide(
        self,
        scores: BiometricScores,
        policy: ThresholdPolicy,
        strategy_name: Optional[str] = None,
        context: Optional[dict] = None
    ) -> tuple[bool, AuthReason]:
        """
        Make an authentication decision using the specified strategy.
        
        Args:
            scores: Biometric analysis scores
            policy: Threshold policy to apply
            strategy_name: Name of strategy to use (defaults to policy-based selection)
            context: Additional context for decision making
            
        Returns:
            tuple: (accept: bool, reason: AuthReason)
        """
        # Auto-select strategy based on policy if not specified
        if strategy_name is None:
            strategy_name = self._select_strategy_for_policy(policy)
        
        strategy = self._strategies.get(strategy_name, self._strategies[self._default_strategy])
        return strategy.decide(scores, policy, context)
    
    def _select_strategy_for_policy(self, policy: ThresholdPolicy) -> str:
        """Auto-select appropriate strategy based on policy name."""
        if 'bank' in policy.name.lower():
            return 'banking'
        elif 'demo' in policy.name.lower() or 'test' in policy.name.lower():
            return 'demo'
        else:
            return 'standard'