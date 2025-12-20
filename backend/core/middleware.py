"""
FastAPI Middleware - Request/Response Logging and Performance Tracking
Provides automatic logging and metrics for all API requests
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logger import get_logger

logger = get_logger("api.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests and responses
    Tracks performance metrics and request context
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        # Extract request context
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Track HTTP request (Prometheus)
        try:
            from core.monitoring import http_requests_total, http_request_duration, PROMETHEUS_AVAILABLE
            if PROMETHEUS_AVAILABLE:
                # Will track after response
                pass
        except ImportError:
            http_requests_total = http_request_duration = None
        
        # Get user ID from token if available
        user_id = None
        try:
            from api.auth import verify_token
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                user = verify_token(token)
                if user:
                    user_id = user.get("sub")
        except Exception:
            pass  # Not authenticated, continue
        
        # Log request start
        logger.debug(
            f"Request started: {method} {path}",
            context={
                "type": "request_start",
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_id": user_id
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Track HTTP metrics (Prometheus)
            try:
                from core.monitoring import http_requests_total, http_request_duration, PROMETHEUS_AVAILABLE
                if PROMETHEUS_AVAILABLE and http_requests_total and http_request_duration:
                    status = str(status_code)
                    # Normalize endpoint path (remove IDs, etc.)
                    endpoint = path.split('/')[-1] if path else "unknown"
                    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
                    http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            except (ImportError, AttributeError):
                pass
            
            # Log successful request
            logger.log_request(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_id=user_id,
                query_params=query_params
            )
            
            # Add performance header
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {method} {path}",
                context={
                    "type": "request_error",
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_id": user_id
                },
                exception=e
            )
            
            raise


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking performance metrics
    Adds timing information to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track request performance
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler
            
        Returns:
            Response with performance headers
        """
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Add performance headers
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Request-Id"] = request.headers.get("X-Request-Id", "unknown")
        
        # Log slow requests (>1 second)
        if duration_ms > 1000:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                context={
                    "type": "slow_request",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms
                }
            )
        
        return response

