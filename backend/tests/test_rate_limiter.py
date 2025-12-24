"""
Unit tests for rate limiter
"""
import pytest
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class"""
    
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            allowed, remaining = limiter.is_allowed("test_user")
            assert allowed == True
            assert remaining >= 0
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test that rate limiter blocks requests over limit"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Use up all requests
        for _ in range(3):
            limiter.is_allowed("test_user")
        
        # Next request should be blocked
        allowed, remaining = limiter.is_allowed("test_user")
        assert allowed == False
        assert remaining == 0
    
    def test_rate_limiter_reset(self):
        """Test that rate limiter reset works"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Use up requests
        limiter.is_allowed("test_user")
        limiter.is_allowed("test_user")
        
        # Should be blocked
        allowed, _ = limiter.is_allowed("test_user")
        assert allowed == False
        
        # Reset
        limiter.reset("test_user")
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("test_user")
        assert allowed == True
    
    def test_rate_limiter_per_user(self):
        """Test that rate limiter works per user"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # User 1 uses up requests
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        
        # User 1 should be blocked
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 == False
        
        # User 2 should still be allowed
        allowed2, _ = limiter.is_allowed("user2")
        assert allowed2 == True

