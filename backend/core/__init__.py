"""
Core scalability and reliability modules
"""
from .cache import CacheManager, cache_manager
from .circuit_breaker import CircuitBreaker, CircuitState, openai_circuit_breaker, anthropic_circuit_breaker
from .retry import retry_with_backoff
from .rate_limiter_redis import RedisRateLimiter
from .task_queue import TaskQueue, TaskStatus, task_queue
from .error_handler import ErrorHandler, handle_errors
from .resource_manager import ResourceManager, setup_graceful_shutdown
from .encryption import ImageEncryption
from .audit_logger import AuditLogger, AuditAction
# Lazy import to avoid FastAPI dependency for unit tests
try:
    from .streaming import StreamingResponseBuilder
except ImportError:
    StreamingResponseBuilder = None  # Allow tests to import other modules
from .logger import StructuredLogger, get_logger, LogLevel
from .middleware import RequestLoggingMiddleware, PerformanceMiddleware
from .pii_redaction import PIIRedactor
from .monitoring import (
    init_sentry, track_llm_api_call, track_vision_analysis,
    track_prescription_extraction, track_browser_execution,
    track_cache_hit, track_cache_miss, get_prometheus_metrics
)

__all__ = [
    "CacheManager",
    "cache_manager",
    "CircuitBreaker",
    "CircuitState",
    "openai_circuit_breaker",
    "anthropic_circuit_breaker",
    "retry_with_backoff",
    "RedisRateLimiter",
    "TaskQueue",
    "TaskStatus",
    "task_queue",
    "ErrorHandler",
    "handle_errors",
    "ResourceManager",
    "setup_graceful_shutdown",
    "ImageEncryption",
    "AuditLogger",
    "AuditAction",
    "StreamingResponseBuilder",
    "StructuredLogger",
    "get_logger",
    "LogLevel",
    "RequestLoggingMiddleware",
    "PerformanceMiddleware",
    "PIIRedactor",
    "init_sentry",
    "track_llm_api_call",
    "track_vision_analysis",
    "track_prescription_extraction",
    "track_browser_execution",
    "track_cache_hit",
    "track_cache_miss",
    "get_prometheus_metrics"
]

