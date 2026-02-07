"""Custom Prometheus metrics for voice biometrics system."""

from prometheus_client import Counter, Histogram, Gauge, Info

# Enrollment metrics
enrollment_total = Counter(
    'enrollment_total',
    'Total number of enrollment attempts',
    ['status']  # success, failed
)

enrollment_duration = Histogram(
    'enrollment_duration_seconds',
    'Time spent on enrollment process',
    buckets=[10, 20, 30, 45, 60, 90, 120]
)

enrollment_samples_quality = Histogram(
    'enrollment_sample_quality',
    'Quality score of enrollment samples',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# Verification metrics
verification_total = Counter(
    'verification_total',
    'Total number of verification attempts',
    ['status', 'difficulty']  # success/failed, easy/medium/hard
)

verification_duration = Histogram(
    'verification_duration_seconds',
    'Time spent on verification process',
    buckets=[5, 10, 15, 20, 30, 45, 60]
)

verification_similarity_score = Histogram(
    'verification_similarity_score',
    'Speaker similarity scores',
    buckets=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

verification_spoofing_score = Histogram(
    'verification_spoofing_score',
    'Anti-spoofing scores',
    buckets=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

verification_asr_score = Histogram(
    'verification_asr_score',
    'ASR (speech recognition) scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# Challenge metrics
challenge_created = Counter(
    'challenge_created_total',
    'Total challenges created',
    ['difficulty']
)

challenge_expired = Counter(
    'challenge_expired_total',
    'Total challenges expired',
    ['difficulty']
)

challenge_active = Gauge(
    'challenge_active_count',
    'Current number of active challenges'
)

# User metrics
users_total = Gauge(
    'users_total',
    'Total number of users'
)

users_enrolled = Gauge(
    'users_enrolled',
    'Number of users with voiceprints'
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

# ML Model metrics
ml_inference_duration = Histogram(
    'ml_inference_duration_seconds',
    'ML model inference time',
    ['model'],  # ecapa_tdnn, anti_spoofing, asr
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
)

# System info
system_info = Info('voice_biometrics_system', 'System information')
