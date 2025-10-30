"""Unit tests for Strategy Pattern in policy decisions."""

import pytest
from unittest.mock import Mock

from ...src.domain.services.DecisionService import (
    DecisionService,
    StandardDecisionStrategy,
    BankingDecisionStrategy,
    DemoDecisionStrategy
)
from ...src.domain.model.AuthAttemptResult import BiometricScores
from ...src.domain.model.ThresholdPolicy import PolicyTemplates
from ...src.shared.types.common_types import AuthReason


class TestDecisionStrategies:
    """Test suite for decision strategy implementations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.standard_policy = PolicyTemplates.get_standard()
        self.banking_policy = PolicyTemplates.get_bank_strict()
        self.demo_policy = PolicyTemplates.get_demo_relaxed()
    
    def test_standard_strategy_accepts_good_scores(self):
        """Test standard strategy accepts high-quality biometric scores."""
        strategy = StandardDecisionStrategy()
        scores = BiometricScores(
            similarity=0.90,
            spoof_probability=0.1,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        accept, reason = strategy.decide(scores, self.standard_policy)
        
        assert accept is True
        assert reason == AuthReason.OK
    
    def test_standard_strategy_rejects_low_similarity(self):
        """Test standard strategy rejects low similarity scores."""
        strategy = StandardDecisionStrategy()
        scores = BiometricScores(
            similarity=0.50,  # Below threshold
            spoof_probability=0.1,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        accept, reason = strategy.decide(scores, self.standard_policy)
        
        assert accept is False
        assert reason == AuthReason.LOW_SIMILARITY
    
    def test_standard_strategy_rejects_spoofing(self):
        """Test standard strategy rejects spoofed audio."""
        strategy = StandardDecisionStrategy()
        scores = BiometricScores(
            similarity=0.90,
            spoof_probability=0.8,  # High spoof probability
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        accept, reason = strategy.decide(scores, self.standard_policy)
        
        assert accept is False
        assert reason == AuthReason.SPOOF
    
    def test_banking_strategy_more_strict(self):
        """Test banking strategy is more strict than standard."""
        banking_strategy = BankingDecisionStrategy()
        scores = BiometricScores(
            similarity=0.86,  # Above standard but might fail banking
            spoof_probability=0.15,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        accept, reason = banking_strategy.decide(scores, self.banking_policy)
        
        # Banking strategy should be more strict
        assert accept is False
        assert reason == AuthReason.LOW_SIMILARITY
    
    def test_demo_strategy_more_relaxed(self):
        """Test demo strategy is more relaxed."""
        demo_strategy = DemoDecisionStrategy()
        scores = BiometricScores(
            similarity=0.65,  # Low similarity
            spoof_probability=0.4,
            phrase_match=0.55,
            phrase_ok=True,
            inference_latency_ms=5000
        )
        
        accept, reason = demo_strategy.decide(scores, self.demo_policy)
        
        # Demo strategy should be more relaxed
        assert accept is True
        assert reason == AuthReason.OK
    
    def test_decision_service_strategy_selection(self):
        """Test decision service selects appropriate strategy."""
        decision_service = DecisionService()
        
        scores = BiometricScores(
            similarity=0.90,
            spoof_probability=0.1,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        # Test automatic strategy selection based on policy name
        banking_policy = PolicyTemplates.get_bank_strict()
        accept, reason = decision_service.decide(scores, banking_policy)
        
        assert isinstance(accept, bool)
        assert isinstance(reason, AuthReason)
    
    def test_decision_service_custom_strategy(self):
        """Test decision service with custom strategy."""
        decision_service = DecisionService()
        
        # Register custom strategy
        custom_strategy = Mock()
        custom_strategy.decide.return_value = (True, AuthReason.OK)
        decision_service.register_strategy("custom", custom_strategy)
        
        scores = BiometricScores(
            similarity=0.90,
            spoof_probability=0.1,
            phrase_match=0.85,
            phrase_ok=True,
            inference_latency_ms=2000
        )
        
        accept, reason = decision_service.decide(
            scores, 
            self.standard_policy, 
            strategy_name="custom"
        )
        
        assert accept is True
        assert reason == AuthReason.OK
        custom_strategy.decide.assert_called_once()