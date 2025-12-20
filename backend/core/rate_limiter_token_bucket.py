"""
Token Bucket rate limiter - in-memory, free, works for single instance
Better algorithm than simple sliding window
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from threading import Lock

class TokenBucketRateLimiter:
    """
    Token Bucket algorithm for rate limiting
    - Free (no external dependencies)
    - Works for single instance
    - More accurate than simple sliding window
    - Smooths out traffic bursts
    """
    
    def __init__(self):
        self.buckets: Dict[str, dict] = defaultdict(lambda: {
            "tokens": 0,
            "last_refill": time.time(),
            "lock": Lock()
        })
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 20,
        window_seconds: int = 60,
        per_user: bool = False
    ) -> Tuple[bool, int]:
        """
        Token Bucket algorithm
        
        Args:
            identifier: User ID or IP address
            max_requests: Maximum requests (bucket capacity)
            window_seconds: Refill rate (tokens per second)
            per_user: Not used, kept for API compatibility
        
        Returns:
            (is_allowed, remaining_tokens)
        """
        bucket = self.buckets[identifier]
        now = time.time()
        
        with bucket["lock"]:
            # Calculate tokens to add based on time passed
            time_passed = now - bucket["last_refill"]
            tokens_to_add = (time_passed * max_requests) / window_seconds
            
            # Refill bucket (but don't exceed capacity)
            bucket["tokens"] = min(
                max_requests,
                bucket["tokens"] + tokens_to_add
            )
            bucket["last_refill"] = now
            
            # Check if we have tokens
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                remaining = int(bucket["tokens"])
                return True, remaining
            else:
                # Not enough tokens
                remaining = 0
                return False, remaining
    
    def reset(self, identifier: str, per_user: bool = False):
        """Reset rate limit for identifier"""
        if identifier in self.buckets:
            with self.buckets[identifier]["lock"]:
                self.buckets[identifier]["tokens"] = 0
                self.buckets[identifier]["last_refill"] = time.time()

