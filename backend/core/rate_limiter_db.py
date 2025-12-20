"""
Database-based rate limiter using PostgreSQL
Free alternative to Redis - uses existing database
"""
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from typing import Tuple, Optional
import os
from api.config import settings

class DatabaseRateLimiter:
    """
    Rate limiter using PostgreSQL database
    Works across multiple instances (shared database)
    Free - uses existing Supabase/PostgreSQL connection
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        if not self.database_url:
            raise ValueError("Database URL required for database rate limiter")
        
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=2,  # Small pool for rate limiting queries
            max_overflow=5
        )
        self._init_table()
    
    def _init_table(self):
        """Create rate limit table if it doesn't exist"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        identifier VARCHAR(255) NOT NULL,
                        request_time TIMESTAMP NOT NULL,
                        PRIMARY KEY (identifier, request_time)
                    )
                """))
                # Create index for faster queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier_time 
                    ON rate_limits(identifier, request_time)
                """))
                conn.commit()
        except Exception as e:
            import logging
            logging.debug(f"Rate limit table creation error (may already exist): {e}")
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 20,
        window_seconds: int = 60,
        per_user: bool = False
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed using database sliding window
        
        Args:
            identifier: User ID or IP address
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            per_user: If True, use user-based limiting
        
        Returns:
            (is_allowed, remaining_requests)
        """
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            with self.engine.connect() as conn:
                # Delete old entries (cleanup)
                conn.execute(
                    text("DELETE FROM rate_limits WHERE request_time < :window_start"),
                    {"window_start": window_start}
                )
                
                # Count current requests in window
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM rate_limits 
                        WHERE identifier = :identifier 
                        AND request_time >= :window_start
                    """),
                    {"identifier": identifier, "window_start": window_start}
                )
                current_count = result.scalar() or 0
                
                # Check if allowed
                if current_count >= max_requests:
                    remaining = 0
                    conn.commit()
                    return False, remaining
                
                # Add current request
                conn.execute(
                    text("""
                        INSERT INTO rate_limits (identifier, request_time) 
                        VALUES (:identifier, :request_time)
                    """),
                    {"identifier": identifier, "request_time": now}
                )
                
                conn.commit()
                remaining = max_requests - (current_count + 1)
                
                return True, remaining
                
        except Exception as e:
            import logging
            logging.error(f"Database rate limiter error: {e}", exc_info=True)
            # Fail open - allow request if database fails
            return True, max_requests
    
    def reset(self, identifier: str, per_user: bool = False):
        """Reset rate limit for identifier"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM rate_limits WHERE identifier = :identifier"),
                    {"identifier": identifier}
                )
                conn.commit()
        except Exception as e:
            import logging
            logging.error(f"Rate limiter reset error: {e}", exc_info=True)

