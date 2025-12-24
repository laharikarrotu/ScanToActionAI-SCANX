"""
Rate Limiting Module
Provides multiple rate limiting implementations for different use cases
"""
from typing import Optional

# Try to import different rate limiter implementations
try:
    from .rate_limiter_redis import RedisRateLimiter
    REDIS_AVAILABLE = True
except ImportError:
    RedisRateLimiter = None
    REDIS_AVAILABLE = False

try:
    from .rate_limiter_db import DatabaseRateLimiter
    DB_AVAILABLE = True
except ImportError:
    DatabaseRateLimiter = None
    DB_AVAILABLE = False

try:
    from .rate_limiter_token_bucket import TokenBucketRateLimiter
    TOKEN_BUCKET_AVAILABLE = True
except ImportError:
    TokenBucketRateLimiter = None
    TOKEN_BUCKET_AVAILABLE = False

# Simple in-memory rate limiter (for development/testing)
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time

class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter for development/testing
    For production, use RedisRateLimiter or DatabaseRateLimiter
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed
        Returns: (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False, 0
        
        # Add current request
        self.requests[identifier].append(now)
        remaining = self.max_requests - len(self.requests[identifier])
        
        return True, remaining
    
    def reset(self, identifier: str):
        """Reset rate limit for an identifier"""
        self.requests[identifier] = []


def get_rate_limiter(preferred: str = "redis") -> Optional[object]:
    """
    Factory function to get the best available rate limiter
    
    Args:
        preferred: Preferred implementation ("redis", "db", "token_bucket", "memory")
    
    Returns:
        Rate limiter instance or None if none available
    """
    if preferred == "redis" and REDIS_AVAILABLE and RedisRateLimiter:
        try:
            return RedisRateLimiter()
        except Exception:
            pass
    
    if preferred == "db" and DB_AVAILABLE and DatabaseRateLimiter:
        try:
            return DatabaseRateLimiter()
        except Exception:
            pass
    
    if preferred == "token_bucket" and TOKEN_BUCKET_AVAILABLE and TokenBucketRateLimiter:
        try:
            return TokenBucketRateLimiter()
        except Exception:
            pass
    
    # Fallback to in-memory
    return InMemoryRateLimiter()


__all__ = [
    "RedisRateLimiter",
    "DatabaseRateLimiter",
    "TokenBucketRateLimiter",
    "InMemoryRateLimiter",
    "get_rate_limiter",
    "REDIS_AVAILABLE",
    "DB_AVAILABLE",
    "TOKEN_BUCKET_AVAILABLE",
]

