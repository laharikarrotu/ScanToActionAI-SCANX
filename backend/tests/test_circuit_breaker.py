"""
Unit tests for circuit breaker module

This test suite verifies the CircuitBreaker class which provides:
- Circuit breaker pattern for external API resilience
- State management (CLOSED, OPEN, HALF_OPEN)
- Failure threshold detection
- Automatic recovery after timeout
- Prevents cascading failures

Each test function is documented with:
- Purpose: What it tests and why it's important for system resilience
- What it verifies: State transitions, failure handling, recovery logic
- Why it matters: Prevents overwhelming failing services, provides fast failure
- What to modify: Guidance if circuit breaker thresholds or recovery logic changes
"""
import pytest
import sys
import os
from datetime import datetime

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
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=100)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = datetime.now()  # Just failed, so recovery timeout not met
        
        def any_func():
            return "should not execute"
        
        with pytest.raises(Exception) as exc_info:
            cb.call(any_func)
        
        assert "circuit" in str(exc_info.value).lower() and "open" in str(exc_info.value).lower()
    
    def test_circuit_enters_half_open_after_timeout(self):
        """Test that circuit enters half-open state after recovery timeout"""
        from datetime import timedelta
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=1)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = datetime.now() - timedelta(seconds=2)  # 2 seconds ago (datetime, not float)
        
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

