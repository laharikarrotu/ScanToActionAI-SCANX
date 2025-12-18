"""
Simple rate limiter for API protection
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
import time

class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis-based rate limiting
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> tuple[bool, int]:
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

