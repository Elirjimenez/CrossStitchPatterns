# PostgreSQL Integration Testing

This guide explains how to run integration tests against a real PostgreSQL database.

## Why PostgreSQL Tests?

SQLite-based tests don't validate:
- **JSONB storage** (PostgreSQL-specific column type)
- **Foreign key cascade deletes** (different behavior)
- **Timezone-aware datetimes** (PostgreSQL native support)
- **SQL dialect differences** (query compatibility)
- **Real infrastructure behavior** (connection pooling, transactions)

## Quick Start

### 1. Start Test Database

The postgres tests connect to a **dedicated test database on port 5433**, separate from the
development database on port 5432. Even if the dev database is already running you must
start this container — the two do not interfere.

```bash
# Start the test database and wait until healthy
docker-compose -f docker/docker-compose.test.yml up -d --wait
```

### 2. Run PostgreSQL Tests

```bash
# Run all PostgreSQL-marked tests
pytest -m postgres -v

# Run specific test file
pytest tests/integration/test_database_operations.py -v

# Run with coverage
pytest -m postgres --cov=app --cov-report=html
```

### 3. Stop Test Database

```bash
# Stop and remove test database
docker-compose -f docker/docker-compose.test.yml down

# Stop and remove with volume cleanup
docker-compose -f docker/docker-compose.test.yml down -v
```

## Test Files

### Database Operation Smoke Tests
**File**: `tests/integration/test_database_operations.py`

Validates core database operations:
- ✅ Connection and schema creation
- ✅ Project CRUD operations
- ✅ PatternResult CRUD operations
- ✅ Transaction handling (commit/rollback)
- ✅ JSONB storage and retrieval
- ✅ Foreign key constraints
- ✅ Cascade deletes
- ✅ End-to-end workflow

### Repository Implementation Tests
**File**: `tests/integration/test_postgres_repositories.py`

Tests PostgreSQL-specific repository behavior:
- ✅ JSONB round-trips (complex nested data)
- ✅ Foreign key enforcement
- ✅ CASCADE DELETE behavior
- ✅ Timezone-aware datetime handling
- ✅ Query ordering and filtering

## Configuration

### Environment Variables

```bash
# Override default PostgreSQL URL
export DATABASE_URL_TEST="postgresql://user:pass@localhost:5433/crossstitch_test"

# Then run tests
pytest -m postgres -v
```

### Test Database Configuration

**Default**: `postgresql://user:pass@localhost:5433/crossstitch_test`

- **Host**: localhost
- **Port**: 5433 (to avoid conflict with dev DB on 5432)
- **Database**: crossstitch_test
- **User**: user
- **Password**: pass

## Continuous Integration

### GitHub Actions

Add PostgreSQL service to CI workflow:

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: crossstitch_test
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

steps:
  - name: Run PostgreSQL tests
    env:
      DATABASE_URL_TEST: postgresql://user:pass@localhost:5432/crossstitch_test
    run: pytest -m postgres -v
```

## Test Markers

Tests are marked with `@pytest.mark.postgres`:

```python
pytestmark = pytest.mark.postgres  # Mark entire file

@pytest.mark.postgres  # Mark individual test
def test_something(pg_session):
    ...
```

Run only PostgreSQL tests:
```bash
pytest -m postgres
```

Run everything EXCEPT PostgreSQL tests:
```bash
pytest -m "not postgres"
```

## Automatic Skip

If the test database on port 5433 is not reachable, the postgres tests skip automatically
so the rest of the suite can still run:

```
tests/integration/test_database_operations.py::test_can_connect SKIPPED
[reason: PostgreSQL is not available]
```

This means a plain `pytest` run (without the test container) reports **549 passed, 24 skipped**.
Start the test container and run `pytest -m postgres` (or the full `pytest`) to get **573 passed, 0 skipped**.

## Troubleshooting

### Database Connection Refused

```bash
# Check if container is running
docker ps | grep crossstitch-test-db

# Check container logs
docker logs crossstitch-test-db

# Restart container
docker-compose -f docker/docker-compose.test.yml restart
```

### Port Already in Use

If port 5433 is already in use:

1. Edit `docker/docker-compose.test.yml` and change the port mapping
2. Update `DATABASE_URL_TEST` environment variable accordingly

### Schema Issues

```bash
# Drop and recreate test database
docker-compose -f docker/docker-compose.test.yml down -v
docker-compose -f docker/docker-compose.test.yml up -d
```

## Best Practices

1. **Always use test database**: Never run tests against production database
2. **Clean state**: Each test gets a fresh schema (drop/create)
3. **Isolated tests**: Tests should not depend on each other
4. **Fast feedback**: Use SQLite for unit tests, PostgreSQL for integration tests
5. **CI/CD**: Run PostgreSQL tests in CI pipeline before merging

## Performance

- **SQLite tests**: ~2 seconds (in-memory, no setup)
- **PostgreSQL tests**: ~5-10 seconds (Docker startup + schema creation)

**Recommendation**: Use SQLite for TDD red-green-refactor cycle, run PostgreSQL tests before committing.
