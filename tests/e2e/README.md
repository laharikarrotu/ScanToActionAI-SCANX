# E2E Testing Suite

Comprehensive end-to-end testing for HealthScan using Playwright and pytest.

## Setup

```bash
# Install dependencies
pip install pytest pytest-asyncio playwright

# Install Playwright browsers
playwright install chromium

# Run tests
pytest tests/e2e/ -v
```

## Test Structure

- `test_full_pipeline.py`: Main test suite
  - Vision Engine tests
  - Planner Engine tests
  - Browser Executor tests
  - Prescription Extraction tests
  - Integration tests
  - API endpoint tests

## Running Tests

```bash
# Run all tests
pytest tests/e2e/

# Run specific test class
pytest tests/e2e/test_full_pipeline.py::TestVisionEngine

# Run with coverage
pytest tests/e2e/ --cov=backend --cov-report=html

# Run only fast tests (skip slow/integration)
pytest tests/e2e/ -m "not slow"
```

## Test Images

Place test images in `tests/e2e/test_images/`:
- `prescription.jpg`: Sample prescription for testing
- `medical_form.jpg`: Sample medical form
- `insurance_card.jpg`: Sample insurance card

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:
- GitHub Actions
- GitLab CI
- CircleCI

Add to your workflow:
```yaml
- name: Run E2E Tests
  run: |
    pip install -r backend/requirements.txt
    pip install pytest pytest-asyncio playwright
    playwright install chromium
    pytest tests/e2e/ -v
```

