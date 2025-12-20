"""
Resource Management Module
Handles cleanup, timeouts, and resource lifecycle management
"""
import asyncio
import logging
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager
import signal
import sys

class ResourceManager:
    """Manages resource cleanup and timeouts"""
    
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)
        self._cleanup_handlers = []
    
    def register_cleanup(self, handler: Callable):
        """Register a cleanup handler"""
        self._cleanup_handlers.append(handler)
    
    async def cleanup_all(self, timeout: Optional[float] = None):
        """Execute all registered cleanup handlers with timeout"""
        timeout = timeout or self.default_timeout
        
        for handler in self._cleanup_handlers:
            try:
                await asyncio.wait_for(
                    self._execute_cleanup(handler),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self.logger.error(f"Cleanup handler {handler.__name__} timed out after {timeout}s")
            except Exception as e:
                self.logger.warning(f"Cleanup handler {handler.__name__} failed: {e}")
    
    async def _execute_cleanup(self, handler: Callable):
        """Execute a single cleanup handler"""
        if asyncio.iscoroutinefunction(handler):
            await handler()
        else:
            handler()
    
    @asynccontextmanager
    async def timeout_context(self, timeout: float, operation_name: str = "operation"):
        """Context manager for operations with timeout"""
        try:
            yield
        except asyncio.TimeoutError:
            self.logger.error(f"{operation_name} timed out after {timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"{operation_name} failed: {e}")
            raise

def setup_graceful_shutdown(cleanup_func: Callable):
    """Setup graceful shutdown handlers"""
    def signal_handler(sig, frame):
        logging.info("Shutdown signal received, cleaning up...")
        if asyncio.iscoroutinefunction(cleanup_func):
            asyncio.run(cleanup_func())
        else:
            cleanup_func()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

