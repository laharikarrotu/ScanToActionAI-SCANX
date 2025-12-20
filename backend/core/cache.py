"""
Redis-based caching layer for scalable result storage
"""
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

import json
import hashlib
from typing import Optional, Any
import pickle
import os
from datetime import timedelta

class CacheManager:
    """
    Scalable caching layer using Redis
    Supports distributed caching across multiple instances
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self._connect()
    
    def _connect(self):
        """Lazy connection to Redis"""
        if not REDIS_AVAILABLE:
            self.client = None
            self._memory_cache = {}
            return
        
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}. Falling back to in-memory cache.")
            self.client = None
            self._memory_cache = {}
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a cache key"""
        return f"healthscan:{prefix}:{identifier}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return self._memory_cache.get(key)
        
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL (seconds)"""
        if not self.client:
            self._memory_cache[key] = value
            return
        
        try:
            data = pickle.dumps(value)
            self.client.setex(key, ttl, data)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.client:
            self._memory_cache.pop(key, None)
            return
        
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def get_image_result(self, image_hash: str) -> Optional[dict]:
        """Get cached vision analysis result for an image"""
        key = self._make_key("vision", image_hash)
        return self.get(key)
    
    def set_image_result(self, image_hash: str, result: dict, ttl: int = 86400):
        """Cache vision analysis result (24 hours default)"""
        key = self._make_key("vision", image_hash)
        self.set(key, result, ttl)
    
    def get_ui_schema(self, image_hash: str, intent: str) -> Optional[dict]:
        """Get cached UI schema for image + intent combination"""
        combined = f"{image_hash}:{hashlib.md5(intent.encode()).hexdigest()}"
        key = self._make_key("ui_schema", combined)
        return self.get(key)
    
    def set_ui_schema(self, image_hash: str, intent: str, schema: dict, ttl: int = 3600):
        """Cache UI schema (1 hour default)"""
        combined = f"{image_hash}:{hashlib.md5(intent.encode()).hexdigest()}"
        key = self._make_key("ui_schema", combined)
        self.set(key, schema, ttl)
    
    def get_plan(self, schema_hash: str, intent: str) -> Optional[dict]:
        """Get cached action plan"""
        combined = f"{schema_hash}:{hashlib.md5(intent.encode()).hexdigest()}"
        key = self._make_key("plan", combined)
        return self.get(key)
    
    def set_plan(self, schema_hash: str, intent: str, plan: dict, ttl: int = 1800):
        """Cache action plan (30 minutes default)"""
        combined = f"{schema_hash}:{hashlib.md5(intent.encode()).hexdigest()}"
        key = self._make_key("plan", combined)
        self.set(key, plan, ttl)
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        if not self.client:
            return
        
        try:
            pattern = f"healthscan:*:{user_id}*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")

# Global cache instance
cache_manager = CacheManager()

