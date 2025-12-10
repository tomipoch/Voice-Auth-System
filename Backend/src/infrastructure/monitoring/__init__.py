"""Monitoring package initialization."""

# Import all metrics to register them with Prometheus
from .metrics import (
    # Enrollment
    enrollment_total,
    enrollment_duration,
    enrollment_samples_quality,
    
    # Verification
    verification_total,
    verification_duration,
    verification_similarity_score,
    verification_spoofing_score,
    verification_asr_score,
    
    # Challenges
    challenge_created,
    challenge_expired,
    challenge_active,
    
    # Users
    users_total,
    users_enrolled,
    
    # API
    api_requests_total,
    api_request_duration,
    
    # Database
    db_query_duration,
    db_connections_active,
    
    # ML Models
    ml_inference_duration,
    
    # System
    system_info,
)

__all__ = [
    'enrollment_total',
    'enrollment_duration',
    'enrollment_samples_quality',
    'verification_total',
    'verification_duration',
    'verification_similarity_score',
    'verification_spoofing_score',
    'verification_asr_score',
    'challenge_created',
    'challenge_expired',
    'challenge_active',
    'users_total',
    'users_enrolled',
    'api_requests_total',
    'api_request_duration',
    'db_query_duration',
    'db_connections_active',
    'ml_inference_duration',
    'system_info',
]
