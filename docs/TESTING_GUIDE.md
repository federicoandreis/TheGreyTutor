# Testing Guide - The Grey Tutor

**Last Updated:** January 1, 2026
**Branch:** `test/infrastructure-setup`
**Status:** ✅ Testing Infrastructure Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Quick Start](#quick-start)
4. [Frontend Testing](#frontend-testing)
5. [Backend Testing](#backend-testing)
6. [Writing Tests](#writing-tests)
7. [Running Tests](#running-tests)
8. [Coverage Reports](#coverage-reports)
9. [CI/CD Integration](#cicd-integration)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Grey Tutor uses a comprehensive testing strategy across frontend and backend:

| Layer | Framework | Current Coverage | Target |
|-------|-----------|------------------|--------|
| Frontend | Jest + React Native Testing Library | ~68% (37/54 tests passing) | 70%+ |
| Backend | pytest + FastAPI TestClient | ✅ 100% (25/25 tests passing) | 70%+ |

**Test Distribution:**
- **Unit Tests:** 70% - Individual functions and components
- **Integration Tests:** 20% - API endpoints, service interactions
- **E2E Tests:** 10% - Full user flows (future)

---

## Testing Philosophy

### Our Principles

1. **Test Behavior, Not Implementation**
   - Focus on what the code does, not how it does it
   - Example: Test that a button navigates, not that it calls `navigate()`

2. **Mandatory Testing for New Code**
   - All new features require tests
   - All bug fixes require regression tests
   - Target: 70%+ coverage for new code

3. **Fast, Reliable, Isolated**
   - Tests should run in <10 seconds
   - No test should depend on another
   - Use mocks for external dependencies

4. **Clear, Descriptive Test Names**
   ```typescript
   // ✅ Good
   it('displays error message when login fails with invalid credentials')

   // ❌ Bad
   it('test login')
   ```

---

## Quick Start

### Run All Tests

```powershell
# Frontend tests
cd thegreytutor/frontend
npm test

# Backend tests
cd thegreytutor/backend
python -m pytest

# Or from project root
npm run test:all  # (if configured)
```

### Run Specific Tests

```powershell
# Frontend - specific test file
cd thegreytutor/frontend
npm test -- RegionMarker.test.tsx

# Backend - specific test file
cd thegreytutor/backend
python -m pytest tests/test_auth.py

# Backend - specific test function
python -m pytest tests/test_auth.py::TestAuthService::test_password_hashing
```

---

## Frontend Testing

### Setup

**Framework:** Jest 29.7.0 + React Native Testing Library 13.3.3

**Configurations:**
- **Unit Tests:** [`jest.config.unit.js`](../thegreytutor/frontend/jest.config.unit.js) + [`jest.setup.unit.js`](../thegreytutor/frontend/jest.setup.unit.js)
- **Integration Tests:** [`jest.config.integration.js`](../thegreytutor/frontend/jest.config.integration.js) + [`jest.setup.integration.js`](../thegreytutor/frontend/jest.setup.integration.js)

### Dual Testing Strategy

The frontend uses **two separate test configurations**:

#### 1. **Unit Tests** (Fast, Isolated)
- **Purpose:** Test individual components and functions in isolation
- **Mocking:** Full mocks for all external dependencies (authApi, navigation, etc.)
- **Speed:** Very fast (<10 seconds)
- **File naming:** `*.test.ts` or `*.test.tsx` (excludes `*.integration.test.*`)
- **Run with:** `npm run test:unit`

#### 2. **Integration Tests** (Realistic, E2E)
- **Purpose:** Test API integration with real backend
- **Mocking:** Minimal mocks (only UI-specific: image picker, navigation)
- **Speed:** Slower (30 second timeout per test)
- **Requirements:** Backend must be running at `http://localhost:8000`
- **File naming:** `*.integration.test.ts` or `*.integration.test.tsx`
- **Run with:** `npm run test:integration`

### Test Structure

```
thegreytutor/frontend/
├── __tests__/
│   ├── components/
│   │   └── journey/
│   │       └── RegionMarker.test.tsx                    ✅ 10/10 unit tests passing
│   ├── screens/
│   │   ├── journey/
│   │   │   └── MapScreen.test.tsx                       ✅ 7/7 unit tests passing
│   │   └── profile/
│   │       └── EditProfileScreen.test.tsx               (needs update)
│   └── services/
│       ├── journeyApi.unit.test.ts                      ✅ 14/14 unit tests passing
│       └── journeyApi.integration.test.ts               ✅ Integration tests ready
│
├── jest.config.unit.js              # Unit test configuration
├── jest.config.integration.js       # Integration test configuration
├── jest.setup.unit.js               # Unit test mocks
└── jest.setup.integration.js        # Integration test minimal mocks
```

### Running Frontend Tests

```powershell
cd thegreytutor/frontend

# Run UNIT tests only (fast, mocked)
npm run test:unit

# Run INTEGRATION tests only (slow, real backend required)
npm run test:integration

# Run ALL tests (unit + integration)
npm run test:all

# Run unit tests in watch mode
npm run test:watch

# Run unit tests with coverage
npm run test:coverage

# Run specific unit test file
npm run test:unit -- journeyApi.unit.test.ts

# Run specific integration test file
npm run test:integration -- journeyApi.integration.test.ts
```

### Frontend Test Example

```typescript
// __tests__/components/journey/RegionMarker.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { RegionMarker } from '../../../src/components/journey/RegionMarker';

describe('RegionMarker', () => {
  const mockOnPress = jest.fn();

  const baseRegion: RegionStatus = {
    name: 'shire',
    display_name: 'The Shire',
    difficulty_level: 'beginner',
    is_unlocked: true,
    // ... other properties
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with unlocked region', () => {
    const { getByText } = render(
      <RegionMarker
        region={baseRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('calls onPress with region name when pressed', () => {
    const { getByTestId } = render(
      <RegionMarker region={baseRegion} onPress={mockOnPress} isCurrentRegion={false} />
    );

    const marker = getByTestId('region-marker-shire');
    fireEvent.press(marker);

    expect(mockOnPress).toHaveBeenCalledWith('shire');
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });
});
```

### Unit vs Integration Test Examples

#### Unit Test Example (Mocked)

```typescript
// __tests__/services/journeyApi.unit.test.ts
import { journeyApi } from '../../src/services/journeyApi';
import { authApi } from '../../src/services/authApi';

// authApi is already mocked by jest.setup.unit.js
const mockAuthenticatedFetch = authApi.authenticatedFetch as jest.MockedFunction<
  typeof authApi.authenticatedFetch
>;

describe('JourneyApi Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches journey state successfully', async () => {
    const mockJourneyState = {
      current_region: 'shire',
      knowledge_points: 150,
      unlocked_regions: ['shire', 'bree'],
      // ... rest of state
    };

    // Mock the fetch response
    mockAuthenticatedFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockJourneyState,
    } as Response);

    const result = await journeyApi.getJourneyState();

    expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/journey/state')
    );
    expect(result).toEqual(mockJourneyState);
  });
});
```

**Characteristics:**
- ✅ Very fast (runs in milliseconds)
- ✅ No backend required
- ✅ Tests logic in isolation
- ❌ Doesn't catch API contract changes
- ❌ Doesn't test real network behavior

#### Integration Test Example (Real Backend)

```typescript
// __tests__/services/journeyApi.integration.test.ts
import { journeyApi } from '../../src/services/journeyApi';
import { authApi } from '../../src/services/authApi';

describe('Journey API Integration Tests', () => {
  let testToken: string;

  beforeAll(async () => {
    // Register a REAL test user
    const registerResponse = await authApi.register({
      email: `test-${Date.now()}@example.com`,
      password: 'TestPassword123',
      username: `testuser${Date.now()}`,
    });
    testToken = registerResponse.tokens.access_token;
  });

  it('should fetch the user journey state from backend', async () => {
    // This makes a REAL API call to http://localhost:8000
    const state = await journeyApi.getJourneyState();

    expect(state).toBeDefined();
    expect(state.current_region).toBeDefined();
    expect(state.knowledge_points).toBeGreaterThanOrEqual(0);
    expect(Array.isArray(state.unlocked_regions)).toBe(true);
  });
});
```

**Characteristics:**
- ✅ Tests real API behavior
- ✅ Catches API contract changes
- ✅ Tests full request/response cycle
- ❌ Slower (30 second timeout)
- ❌ Requires backend running
- ❌ Can be flaky (network issues)

### When to Use Each Type

| Use Unit Tests For | Use Integration Tests For |
|--------------------|---------------------------|
| Component rendering logic | API endpoint validation |
| State management | Authentication flows |
| Utility functions | Data persistence |
| UI interactions | Error handling with real backend |
| Fast feedback loop | Pre-deployment verification |

### Common Frontend Test Patterns

#### Testing Components
```typescript
import { render, screen } from '@testing-library/react-native';

it('renders component correctly', () => {
  const { getByText } = render(<MyComponent />);
  expect(getByText('Expected Text')).toBeTruthy();
});
```

#### Testing User Interactions
```typescript
import { fireEvent } from '@testing-library/react-native';

it('handles button press', () => {
  const onPress = jest.fn();
  const { getByTestId } = render(<Button onPress={onPress} testID="my-button" />);

  fireEvent.press(getByTestId('my-button'));
  expect(onPress).toHaveBeenCalled();
});
```

#### Testing Async Behavior
```typescript
import { waitFor } from '@testing-library/react-native';

it('loads data asynchronously', async () => {
  const { getByText } = render(<DataComponent />);

  await waitFor(() => {
    expect(getByText('Loaded Data')).toBeTruthy();
  });
});
```

#### Mocking API Calls
```typescript
jest.mock('../services/authApi', () => ({
  authApi: {
    login: jest.fn(() => Promise.resolve({ success: true })),
  },
}));
```

### Current Frontend Test Status

**Unit Tests:**
- ✅ `RegionMarker.test.tsx` - 10/10 tests passing
- ✅ `MapScreen.test.tsx` - 7/7 tests passing
- ✅ `journeyApi.unit.test.ts` - 14/14 tests passing (NEW!)
- ⚠️ `EditProfileScreen.test.tsx` - 3/10 tests (needs update to use new mocks)

**Integration Tests:**
- ✅ `journeyApi.integration.test.ts` - Ready (requires backend running)

**Overall Progress:**
- Unit Tests: 31/41 passing (75.6%)
- Integration Tests: Infrastructure complete, tests ready to run
- Old failing tests replaced with new dual-test strategy

**Next Steps:**
1. Update `EditProfileScreen.test.tsx` to use new unit test mocks
2. Run integration tests against live backend
3. Add more integration tests for other API services

---

## Backend Testing

### Setup

**Framework:** pytest 8.3.4 + FastAPI TestClient

**Configuration:** [`thegreytutor/backend/pytest.ini`](../thegreytutor/backend/pytest.ini)

### Test Structure

```
thegreytutor/backend/
├── tests/
│   ├── __init__.py
│   ├── test_auth.py                        ✅ 25/25 passing
│   ├── agents/
│   │   ├── test_journey_agent.py
│   │   └── test_journey_agent_simplified.py
│   └── api/
│       └── test_journey_routes.py
├── pytest.ini
└── requirements.txt
```

### Running Backend Tests

```powershell
cd thegreytutor/backend

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_auth.py

# Run specific test class
python -m pytest tests/test_auth.py::TestAuthService

# Run specific test function
python -m pytest tests/test_auth.py::TestAuthService::test_password_hashing

# Run tests matching pattern
python -m pytest -k "auth"

# Run only unit tests (with marker)
python -m pytest -m unit

# Run tests except slow ones
python -m pytest -m "not slow"
```

### Backend Test Example

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override."""
    from src.main import app
    from src.database.connection import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

class TestAuthEndpoints:
    def test_register_success(self, client, test_db):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == "testuser"
        assert "access_token" in data["tokens"]
```

### Common Backend Test Patterns

#### Testing Service Functions
```python
def test_password_hashing():
    """Test that passwords are properly hashed."""
    from src.services.auth_service import auth_service

    password = "TestPassword123"
    hashed = auth_service.hash_password(password)

    assert hashed != password
    assert auth_service.verify_password(password, hashed) is True
```

#### Testing API Endpoints
```python
def test_api_endpoint(client):
    """Test API endpoint returns correct data."""
    response = client.get("/api/endpoint")

    assert response.status_code == 200
    data = response.json()
    assert "expected_key" in data
```

#### Testing with Authentication
```python
def test_protected_endpoint(client):
    """Test protected endpoint requires authentication."""
    # Register and get token
    register_response = client.post("/auth/register", json={"username": "test", ...})
    token = register_response.json()["tokens"]["access_token"]

    # Access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
```

#### Testing Database Operations
```python
def test_database_operation(test_db):
    """Test database create and read."""
    from database.models.user import User

    user = User(username="test", email="test@example.com")
    test_db.add(user)
    test_db.commit()

    retrieved = test_db.query(User).filter_by(username="test").first()
    assert retrieved is not None
    assert retrieved.email == "test@example.com"
```

### Current Backend Test Status

**Passing Tests (25/25):**
- ✅ `test_auth.py` - All authentication tests passing
  - Password hashing and verification
  - Access token creation and validation
  - Refresh token creation and validation
  - User registration (success, duplicate email, duplicate username, weak password)
  - User login (success, wrong password, nonexistent user)
  - Current user retrieval
  - Token refresh
  - Password change
  - Profile updates (full, partial, validation)

**Warnings:** 148 deprecation warnings (datetime.utcnow() usage - non-critical)

---

## Writing Tests

### Test File Naming

- **Frontend:** `*.test.tsx` or `*.test.ts`
- **Backend:** `test_*.py` or `*_test.py`

### Test Organization

```python
# Group related tests in classes
class TestUserAuthentication:
    def test_successful_login(self):
        pass

    def test_failed_login_wrong_password(self):
        pass

    def test_failed_login_nonexistent_user(self):
        pass
```

### Test Naming Convention

```
test_[what]_[condition]_[expected_result]
```

Examples:
- `test_login_with_valid_credentials_succeeds`
- `test_registration_with_duplicate_email_fails`
- `test_region_marker_when_locked_displays_lock_icon`

### Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange - Set up test data
    user = create_test_user()

    # Act - Perform the action
    result = login(user.email, "password")

    # Assert - Check the outcome
    assert result.success is True
```

---

## Coverage Reports

### Generate Coverage Reports

**Frontend:**
```powershell
cd thegreytutor/frontend
npm test -- --coverage
# Report saved to: coverage/lcov-report/index.html
```

**Backend:**
```powershell
cd thegreytutor/backend
python -m pytest --cov=src --cov-report=html
# Report saved to: htmlcov/index.html
```

### View Coverage Reports

```powershell
# Frontend
start coverage/lcov-report/index.html

# Backend
start htmlcov/index.html
```

### Coverage Targets

- **New Features:** 70%+ coverage required
- **Critical Paths:** 90%+ coverage (auth, payments, data loss)
- **Overall Project:** Target 70%+

---

## CI/CD Integration

### GitHub Actions Workflow (Future)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd thegreytutor/frontend && npm install --legacy-peer-deps
      - run: cd thegreytutor/frontend && npm test -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          file: ./thegreytutor/frontend/coverage/lcov.info

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: cd thegreytutor/backend && pip install -r requirements.txt
      - run: cd thegreytutor/backend && python -m pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          file: ./thegreytutor/backend/coverage.xml
```

---

## Troubleshooting

### Frontend Test Issues

#### "jest is not recognized"
```powershell
# Solution: Install dependencies
cd thegreytutor/frontend
npm install --legacy-peer-deps
```

#### "Cannot find module 'react-native-worklets'"
```powershell
# Solution: Install worklets
npm install --save-dev react-native-worklets --legacy-peer-deps
```

#### Tests fail with "Cannot read properties of undefined"
```javascript
// Solution: Add proper mocks in jest.setup.js
jest.mock('../services/authApi', () => ({
  authApi: {
    authenticatedFetch: jest.fn(),
    login: jest.fn(),
  },
}));
```

### Backend Test Issues

#### "ModuleNotFoundError: No module named 'pytest'"
```powershell
# Solution: Install pytest
cd thegreytutor/backend
pip install pytest pytest-cov pytest-asyncio
```

#### "ImportError: attempted relative import"
```powershell
# Solution: Run tests as module from backend directory
cd thegreytutor/backend
python -m pytest  # NOT: python tests/test_auth.py
```

#### Database connection errors
```python
# Solution: Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

---

## Test Checklist for PRs

Before submitting a pull request:

- [ ] All tests pass locally (`npm test` and `python -m pytest`)
- [ ] New code has tests (70%+ coverage)
- [ ] Test names are descriptive
- [ ] No commented-out tests
- [ ] No `console.log` or `print` statements (except in actual code)
- [ ] Mocks are properly cleaned up (`jest.clearAllMocks()`, `@pytest.fixture`)
- [ ] Tests are fast (< 10 seconds total)
- [ ] Coverage report reviewed (no major gaps)

---

## Next Steps

### Immediate (This PR)
- ✅ Frontend test infrastructure set up
- ✅ Backend test infrastructure set up
- ✅ pytest configuration created
- ✅ Documentation written
- ⏳ Update README files

### Short Term (Next PRs)
- [ ] Fix failing frontend tests (auth mocks)
- [ ] Add tests for Journey Agent
- [ ] Add tests for Quiz Service
- [ ] Increase coverage to 70%+

### Long Term
- [ ] Set up CI/CD with GitHub Actions
- [ ] Add E2E tests with Maestro/Detox
- [ ] Add performance tests
- [ ] Add visual regression tests

---

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Native Testing Library](https://callstack.github.io/react-native-testing-library/)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://testingjavascript.com/)

---

**Version:** 1.0
**Author:** The Grey Tutor Team
**Last Updated:** January 1, 2026
