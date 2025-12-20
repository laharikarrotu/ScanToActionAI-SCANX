"""
Enhanced Error Handling Module
Provides comprehensive error handling, retry logic, and user-friendly error messages
"""
import logging
import asyncio
from typing import Callable, Any, Optional, Dict
from functools import wraps
import traceback

class ErrorHandler:
    """Centralized error handling with retry logic"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry a function with exponential backoff
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    asyncio.sleep(delay) if asyncio.iscoroutinefunction(func) else None
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed: {str(e)}")
        
        raise last_exception
    
    @staticmethod
    def get_user_friendly_error(error: Exception) -> str:
        """
        Convert technical errors to user-friendly messages
        """
        error_str = str(error).lower()
        
        # Network errors
        if "connection" in error_str or "timeout" in error_str:
            return "Connection error. Please check your internet connection and try again."
        
        if "429" in error_str or "rate limit" in error_str:
            return "Too many requests. Please wait a moment and try again."
        
        # API errors
        if "api key" in error_str or "authentication" in error_str:
            return "Authentication error. Please check your API configuration."
        
        if "quota" in error_str or "insufficient" in error_str:
            return "API quota exceeded. Please check your API account limits."
        
        # Image errors
        if "image" in error_str or "blurry" in error_str:
            return "Image quality issue. Please use a clearer image."
        
        if "file" in error_str or "upload" in error_str:
            return "File upload error. Please try a different image."
        
        # Generic fallback
        return "An error occurred. Please try again or contact support if the problem persists."
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log error with context for debugging
        """
        logger = logging.getLogger(__name__)
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        if context:
            error_details["context"] = context
        
        logger.error(f"Error occurred: {error_details}")

def handle_errors(func: Callable) -> Callable:
    """
    Decorator for automatic error handling
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.log_error(e, {"function": func.__name__})
            user_message = ErrorHandler.get_user_friendly_error(e)
            raise Exception(user_message) from e
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.log_error(e, {"function": func.__name__})
            user_message = ErrorHandler.get_user_friendly_error(e)
            raise Exception(user_message) from e
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

