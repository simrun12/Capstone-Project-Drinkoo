# DRINKOO Test Suite

## Overview
Comprehensive test suite for DRINKOO backend API, database layer, and validation logic.

## Test Structure

```
backend/tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_validators.py    # Input validation tests
├── test_database.py      # Database schema and integrity tests
├── test_auth.py          # Authentication utility tests
└── test_api_endpoints.py # FastAPI endpoint tests
```

## Test Categories

### Validators (`test_validators.py`)
- ✅ SKU size validation (1000ml, 1500ml only)
- ✅ Currency value validation (non-negative)
- ✅ Quantity validation (non-negative)
- ✅ Tracking code format validation
- ✅ Constants and configuration checks

**Markers:** `@pytest.mark.validators`

### Database (`test_database.py`)
- ✅ Schema creation for all tables
- ✅ Foreign key constraint enforcement
- ✅ State initialization (36 states/UTs)
- ✅ Admin user creation
- ✅ Query patterns (insert, retrieve, unique constraints)

**Markers:** `@pytest.mark.database`

### Authentication (`test_auth.py`)
- ✅ Valid credential acceptance (admin/password)
- ✅ Invalid credential rejection
- ✅ Empty/None credential handling
- ✅ Case sensitivity
- ✅ SQL injection prevention
- ✅ Whitespace padding handling

**Markers:** `@pytest.mark.auth`

### API Endpoints (`test_api_endpoints.py`)
- ✅ Login success/failure
- ✅ Authentication requirement
- ✅ States endpoint
- ✅ SKU CRUD operations
- ✅ SKU validation (size, price)
- ✅ Shipment operations
- ✅ Analytics endpoints
- ✅ Error handling (404, 400, 422)

**Markers:** `@pytest.mark.routes`

## Running Tests

### Prerequisites
```bash
pip install -r backend/requirements.txt
```

### Run All Tests
```bash
pytest backend/tests/ -v
```

### Run Specific Test Category

**Validators only:**
```bash
pytest backend/tests/ -v -m validators
```

**Database tests only:**
```bash
pytest backend/tests/ -v -m database
```

**Auth tests only:**
```bash
pytest backend/tests/ -v -m auth
```

**API route tests only:**
```bash
pytest backend/tests/ -v -m routes
```

### Run Specific Test File
```bash
pytest backend/tests/test_validators.py -v
```

### Run with Coverage Report
```bash
pytest backend/tests/ -v --cov=backend --cov-report=html
```

### Run Tests in Parallel
```bash
pytest backend/tests/ -v -n auto
```
(Requires: `pip install pytest-xdist`)

## Test Markers

| Marker | Purpose |
|--------|---------|
| `@pytest.mark.validators` | Input validation tests |
| `@pytest.mark.database` | Database schema/integrity tests |
| `@pytest.mark.auth` | Authentication tests |
| `@pytest.mark.routes` | API endpoint tests |
| `@pytest.mark.integration` | End-to-end tests |

## Fixtures

### Database Fixtures
- `test_db_path`: Temporary test database file
- `test_db_connection`: Connection to test database
- `initialized_test_db`: Test database with initialized schema

### Auth Fixtures
- `test_auth_token`: Bearer token for authenticated requests
- `auth_headers`: Headers dict with authorization token

### Data Fixtures
- `sample_sku_data`: Valid SKU creation payload
- `sample_shipment_data`: Valid shipment creation payload
- `client`: FastAPI TestClient

## Key Test Cases

### Business Rule Validation
```python
# SKU size must be 1000ml or 1500ml (not 1250ml)
assert is_valid_sku_size(1000) is True
assert is_valid_sku_size(1250) is False
```

### Security Testing
```python
# SQL injection protection
assert verify_development_login("admin' OR '1'='1", 'password') is None
```

### API Response Validation
```python
# Login endpoint returns token
response = client.post("/api/v1/auth/login", 
                       params={"username": "admin", "password": "password"})
assert response.status_code == 200
assert "access_token" in response.json()
```

## Coverage

Target coverage: **80%+**

Run coverage report:
```bash
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

## CI/CD Integration

For GitHub Actions or similar CI, use:
```bash
pytest backend/tests/ -v --junitxml=test-results.xml --cov=backend --cov-report=xml
```

## Troubleshooting

### Tests fail with ImportError
```bash
# Ensure you're in the drinkoo root directory
cd /path/to/drinkoo
pytest backend/tests/ -v
```

### Database tests fail
```bash
# Ensure pytest-sqlite is available
pip install pytest-sqlite
```

### TestClient fails to import FastAPI app
```bash
# Check that backend/main.py has no import errors
python -c "from backend.main import app; print('✓ App loads successfully')"
```

## Next Steps

1. Run full test suite: `pytest backend/tests/ -v`
2. Generate coverage report: `pytest backend/tests/ --cov=backend`
3. Fix any failing tests
4. Set up CI/CD pipeline for automated testing
5. Add more integration tests for critical workflows
