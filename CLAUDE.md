# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cross-Stitch Pattern Generator - A TFM (Master's Final Project) for the Master in AI Development. This is a web application that converts images into cross-stitch patterns, calculates fabric requirements, manages embroidery projects, and exports printable PDFs.

**Key Philosophy**: AI-assisted development under strict human supervision. AI proposes, human decides and validates. All code changes must pass tests before committing.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_fabric_size.py

# Run tests with coverage (once coverage is configured)
pytest --cov=app tests/
```

### Python Environment
```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Unix/Mac)
source .venv/bin/activate

# Install dependencies (when available)
pip install -r requirements.txt
```

### Code Quality Tools
```bash
# Format code with black
black app/ tests/

# Check code formatting
black --check app/ tests/

# Run type checker
mypy app/

# Run linter
ruff check app/ tests/

# Run all quality checks
black --check . && mypy app/ && ruff check .
```

### Docker Commands
```bash
# Build and run with docker-compose
docker-compose -f docker/docker-compose.yml up --build

# Run tests in Docker
docker-compose -f docker/docker-compose.yml run --rm web pytest

# Stop all containers
docker-compose -f docker/docker-compose.yml down
```

## Architecture

### Clean Architecture (Light)
The project follows Clean Architecture principles pragmatically:

```
app/
├── domain/           # Core business logic (framework-independent)
│   ├── model/       # Domain entities (Pattern, PatternGrid, Palette)
│   └── services/    # Domain services (fabric size calculations, etc.)
├── application/     # Use cases and application services
├── infrastructure/  # External concerns (DB, file system, etc.)
├── web/            # Web layer (FastAPI + HTMX)
└── main.py         # Application entry point
```

**Dependency Rule**: Dependencies flow inward. Domain layer has NO dependencies on outer layers (application, infrastructure, web). Domain is pure Python with business logic only.

### Domain Model
- **PatternGrid**: Immutable 2D grid of palette indices representing the cross-stitch pattern
- **Palette**: Collection of RGB colors used in the pattern
- **Pattern**: Combines a grid with its palette
- **FabricSize**: Value object for fabric dimensions in cm

All domain entities are immutable (frozen dataclasses) to prevent accidental mutations.

### Key Domain Services
- `compute_fabric_size_cm()`: Calculates required fabric size based on stitch count, Aida count (stitches per inch), and margin requirements

### Repository Pattern (Ports & Adapters)
Repository interfaces must be defined in the domain layer as abstract contracts:
- `PatternRepository`: Save and retrieve patterns
- `ProjectRepository`: Manage user projects (if implementing authentication)

Implementations live in `infrastructure/persistence/` using SQLAlchemy or similar ORM.

### Use Cases (Application Layer)
Use cases orchestrate domain services and repositories to fulfill business operations:
- `ConvertImageToPattern`: Handle image upload and conversion
- `CalculateFabricRequirements`: Calculate fabric and thread needs
- `ExportPatternToPDF`: Generate printable pattern
- `SavePattern`: Persist pattern to database

Each use case should have a dedicated test file following TDD.

### Infrastructure Adapters
Concrete implementations of external dependencies:
- **Persistence**: PostgreSQL repository implementations with SQLAlchemy
- **Image Processing**: PIL/Pillow adapter for image manipulation
- **PDF Export**: ReportLab or WeasyPrint adapter for PDF generation
- **File Storage**: Local or cloud storage adapter

### Web Layer (FastAPI)
RESTful API endpoints with proper request/response validation:
- Use Pydantic models for API contracts
- Dependency injection for use cases
- Proper error handling and HTTP status codes
- CORS configuration if needed

## Test-Driven Development (TDD)

**CRITICAL**: This project uses strict TDD. Always write tests FIRST before implementing features.

1. Write a failing test that defines the desired behavior
2. Write minimal code to make the test pass
3. Refactor while keeping tests green
4. Never bypass tests or write code without corresponding tests

Tests live in `tests/unit/` and mirror the `app/` structure.

**Test Coverage Requirement**: Minimum 80% coverage (TFM requirement). Measure with:
```bash
pytest --cov=app --cov-report=html --cov-report=term --cov-fail-under=80
```

**Test Types Required**:
- **Unit tests**: Test domain entities, services, and use cases in isolation
- **Integration tests**: Test repository implementations, database operations, and use case workflows
- **E2E tests** (optional): Test complete API endpoints

## AI Collaboration Rules (from AGENTS.md)

### AI MUST:
- Propose alternatives and explain trade-offs
- Assist with tests, refactors, and debugging
- Respect architecture boundaries and TDD workflow
- Wait for human validation before proceeding

### AI MUST NOT:
- Make autonomous decisions
- Introduce new technologies without approval
- Bypass or skip tests
- Deliver large unreviewed code blocks

### Human-in-the-Loop Workflow:
1. Human defines task and constraints
2. AI suggests options and implementations
3. Human reviews and validates
4. Tests are executed
5. Human commits

## Technology Stack

- **Backend**: FastAPI + HTMX (planned)
- **Database**: PostgreSQL (planned)
- **Testing**: pytest
- **Containerization**: Docker (planned)
- **Python**: >= 3.11

## MVP Scope

The Minimum Viable Product includes:
1. Image to cross-stitch pattern conversion
2. Fabric size calculation
3. Floss (thread) estimation
4. PDF export for printable patterns
5. PostgreSQL persistence

## TFM Requirements & Quality Standards

### Required Deliverables (Deadline: February 23, 2025)
1. **Complete README.md** with:
   - Project description and features
   - Technology stack
   - Installation and execution instructions
   - Project structure explanation
   - Deployment URL
   - Screenshots/demos

2. **Public GitHub Repository**:
   - Meaningful commit history
   - Proper .gitignore
   - No sensitive data in commits

3. **Deployed Application**:
   - Public URL for demo
   - Must be documented in README

4. **Presentation Slides**:
   - Google Slides, PowerPoint, or similar
   - Explain architecture, decisions, and features

### Code Quality Requirements
- **Test Coverage**: Minimum 80% (enforced in CI)
- **Code Formatting**: Use `black` for consistent formatting
- **Type Checking**: Use `mypy` with strict mode
- **Linting**: Use `ruff` for Python linting
- **Pre-commit Hooks**: Automated quality checks before commits

### CI/CD Requirements
- **GitHub Actions** pipeline that:
  - Runs all tests
  - Checks test coverage (≥80%)
  - Runs code quality tools (black, mypy, ruff)
  - Fails if any check doesn't pass

### Documentation Requirements
- **Architecture Decision Records (ADRs)**: Document key architectural decisions in `docs/adr/`
- **Mermaid Diagrams**: Visual representation of architecture layers and data flow
- **API Documentation**: FastAPI auto-generates OpenAPI docs; ensure comprehensive endpoint descriptions
- **AI-Assisted Development Notes**: Document how AI tools were used in development

### Security Requirements
- **Input Validation**: Use Pydantic models for all API inputs
- **File Upload Safety**: Validate file types, sizes, and scan for malicious content
- **Error Handling**: Never expose sensitive information in error messages
- **Rate Limiting**: Implement rate limiting on API endpoints
- **Security Headers**: Proper CORS, CSP, and other security headers

### Deployment Requirements
- **Containerization**: Complete Docker and docker-compose configuration
- **Health Checks**: `/health` endpoint for monitoring
- **Logging**: Structured logging for debugging and monitoring
- **Error Tracking**: Consider Sentry or similar (mentioned in TFM curriculum)

## Project Context

This is an academic TFM project demonstrating:
- Real, deployable application development
- Clean architecture applied pragmatically
- Test-Driven Development methodology
- Responsible AI-assisted development with human oversight

The human developer maintains full control over architectural decisions, technology choices, and commits. AI serves as a copilot, not an autopilot.
