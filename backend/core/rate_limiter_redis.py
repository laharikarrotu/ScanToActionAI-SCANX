"""
Redis-based rate limiter for distributed rate limiting
Works across multiple backend instances
"""
try:
    import redis  # type: ignore[reportMissingImports]
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

import time
from typing import Tuple, Optional
import os

class RedisRateLimiter:
    """
    Distributed rate limiter using Redis
    Supports sliding window algorithm for accurate rate limiting
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/1")
        if not REDIS_AVAILABLE:
            self.client = None
            return
        
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            self.client.ping()
        except Exception as e:
            import logging
            logging.warning(f"Redis rate limiter connection failed: {e}", exc_info=True)
            self.client = None
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 20,
        window_seconds: int = 60,
        per_user: bool = False
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed using sliding window algorithm
        
        Args:
            identifier: User ID or IP address
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            per_user: If True, use user-based limiting; if False, use IP-based
        
        Returns:
            (is_allowed, remaining_requests)
        """
        if not self.client:
            # Fallback: always allow if Redis unavailable
            return True, max_requests
        
        key = f"ratelimit:{'user' if per_user else 'ip'}:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        try:
            # Use sorted set for sliding window
            pipe = self.client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, window_seconds + 1)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for current request
            
            is_allowed = current_count <= max_requests
            remaining = max(0, max_requests - current_count)
            
            return is_allowed, remaining
            
        except Exception as e:
            import logging
            logging.error(f"Rate limiter error: {e}", exc_info=True)
            # Fail open - allow request if Redis fails
            return True, max_requests
    
    def reset(self, identifier: str, per_user: bool = False):
        """Reset rate limit for identifier"""
        if not self.client:
            return
        
        key = f"ratelimit:{'user' if per_user else 'ip'}:{identifier}"
        try:
            self.client.delete(key)
        except Exception as e:
            import logging
            logging.error(f"Rate limiter reset error: {e}", exc_info=True)

