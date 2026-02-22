# Persistence Layer Implementation Plan
## Cross-Stitch Pattern Generator (TFM)

### Goal
Implement a Postgres-backed persistence layer (running in Docker) and a local file storage adapter, while strictly preserving Clean Architecture principles and using Test-Driven Development (TDD).

This feature will persist **project and pattern metadata only** (no binary blobs in the DB), using Postgres JSONB fields for flexible parameters and palettes.

---

## Architectural Constraints (Non-Negotiable)

- `domain/` and `application/` MUST NOT depend on:
  - SQLAlchemy
  - Alembic
  - psycopg
  - FastAPI
  - Docker or environment variables
- Persistence must be implemented via **ports and adapters**
- Domain entities MUST be independent from ORM models
- Mapping between ORM models and domain entities must be explicit
- Tests must be split into:
  - Unit tests (in-memory fakes, no DB)
  - Integration tests (real Postgres via Docker)

---

## Technology Decisions (Final)

- Web framework: **FastAPI (sync)**
- Database: **PostgreSQL**
- ORM: **SQLAlchemy 2.0 (sync)**
- Driver: **psycopg3**
- Migrations: **Alembic**
- Storage: **Local filesystem (paths only)**
- DB fields for flexible data: **JSONB**
- Project lifecycle: **explicit project status**
- Test DB: **docker-compose Postgres**

---

## Domain Model Decisions

### Aggregate Root
- **Project** is the aggregate root

### Entities

#### Project
- `id`
- `name`
- `created_at`
- `status` (enum)
- `source_image_ref` (file path / ref)
- `parameters` (dict → JSONB)

#### Pattern
- `id`
- `project_id`
- `created_at`
- `palette` (dict → JSONB)
- `grid_width`
- `grid_height`
- `stitch_count`
- `pdf_ref` (file path / ref)
- `processing_mode` (str: `"auto"` | `"photo"` | `"drawing"` | `"pixel_art"`)
- `variant` (str: `"color"` | `"bw"`)

### Explicitly Out of Scope
- Binary blobs in DB (images / PDFs)
- User management / authentication
- Versioned patterns
- Cloud storage

---

## Recommended Delivery Strategy

**Do NOT implement persistence as one big change.**  
Split it into **vertical slices**, each independently testable and reviewable.

---

## Slice 1 — Domain Entities and Repository Ports

### Deliverables
- Domain entities:
  - `Project`
  - `Pattern`
- Domain enum:
  - `ProjectStatus`
- Repository interfaces (ports):
  - `ProjectRepository`
    - `add(project)`
    - `get(project_id)`
    - `list()`
    - `update_status(project_id, status)`
  - `PatternRepository`
    - `add(pattern)`
    - `list_by_project(project_id)`
    - `get_latest_by_project(project_id)`

### Tests
- Domain unit tests (only invariants if present)

### Definition of Done
- Domain layer compiles
- No infrastructure imports
- Tests green

---

## Slice 2 — Application Use Cases + Unit Tests

### Deliverables
- Use cases:
  - `CreateProject`
  - `GetProject`
  - `ListProjects`
  - `UpdateProjectStatus`
  - `SavePatternResult`
  - `GetLatestPatternByProject`
- In-memory repositories for tests:
  - `InMemoryProjectRepository`
  - `InMemoryPatternRepository`

### Tests
- Unit tests for all use cases
- No DB, no SQLAlchemy, no Docker

### Definition of Done
- All business logic covered by unit tests
- Use cases depend only on repository interfaces

---

## Slice 3 — Local File Storage Adapter

### Deliverables
- Storage port interface:
  - `FileStorage`
    - `save_source_image(project_id, bytes, extension) -> ref`
    - `save_pdf(project_id, bytes, filename) -> ref`
- Infrastructure implementation:
  - `LocalFileStorage`
- Deterministic folder structure, e.g.:
  - `storage/projects/{project_id}/source.png`
  - `storage/projects/{project_id}/pattern_latest.pdf`

### Tests
- Unit tests using temporary directories

### Definition of Done
- Files saved correctly
- Returned refs can be persisted
- No DB involved

---

## Slice 4 — Postgres Docker Setup + DB Infrastructure

### Deliverables
- `docker-compose.yml`:
  - Postgres service
  - Healthcheck
  - Persistent volume
- Environment configuration:
  - `DATABASE_URL`
- Infrastructure DB setup:
  - SQLAlchemy engine
  - Session factory / Unit of Work
- Alembic initialized and wired to DB

### Definition of Done
- Postgres runs locally in Docker
- Alembic migrations execute successfully

---

## Slice 5 — ORM Models, Mapping, and Migrations

### Deliverables
- ORM models (separate from domain):
  - `ProjectModel`
  - `PatternModel`
- Explicit mapping layer:
  - `ProjectMapper`
  - `PatternMapper`
- Alembic migration:
  - Tables
  - Foreign keys
  - JSONB fields
  - Project status column

### Definition of Done
- Schema fully migrated
- Mapping tested manually or via integration tests

---

## Slice 6 — Postgres Repository Adapters + Integration Tests

### Deliverables
- Infrastructure repositories:
  - `SqlAlchemyProjectRepository`
  - `SqlAlchemyPatternRepository`
- Integration tests:
  - CRUD operations
  - JSONB round-trip
  - Status updates
  - FK constraints
- FastAPI wiring (composition root):
  - Sessions
  - Repositories
  - File storage
  - Use cases
- Minimal endpoints:
  - `POST /projects`
  - `GET /projects`
  - `GET /projects/{id}`
  - `PATCH /projects/{id}/status`
  - `POST /projects/{id}/patterns`

### Definition of Done
- End-to-end flow works
- Unit + integration tests pass
- Clean Architecture boundaries preserved

---

## Testing Strategy Summary

| Test Type | Scope | Tools |
|---------|------|------|
| Unit | Domain + Application | pytest, in-memory fakes |
| Integration | Infrastructure (DB) | pytest + docker-compose |
| Manual | API flow | FastAPI |

---

## What Remains After Persistence Is Complete

1. Image processing quality improvements
2. Production-grade deployment (app + db)
3. Documentation, demo flow, and TFM presentation

Persistence is a **major milestone**; after this, the project is mostly in the productization and polish phase.

---
