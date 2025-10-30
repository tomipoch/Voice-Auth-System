"""Unit tests for Builder Pattern implementation."""

import pytest
from uuid import uuid4

from ...src.domain.services.ResultBuilder import ResultBuilder
from ...src.domain.model.AuthAttemptResult import BiometricScores
from ...src.shared.types.common_types import AuthReason


class TestResultBuilder:
    """Test suite for ResultBuilder class."""
    
    def test_builder_creates_valid_result(self):
        """Test that builder can create a valid authentication result."""
        user_id = uuid4()
        client_id = uuid4()
        
        result = (ResultBuilder()
                  .with_user(user_id)
                  .with_client(client_id)
                  .with_biometric_scores(
                      similarity=0.95,
                      spoof_probability=0.1,
                      phrase_match=0.9,
                      phrase_ok=True,
                      inference_latency_ms=1500
                  )
                  .accept_with_reason(AuthReason.OK)
                  .build())
        
        assert result.user_id == user_id
        assert result.client_id == client_id
        assert result.decided is True
        assert result.accept is True
        assert result.reason == AuthReason.OK
        assert result.scores.similarity == pytest.approx(0.95)
        assert result.scores.spoof_probability == pytest.approx(0.1)
        assert result.is_successful() is True
    
    def test_builder_rejects_authentication(self):
        """Test builder can create rejected authentication result."""
        user_id = uuid4()
        
        result = (ResultBuilder()
                  .with_user(user_id)
                  .with_biometric_scores(
                      similarity=0.3,
                      spoof_probability=0.8,
                      phrase_match=0.6,
                      phrase_ok=False,
                      inference_latency_ms=2000
                  )
                  .reject_with_reason(AuthReason.SPOOF)
                  .build())
        
        assert result.user_id == user_id
        assert result.decided is True
        assert result.accept is False
        assert result.reason == AuthReason.SPOOF
        assert result.is_successful() is False
        assert result.is_fraud_attempt() is True
    
    def test_builder_requires_decision(self):
        """Test that builder requires a decision before building."""
        with pytest.raises(ValueError, match="Result must be decided"):
            (ResultBuilder()
             .with_user(uuid4())
             .build())
    
    def test_builder_reset_functionality(self):
        """Test that builder can be reset and reused."""
        builder = ResultBuilder()
        
        # First result
        result1 = (builder
                   .with_user(uuid4())
                   .accept_with_reason(AuthReason.OK)
                   .build())
        
        # Reset and create second result
        result2 = (builder
                   .reset()
                   .with_user(uuid4())
                   .reject_with_reason(AuthReason.LOW_SIMILARITY)
                   .build())
        
        assert result1.id != result2.id
        assert result1.accept is True
        assert result2.accept is False