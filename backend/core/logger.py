"""
Structured Logging Module - Production-Grade Logging
Provides JSON-structured logging with levels, context, and performance metrics
"""
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback
from pathlib import Path

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StructuredLogger:
    """
    Production-grade structured logger with JSON output
    Provides consistent, parseable logs for monitoring and debugging
    """
    
    def __init__(
        self,
        name: str = "healthscan",
        log_file: Optional[str] = None,
        log_level: LogLevel = LogLevel.INFO,
        json_output: bool = True
    ):
        """
        Initialize structured logger
        
        Args:
            name: Logger name
            log_file: Optional file path for file logging
            log_level: Minimum log level
            json_output: Whether to output JSON format (default: True)
        """
        self.name = name
        self.json_output = json_output
        self.log_level = log_level
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.value))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.value))
        
        if json_output:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # File gets all logs
            
            if json_output:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                )
            
            self.logger.addHandler(file_handler)
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Internal logging method with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "logger": self.name,
            "message": message,
            **kwargs
        }
        
        if context:
            log_data["context"] = context
        
        if exception:
            log_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc() if level in [LogLevel.ERROR, LogLevel.CRITICAL] else None
            }
        
        log_method = getattr(self.logger, level.value.lower())
        if self.json_output:
            log_method(json.dumps(log_data, default=str))
        else:
            # Format for human-readable output
            context_str = f" | Context: {json.dumps(context)}" if context else ""
            exception_str = f" | Exception: {str(exception)}" if exception else ""
            log_method(f"{message}{context_str}{exception_str}")
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, context, **kwargs)
    
    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Log error message"""
        self._log(LogLevel.ERROR, message, context, exception, **kwargs)
    
    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, context, exception, **kwargs)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log HTTP request with performance metrics"""
        self.info(
            f"{method} {path} - {status_code}",
            context={
                "type": "http_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_id": user_id,
                **kwargs
            }
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log performance metrics"""
        perf_data = {
            "type": "performance",
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            **(context or {}),
            **kwargs
        }
        self.info(f"Performance: {operation} took {duration_ms:.2f}ms", context=perf_data)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        return json.dumps(log_data, default=str)


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None

def get_logger(name: str = "healthscan") -> StructuredLogger:
    """
    Get or create global logger instance
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        log_file = None
        log_level = LogLevel.INFO
        
        # Check environment for logging configuration
        import os
        if os.getenv("LOG_FILE"):
            log_file = os.getenv("LOG_FILE")
        if os.getenv("LOG_LEVEL"):
            try:
                log_level = LogLevel[os.getenv("LOG_LEVEL").upper()]
            except KeyError:
                pass
        
        _logger_instance = StructuredLogger(
            name=name,
            log_file=log_file,
            log_level=log_level,
            json_output=os.getenv("LOG_JSON", "true").lower() == "true"
        )
    
    return _logger_instance

