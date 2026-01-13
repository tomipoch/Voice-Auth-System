"""Threshold policies for risk assessment."""

from dataclasses import dataclass
from typing import Dict, Any

from ...shared.types.common_types import RiskLevel


@dataclass
class ThresholdPolicy:
    """Defines thresholds for authentication decisions."""
    
    name: str
    risk_level: RiskLevel
    similarity_threshold: float
    spoof_threshold: float  # Max acceptable spoof probability
    phrase_match_threshold: float
    max_inference_latency_ms: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def validate_thresholds(self) -> bool:
        """Validate that all thresholds are within acceptable ranges."""
        return (
            0.0 <= self.similarity_threshold <= 1.0 and
            0.0 <= self.spoof_threshold <= 1.0 and
            0.0 <= self.phrase_match_threshold <= 1.0 and
            self.max_inference_latency_ms > 0
        )
    
    def is_stricter_than(self, other: 'ThresholdPolicy') -> bool:
        """Check if this policy is stricter than another."""
        return (
            self.similarity_threshold >= other.similarity_threshold and
            self.spoof_threshold <= other.spoof_threshold and
            self.phrase_match_threshold >= other.phrase_match_threshold and
            self.max_inference_latency_ms <= other.max_inference_latency_ms
        )


# Predefined policies for different risk levels
class PolicyTemplates:
    """Common threshold policy templates."""
    
    @staticmethod
    def get_bank_strict() -> ThresholdPolicy:
        """High-security policy for banking applications."""
        return ThresholdPolicy(
            name="bank_strict_v1",
            risk_level=RiskLevel.HIGH,
            similarity_threshold=0.90,
            spoof_threshold=0.4,  # Optimizado: mejor balance detección vs usabilidad
            phrase_match_threshold=0.85,
            max_inference_latency_ms=3000,
            metadata={"description": "Strict policy for banking operations"}
        )
    
    @staticmethod
    def get_standard() -> ThresholdPolicy:
        """Standard security policy for general applications."""
        return ThresholdPolicy(
            name="standard_v1",
            risk_level=RiskLevel.MEDIUM,
            similarity_threshold=0.85,
            spoof_threshold=0.4,  # Optimizado: mejor balance detección vs usabilidad
            phrase_match_threshold=0.80,
            max_inference_latency_ms=5000,
            metadata={"description": "Standard security policy"}
        )
    
    @staticmethod
    def get_demo_relaxed() -> ThresholdPolicy:
        """Relaxed policy for demos and testing."""
        return ThresholdPolicy(
            name="demo_relaxed_v1",
            risk_level=RiskLevel.LOW,
            similarity_threshold=0.75,
            spoof_threshold=0.5,
            phrase_match_threshold=0.70,
            max_inference_latency_ms=10000,
            metadata={"description": "Relaxed policy for demos"}
        )