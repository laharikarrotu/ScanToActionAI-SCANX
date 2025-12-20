"""
Monitoring and Observability Module
Integrates Sentry for error tracking and Prometheus for metrics
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Sentry Integration
SENTRY_AVAILABLE = False
try:
    import sentry_sdk  # type: ignore[reportMissingImports]
    from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore[reportMissingImports]
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore[reportMissingImports]
    from sentry_sdk.integrations.httpx import HttpxIntegration  # type: ignore[reportMissingImports]
    SENTRY_AVAILABLE = True
except ImportError:
    sentry_sdk = None

# Prometheus Integration
PROMETHEUS_AVAILABLE = False
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore[reportMissingImports]
    PROMETHEUS_AVAILABLE = True
except ImportError:
    Counter = Histogram = Gauge = None

# Prometheus Metrics
if PROMETHEUS_AVAILABLE:
    # Request metrics
    http_requests_total = Counter(
        'healthscan_http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )
    
    http_request_duration = Histogram(
        'healthscan_http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    )
    
    # LLM API metrics
    llm_api_calls_total = Counter(
        'healthscan_llm_api_calls_total',
        'Total LLM API calls',
        ['provider', 'model', 'status']
    )
    
    llm_api_duration = Histogram(
        'healthscan_llm_api_duration_seconds',
        'LLM API call duration in seconds',
        ['provider', 'model']
    )
    
    # Vision analysis metrics
    vision_analyses_total = Counter(
        'healthscan_vision_analyses_total',
        'Total vision analyses',
        ['status']
    )
    
    # Prescription extraction metrics
    prescription_extractions_total = Counter(
        'healthscan_prescription_extractions_total',
        'Total prescription extractions',
        ['status']
    )
    
    # Browser execution metrics
    browser_executions_total = Counter(
        'healthscan_browser_executions_total',
        'Total browser executions',
        ['status']
    )
    
    browser_execution_duration = Histogram(
        'healthscan_browser_execution_duration_seconds',
        'Browser execution duration in seconds'
    )
    
    # Active connections
    active_connections = Gauge(
        'healthscan_active_connections',
        'Number of active connections'
    )
    
    # Cache metrics
    cache_hits_total = Counter(
        'healthscan_cache_hits_total',
        'Total cache hits',
        ['cache_type']
    )
    
    cache_misses_total = Counter(
        'healthscan_cache_misses_total',
        'Total cache misses',
        ['cache_type']
    )

def init_sentry(dsn: Optional[str] = None, environment: str = "production"):
    """
    Initialize Sentry for error tracking.
    
    Args:
        dsn: Sentry DSN (from SENTRY_DSN env var if not provided)
        environment: Environment name (production, development, etc.)
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry not available. Install with: pip install sentry-sdk")
        return False
    
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("SENTRY_DSN not set. Sentry monitoring disabled.")
        return False
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                HttpxIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of transactions
            send_default_pii=False,  # Don't send PII to Sentry
            before_send=lambda event, hint: filter_pii_from_sentry(event),  # Filter PII
        )
        logger.info("Sentry initialized successfully", context={"environment": environment})
        return True
    except Exception as e:
        logger.error(f"Sentry initialization failed: {e}")
        return False

def filter_pii_from_sentry(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter PII from Sentry events to ensure HIPAA compliance.
    """
    # Remove sensitive data from event
    if "request" in event:
        if "data" in event["request"]:
            # Redact potential PII from request data
            if isinstance(event["request"]["data"], dict):
                for key in list(event["request"]["data"].keys()):
                    if any(pii_term in key.lower() for pii_term in ["ssn", "phone", "email", "patient", "name", "address"]):
                        event["request"]["data"][key] = "[REDACTED]"
    
    return event

def track_llm_api_call(provider: str, model: str, duration: float, success: bool):
    """Track LLM API call metrics"""
    if PROMETHEUS_AVAILABLE:
        status = "success" if success else "error"
        llm_api_calls_total.labels(provider=provider, model=model, status=status).inc()
        llm_api_duration.labels(provider=provider, model=model).observe(duration)

def track_vision_analysis(success: bool):
    """Track vision analysis metrics"""
    if PROMETHEUS_AVAILABLE:
        status = "success" if success else "error"
        vision_analyses_total.labels(status=status).inc()

def track_prescription_extraction(success: bool):
    """Track prescription extraction metrics"""
    if PROMETHEUS_AVAILABLE:
        status = "success" if success else "error"
        prescription_extractions_total.labels(status=status).inc()

def track_browser_execution(success: bool, duration: float):
    """Track browser execution metrics"""
    if PROMETHEUS_AVAILABLE:
        status = "success" if success else "error"
        browser_executions_total.labels(status=status).inc()
        browser_execution_duration.observe(duration)

def track_cache_hit(cache_type: str):
    """Track cache hit"""
    if PROMETHEUS_AVAILABLE:
        cache_hits_total.labels(cache_type=cache_type).inc()

def track_cache_miss(cache_type: str):
    """Track cache miss"""
    if PROMETHEUS_AVAILABLE:
        cache_misses_total.labels(cache_type=cache_type).inc()

def get_prometheus_metrics():
    """Get Prometheus metrics in text format"""
    if PROMETHEUS_AVAILABLE:
        return generate_latest()
    return b"# Prometheus not available\n"

