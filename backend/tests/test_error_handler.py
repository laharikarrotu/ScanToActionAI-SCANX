"""
Unit tests for error handler module
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.error_handler import ErrorHandler, ErrorCategory


class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def test_categorize_network_error(self):
        """Test network error categorization"""
        error = ConnectionError("Connection timeout")
        category = ErrorHandler.categorize_error(error)
        assert category == ErrorCategory.NETWORK
    
    def test_categorize_rate_limit_error(self):
        """Test rate limit error categorization"""
        error = Exception("Rate limit exceeded. 429")
        category = ErrorHandler.categorize_error(error)
        assert category == ErrorCategory.RATE_LIMIT
    
    def test_categorize_authentication_error(self):
        """Test authentication error categorization"""
        error = Exception("Invalid API key")
        category = ErrorHandler.categorize_error(error)
        assert category == ErrorCategory.AUTHENTICATION
    
    def test_categorize_database_error(self):
        """Test database error categorization"""
        error = Exception("Database connection failed")
        category = ErrorHandler.categorize_error(error)
        assert category == ErrorCategory.DATABASE
    
    def test_sanitize_error_message_production(self):
        """Test error message sanitization in production"""
        error = Exception("Error in /path/to/file.py: Database connection postgresql://user:pass@host/db failed")
        sanitized = ErrorHandler.sanitize_error_message(error, is_production=True)
        
        assert "[file]" in sanitized or "file" not in sanitized.lower()
        assert "postgresql://" not in sanitized
        assert "[database]" in sanitized or "database" not in sanitized.lower()
    
    def test_sanitize_error_message_removes_api_key(self):
        """Test that API keys are removed from error messages"""
        error = Exception("API key: sk-1234567890abcdef failed")
        sanitized = ErrorHandler.sanitize_error_message(error, is_production=True)
        
        assert "sk-1234567890abcdef" not in sanitized
        assert "[REDACTED]" in sanitized or "REDACTED" in sanitized
    
    def test_sanitize_error_message_removes_email(self):
        """Test that email addresses are removed"""
        error = Exception("User email test@example.com not found")
        sanitized = ErrorHandler.sanitize_error_message(error, is_production=True)
        
        assert "test@example.com" not in sanitized
        assert "[email]" in sanitized
    
    def test_sanitize_error_message_removes_ip(self):
        """Test that IP addresses are removed"""
        error = Exception("Connection to 192.168.1.1 failed")
        sanitized = ErrorHandler.sanitize_error_message(error, is_production=True)
        
        assert "192.168.1.1" not in sanitized
        assert "[ip]" in sanitized
    
    def test_get_user_friendly_error_production(self):
        """Test user-friendly error messages in production"""
        error = ConnectionError("Connection timeout to database")
        message = ErrorHandler.get_user_friendly_error(error, is_production=True)
        
        assert "Connection error" in message or "connection" in message.lower()
        assert "timeout" not in message.lower()  # Should be generic
    
    def test_get_user_friendly_error_development(self):
        """Test error messages in development (more detailed)"""
        error = ValueError("Invalid input: missing required field")
        message = ErrorHandler.get_user_friendly_error(error, is_production=False)
        
        # Development mode can be more specific
        assert len(message) > 0

