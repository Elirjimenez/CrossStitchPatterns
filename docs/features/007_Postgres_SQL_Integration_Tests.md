# Plan: PostgreSQL Integration Tests

## Context

The current integration tests use SQLite in-memory, which is fast but doesn't validate real Postgres behavior (JSONB storage, native FK enforcement, CASCADE deletes, timezone handling). Adding 8-9 tests against real Postgres strengthens the TFM's technical credibility.

## Changes

### 1. Register `postgres` marker in `pyproject.toml`

Add `markers` to `[tool.pytest.ini_options]` so `pytest -m postgres` works without warnings.

### 2. Fix ORM/migration mismatch in `pattern_result_model.py`

**Line 13**: Add `ondelete="CASCADE"` to `ForeignKey("projects.id", ondelete="CASCADE")` so the ORM matches the Alembic migration. Without this, `Base.metadata.create_all()` creates the FK without CASCADE, and the CASCADE test would fail.

### 3. Create `tests/integration/conftest.py` — Postgres fixtures

- `_postgres_is_available()` — probes `postgresql://user:pass@localhost:5432/crossstitch` once at import time
- `pg_engine` (session-scoped) — creates engine, calls `pytest.skip()` if Postgres is down
- `pg_session` (function-scoped) — `drop_all` / `create_all` per test for clean isolation, yields session, drops tables in cleanup
- `pg_project_repo`, `pg_pattern_repo` — wrappers over `pg_session`

**Why drop_all/create_all per test?** We need real commits to validate FK constraints and CASCADE. Transaction rollback would hide commit-time constraint violations.

### 4. Create `tests/integration/test_postgres_repositories.py` — 8-9 tests

All tests marked with `pytestmark = pytest.mark.postgres`.

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_add_and_get_project` | Basic insert + retrieve on Postgres |
| 2 | `test_list_all_returns_projects` | Multi-row list query |
| 3 | `test_update_status` | Status update persists correctly |
| 4 | `test_project_parameters_jsonb_roundtrip` | Complex nested dict survives JSON/JSONB |
| 5 | `test_pattern_result_palette_jsonb_roundtrip` | Palette dict roundtrip |
| 6 | `test_fk_rejects_orphan_pattern_result` | FK prevents insert with bad project_id |
| 7 | `test_cascade_delete_removes_pattern_results` | Deleting project cascades to children |
| 8 | `test_get_latest_returns_most_recent` | ORDER BY created_at DESC works on Postgres |
| 9 | `test_get_latest_returns_none_when_empty` | Edge case: no results |

## Files Modified

| File | Action |
|------|--------|
| `pyproject.toml` | Add `markers` list (2 lines) |
| `app/infrastructure/persistence/models/pattern_result_model.py` | Add `ondelete="CASCADE"` to FK |
| `tests/integration/conftest.py` | **New** — Postgres fixtures (~50 lines) |
| `tests/integration/test_postgres_repositories.py` | **New** — 9 tests (~170 lines) |

## How to Run

```bash
# Start Postgres
docker compose -f docker/docker-compose.yml up -d db

# Run only Postgres tests
pytest -m postgres -v

# Run all tests (Postgres tests skip if DB is down)
pytest -v

# Run everything except Postgres
pytest -m "not postgres" -v
```

## Verification

1. With Docker Postgres running: `pytest -m postgres -v` — all 9 tests pass
2. Without Postgres: `pytest -v` — Postgres tests show as SKIPPED, other 212 tests pass
3. `black app/ tests/` — no formatting issues
