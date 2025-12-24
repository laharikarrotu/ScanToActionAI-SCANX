# Test Suite Overview

## Philosophy: Fail Fast, Not Skip

**Core Principle**: Unit tests for core business logic should **FAIL** if dependencies are missing, not skip gracefully.

### Why Fail Instead of Skip?

1. **Core Business Logic Must Work**: If encryption, PII redaction, or error handling can't be tested, the application is broken.
2. **Dependencies Are Required**: If a dependency is in `requirements.txt`, it MUST be installed for tests to pass.
3. **Catch Problems Early**: Failing tests immediately show when dependencies are missing or broken.
4. **CI/CD Integration**: Failed tests block deployments, ensuring production readiness.

### When to Skip vs Fail

#### ✅ **FAIL** (use `pytest.fail()`) for:
- **Core dependencies** listed in `requirements.txt`:
  - `cryptography` (encryption - HIPAA requirement)
  - Core business logic methods (PII detection, error handling)
  - Security features (error sanitization)

#### ⚠️ **SKIP** (use `pytest.skip()`) for:
- **Optional dependencies** with fallbacks:
  - Redis (cache has memory fallback)
  - Sentry (monitoring - optional)
  - External services (only in integration tests)

### Test Categories

1. **Unit Tests** - Test core business logic in isolation
   - Must have all dependencies installed
   - Should FAIL if core dependencies missing
   - Fast execution (< 1 second per test)

2. **Integration Tests** - Test API endpoints and module interactions
   - May require external services
   - Can skip if services unavailable (with clear message)

3. **E2E Tests** - Test complete user flows
   - Require full stack running
   - Can skip if services unavailable

## Running Tests

```bash
# Unit tests (must pass - core business logic)
pytest tests/test_error_handler.py tests/test_pii_redaction.py tests/test_encryption.py tests/test_circuit_breaker.py tests/test_cache.py tests/test_rate_limiter.py -v

# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html
```

## Test Requirements

All unit tests require:
- Python 3.11+
- All packages from `requirements.txt` installed
- Core dependencies available (cryptography, etc.)

If tests fail with "CRITICAL: dependency not found", install missing dependencies:
```bash
pip install -r requirements.txt
```

## Documentation

See `docs/tests/TEST_DOCUMENTATION.md` for detailed documentation of each test function.

