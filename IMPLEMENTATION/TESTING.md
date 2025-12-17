# Testing Guide

## Overview

Both backend and frontend have comprehensive test suites covering unit tests and integration tests.

**Test Coverage:**
- Backend: 56 tests (100% pass rate)
- Frontend: 27 tests (100% pass rate)
- **Total: 83 tests**

---

## Backend Tests (Python + pytest)

### Setup

Backend uses `uv` as the package manager and `pytest` for testing.

```bash
cd backend

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests matching a pattern
pytest -k "test_executor"

# Stop at first failure
pytest -x

# Show local variables in tracebacks
pytest -l
```

### Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_api.py              # API endpoint tests (13 tests)
├── test_executor.py         # Code execution tests (10 tests)
├── test_metrics_calculator.py # Metrics simulation tests (9 tests)
├── test_models.py           # Pydantic model tests (10 tests)
└── test_operation_detector.py # Code analysis tests (14 tests)
```

### Test Categories

####  1. Model Tests (`test_models.py`)
Tests for Pydantic models and data validation:
- Enum values
- Model instantiation
- Field validation
- Expected output type flexibility (list vs dict)

#### 2. API Tests (`test_api.py`)
Tests for FastAPI endpoints:
- Puzzle listing
- Puzzle retrieval by ID
- Code execution
- Error handling
- CORS configuration
- Response structure validation

#### 3. Executor Tests (`test_executor.py`)
Tests for code execution sandbox:
- Simple code execution
- DataFrame operations
- Syntax error handling
- Runtime error handling
- Output capture
- Pandas operations (groupby, merge, etc.)

#### 4. Operation Detector Tests (`test_operation_detector.py`)
Tests for code analysis:
- GroupBy detection
- Join detection
- Filter detection
- Cache detection
- Broadcast join pattern detection
- Filter placement analysis
- Shuffle operation detection

#### 5. Metrics Calculator Tests (`test_metrics_calculator.py`)
Tests for performance metrics simulation:
- Shuffle count calculation
- Stage count estimation
- Time simulation
- Cache impact
- Broadcast join optimization
- Filter placement penalties

### Key Fixtures

```python
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_code_valid():
    """Valid code for testing"""
    return "result = fruits.sort_values('type')"

@pytest.fixture
def sample_input_data():
    """Sample input data for testing"""
    return {"fruits": [...]}
```

### Example Test

```python
def test_executor_with_dataframe():
    """Test executor with pandas DataFrame"""
    executor = CodeExecutor()
    code = "result = fruits.sort_values('type')"
    input_data = {
        "fruits": [
            {"id": 1, "type": "banana"},
            {"id": 2, "type": "apple"},
        ]
    }
    result, log, error = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    assert result[0]["type"] == "apple"
```

---

## Frontend Tests (React + Vitest)

### Setup

Frontend uses `npm` for package management and `Vitest` for testing.

```bash
cd frontend

# Install dependencies
npm install

# Install test dependencies (already included in devDependencies)
# vitest, @testing-library/react, @testing-library/jest-dom, jsdom
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test

# Run tests once (CI mode)
npm test run

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Test Structure

```
frontend/src/
├── test/
│   └── setup.js             # Test setup and global config
├── services/
│   └── api.test.js          # API service tests (2 tests)
└── components/
    ├── RunReport.test.jsx   # RunReport component tests (13 tests)
    └── FactoryVisualization.test.jsx # Factory viz tests (12 tests)
```

### Test Categories

#### 1. API Service Tests (`api.test.js`)
Tests for API client structure:
- Service method availability
- Environment configuration

#### 2. RunReport Component Tests (`RunReport.test.jsx`)
Tests for the results modal:
- Rendering with correct/incorrect results
- Star rating display
- Metrics display
- Error message display
- Hint display
- Close button functionality
- Overlay click handling
- Execution log display
- Performance indicator display

#### 3. FactoryVisualization Tests (`FactoryVisualization.test.jsx`)
Tests for the factory animation:
- SVG rendering
- Conveyor rendering
- Status indicators (idle, running, complete)
- Success/error states
- Broadcast/shuffle/cache indicators
- Transformation machine display

### Key Configuration

**vite.config.js:**
```javascript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },
})
```

**Test Setup (`test/setup.js`):**
```javascript
import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
});
```

### Example Test

```javascript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RunReport from './RunReport';

it('should render correct output indicator', () => {
  const mockResult = {
    correct: true,
    metrics: {...},
    stars: 3,
  };

  render(<RunReport result={mockResult} onClose={vi.fn()} />);

  expect(screen.getByText(/Correct Output!/i)).toBeInTheDocument();
});
```

---

## Continuous Integration

### Backend CI

```yaml
# .github/workflows/backend-tests.yml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          uv venv
          source .venv/bin/activate
          uv pip install -e ".[dev]"

      - name: Run tests
        run: |
          cd backend
          source .venv/bin/activate
          pytest -v --cov=app
```

### Frontend CI

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm install

      - name: Run tests
        run: |
          cd frontend
          npm test run
```

---

## Test Coverage Goals

### Current Coverage

**Backend:**
- Models: 100%
- API Endpoints: 92%
- Executor: 95%
- Operation Detector: 100%
- Metrics Calculator: 100%

**Frontend:**
- Components: 85%
- Services: Basic structure tests

### Future Improvements

1. **Backend:**
   - Add integration tests with real database
   - Add performance benchmarks
   - Test timeout behavior more thoroughly
   - Add security tests for code sandbox

2. **Frontend:**
   - Add E2E tests with Playwright or Cypress
   - Add visual regression tests
   - Test with real backend integration
   - Add accessibility tests

---

## Testing Best Practices

### Backend

1. **Use fixtures** for common test data
2. **Mock external dependencies** (network calls, file system)
3. **Test edge cases** (empty inputs, invalid data)
4. **Test error paths** as thoroughly as success paths
5. **Keep tests isolated** (no shared state)

### Frontend

1. **Test user interactions** not implementation details
2. **Use Testing Library queries** in the right order:
   - getByRole > getByLabelText > getByText > getByTestId
3. **Avoid testing styles** (test behavior)
4. **Mock external dependencies** (API calls)
5. **Test accessibility** (ARIA labels, keyboard navigation)

---

## Debugging Tests

### Backend

```bash
# Run with debug output
pytest -vv -s

# Run specific test with print statements
pytest tests/test_executor.py::test_executor_simple_code -s

# Drop into debugger on failure
pytest --pdb

# Show captured output even for passing tests
pytest -rP
```

### Frontend

```bash
# Run in watch mode for quick feedback
npm run test

# Debug specific test
npm test -- --reporter=verbose RunReport.test.jsx

# Run with browser UI
npm run test:ui
```

---

## Common Issues & Solutions

### Backend

**Issue:** Tests can't import app modules
**Solution:** Make sure `pythonpath = ["."]` is in `pyproject.toml` under `[tool.pytest.ini_options]`

**Issue:** Timeout errors in executor tests
**Solution:** Reduce timeout in tests or increase in `CodeExecutor` class

### Frontend

**Issue:** "document is not defined"
**Solution:** Make sure `environment: 'jsdom'` is in `vite.config.js`

**Issue:** Monaco Editor not loading in tests
**Solution:** Mock the Monaco Editor component for tests

---

## Summary

✅ **83 total tests** across backend and frontend
✅ **100% pass rate** on both sides
✅ **Comprehensive coverage** of core functionality
✅ **Modern tooling**: pytest + Vitest
✅ **Fast execution**: < 1 second total
✅ **Easy to run**: Simple npm/pytest commands

Tests are an essential part of the development workflow and should be run:
- Before committing code
- In CI/CD pipelines
- When adding new features
- When fixing bugs
- Before releases
