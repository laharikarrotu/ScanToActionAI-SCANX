"""
Unit tests for circuit breaker module
"""
import pytest
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def test_circuit_starts_closed(self):
        """Test that circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
    
    def test_successful_call(self):
        """Test successful function call"""
        cb = CircuitBreaker(name="test")
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_failure_increments_count(self):
        """Test that failures increment failure count"""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        def fail_func():
            raise Exception("Test error")
        
        # First failure
        with pytest.raises(Exception):
            cb.call(fail_func)
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED
        
        # Second failure
        with pytest.raises(Exception):
            cb.call(fail_func)
        assert cb.failure_count == 2
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold"""
        cb = CircuitBreaker(name="test", failure_threshold=2)
        
        def fail_func():
            raise Exception("Test error")
        
        # First failure
        with pytest.raises(Exception):
            cb.call(fail_func)
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count >= cb.failure_threshold
    
    def test_open_circuit_rejects_immediately(self):
        """Test that open circuit rejects calls immediately"""
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb.state = CircuitState.OPEN
        
        def any_func():
            return "should not execute"
        
        with pytest.raises(Exception) as exc_info:
            cb.call(any_func)
        
        assert "circuit is open" in str(exc_info.value).lower() or "circuit breaker" in str(exc_info.value).lower()
    
    def test_circuit_enters_half_open_after_timeout(self):
        """Test that circuit enters half-open state after recovery timeout"""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=1)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 2  # 2 seconds ago
        
        def success_func():
            return "success"
        
        # Should attempt reset and enter half-open
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN or cb.state == CircuitState.CLOSED
    
    def test_half_open_success_closes_circuit(self):
        """Test that successful call in half-open state closes circuit"""
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.state = CircuitState.HALF_OPEN
        cb.success_count = 0
        
        def success_func():
            return "success"
        
        # Multiple successes should close circuit
        for _ in range(3):
            result = cb.call(success_func)
            assert result == "success"
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

