"""
Enhanced Error Handling Module - Production-Grade Error Management
Provides comprehensive error handling, retry logic, and user-friendly error messages
"""
import asyncio
from typing import Callable, Any, Optional, Dict, TypeVar, Union
from functools import wraps
import traceback
from enum import Enum

from .logger import get_logger

logger = get_logger("error_handler")

T = TypeVar('T')

class ErrorCategory(Enum):
    """Error categories for better error handling"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    NETWORK = "network"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorHandler:
    """
    Centralized error handling with retry logic and structured logging
    Provides consistent error management across the application
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize error handler
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger
    
    async def retry_with_backoff_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry an async function with exponential backoff
        
        Args:
            func: Async function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Retry attempt {attempt + 1}/{self.max_retries} failed",
                        context={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "error": str(e),
                            "retry_delay": delay
                        },
                        exception=e
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    self.logger.error(
                        f"All {self.max_retries} retry attempts failed",
                        context={
                            "function": func.__name__,
                            "max_retries": self.max_retries
                        },
                        exception=e
                    )
        
        raise last_exception
    
    def retry_with_backoff_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry a sync function with exponential backoff
        
        Args:
            func: Sync function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        import time
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Retry attempt {attempt + 1}/{self.max_retries} failed",
                        context={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "error": str(e),
                            "retry_delay": delay
                        },
                        exception=e
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    self.logger.error(
                        f"All {self.max_retries} retry attempts failed",
                        context={
                            "function": func.__name__,
                            "max_retries": self.max_retries
                        },
                        exception=e
                    )
        
        raise last_exception
    
    @staticmethod
    def categorize_error(error: Exception) -> ErrorCategory:
        """
        Categorize error for better handling
        
        Args:
            error: Exception to categorize
            
        Returns:
            ErrorCategory enum value
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network errors
        if (any(keyword in error_str for keyword in ["connection", "timeout", "network"]) or
            "connection" in error_type or "timeout" in error_type):
            return ErrorCategory.NETWORK
        
        # Rate limiting
        if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
            return ErrorCategory.RATE_LIMIT
        
        # Authentication
        if any(keyword in error_str for keyword in ["api key", "authentication", "unauthorized", "401"]):
            return ErrorCategory.AUTHENTICATION
        
        # Authorization
        if any(keyword in error_str for keyword in ["forbidden", "403", "permission", "access denied"]):
            return ErrorCategory.AUTHORIZATION
        
        # Not found
        if any(keyword in error_str for keyword in ["not found", "404", "does not exist"]):
            return ErrorCategory.NOT_FOUND
        
        # External API errors
        if any(keyword in error_str for keyword in ["api", "external", "third-party", "quota", "insufficient"]):
            return ErrorCategory.EXTERNAL_API
        
        # Database errors
        if any(keyword in error_str for keyword in ["database", "sql", "query", "connection pool"]):
            return ErrorCategory.DATABASE
        
        # Validation errors
        if any(keyword in error_str for keyword in ["validation", "invalid", "bad request", "400"]):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    @staticmethod
    def get_user_friendly_error(error: Exception) -> str:
        """
        Convert technical errors to user-friendly messages
        
        Args:
            error: Exception to convert
            
        Returns:
            User-friendly error message
        """
        category = ErrorHandler.categorize_error(error)
        error_str = str(error).lower()
        
        error_messages = {
            ErrorCategory.NETWORK: "Connection error. Please check your internet connection and try again.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication error. Please check your API configuration.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.NOT_FOUND: "The requested resource was not found.",
            ErrorCategory.EXTERNAL_API: "API quota exceeded. Please check your API account limits.",
            ErrorCategory.DATABASE: "Database error. Please try again later.",
            ErrorCategory.VALIDATION: "Invalid input. Please check your request and try again.",
            ErrorCategory.INTERNAL: "An internal error occurred. Please try again or contact support.",
            ErrorCategory.UNKNOWN: "An error occurred. Please try again or contact support if the problem persists."
        }
        
        # Special handling for specific error types
        if "image" in error_str or "blurry" in error_str:
            return "Image quality issue. Please use a clearer image."
        
        if "file" in error_str or "upload" in error_str:
            return "File upload error. Please try a different image."
        
        return error_messages.get(category, error_messages[ErrorCategory.UNKNOWN])
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log error with structured context for debugging
        
        Args:
            error: Exception to log
            context: Additional context dictionary
        """
        category = ErrorHandler.categorize_error(error)
        
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_category": category.value,
            **(context or {})
        }
        
        logger.error(
            f"Error occurred: {type(error).__name__}",
            context=error_context,
            exception=error
        )


def handle_errors(func: Callable) -> Callable:
    """
    Decorator for automatic error handling with structured logging
    
    Automatically catches exceptions, logs them with context,
    and converts them to user-friendly messages
    
    Usage:
        @handle_errors
        async def my_function():
            # Re-raise the exception after logging
            raise
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.log_error(
                e,
                {
                    "function": func.__name__,
                    "module": func.__module__
                }
            )
            user_message = ErrorHandler.get_user_friendly_error(e)
            raise Exception(user_message) from e
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.log_error(
                e,
                {
                    "function": func.__name__,
                    "module": func.__module__
                }
            )
            user_message = ErrorHandler.get_user_friendly_error(e)
            raise Exception(user_message) from e
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
