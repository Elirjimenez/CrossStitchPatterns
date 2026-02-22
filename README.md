# Cross-Stitch Pattern Generator

> **TFM (Final Master Project)** – Master in Development with AI
> AI-assisted development with Clean Architecture & Test-Driven Development

Convert images into printable cross-stitch patterns with automatic fabric calculations, DMC thread matching, and PDF export.

---

## 🎯 Project Overview

The Cross-Stitch Pattern Generator is a deployable web application designed to convert images into structured cross-stitch patterns.

The system provides:

✔ Image → Pattern conversion
✔ Fabric size calculation
✔ DMC thread colour matching
✔ Printable PDF export
✔ Persistent project management

---

## 🚀 Core Features

### Pattern Generation
- ✅ Image to cross-stitch pattern conversion
- ✅ DMC thread matching (489 colours, CIE Lab Delta E)
- ✅ Intelligent colour reduction (2–20 colours)
- ✅ Custom pattern dimensions
- ✅ Black & White / Colour variants
- ✅ Adaptive image mode detection (photo / drawing / pixel art)

### Calculations
- ✅ Fabric size estimation (Aida count + margin)
- ✅ Floss/thread usage calculation per colour
- ✅ Margin configuration

### Export & Persistence
- ✅ Multi-page PDF export (overview + legend + grid pages)
- ✅ PostgreSQL project persistence
- ✅ Source image management
- ✅ Pattern history tracking

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.109 + HTMX |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 + Alembic |
| Image processing | Pillow 10.2 (loading, resizing, format conversion) |
| Colour matching | numpy — CIE Lab Delta E against 489 DMC colours |
| PDF generation | ReportLab 4.0 (multi-page: overview + legend + grid) |
| Testing | pytest — unit, integration, PostgreSQL |
| Containerisation | Docker (multi-stage build) + Docker Compose |
| Deployment | Railway (managed PostgreSQL + persistent storage) |
| Python | 3.11 |

---

## 🏗️ Architecture & Project Structure

The project follows a **Clean Architecture** approach with a strict dependency rule: inner layers never depend on outer layers.

```
app/
├── domain/           # Business logic — framework-independent
│   ├── model/        # Entities: Pattern, Project, Palette (frozen dataclasses)
│   ├── services/     # Fabric calc, colour matching, image mode detection
│   └── repositories/ # Repository interfaces (Ports)
├── application/      # Use cases + application services
│   ├── use_cases/    # CreateCompletePattern, CompleteExistingProject, …
│   └── ports/        # ImageResizer, PatternPdfExporter, FileStorage (Protocols)
├── infrastructure/   # Adapters: PostgreSQL, Pillow, ReportLab, LocalFileStorage
└── web/              # FastAPI routes (REST API + HTMX server-rendered UI)
```

Dependency flow:

```
Domain ← Application ← Infrastructure
                     ← Web
```

Key principles:

✔ Domain layer has no dependencies on outer layers
✔ Ports & Adapters — infrastructure is swappable
✔ All domain entities are immutable (frozen dataclasses)
✔ Dependency injection throughout

---

## 📡 API Reference

Interactive docs: [`/api/docs`](http://localhost:8000/api/docs) (Swagger UI) and [`/api/redoc`](http://localhost:8000/api/redoc).

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/projects/complete` | Full workflow: upload → pattern → PDF |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create project |
| `GET` | `/api/projects/{id}` | Get project details |
| `PATCH` | `/api/projects/{id}/status` | Update project status |
| `POST` | `/api/projects/{id}/source-image` | Upload source image |
| `POST` | `/api/projects/{id}/patterns` | Save pattern result |
| `POST` | `/api/projects/{id}/patterns/with-pdf` | Save pattern result + PDF |
| `POST` | `/api/patterns/convert` | Convert image to pattern |
| `POST` | `/api/patterns/export-pdf` | Export pattern to PDF |
| `POST` | `/api/patterns/calculate-fabric` | Calculate fabric requirements |
| `GET` | `/api/projects/files/{path}` | Download PDF or image |
| `GET` | `/health` | Health check |

---

## 🧪 Testing & Quality Assurance

Development followed a **Test-Driven Development (TDD)** methodology throughout — tests were written before implementation for every feature.

**Test suite:**

| Category | Count |
|---|---|
| Unit tests (domain, use cases, services) | 366 |
| Integration tests (SQLite + API) | 184 |
| PostgreSQL integration tests | 23 |
| **Total** | **573** |

**Last run results:** 573 passed, 0 skipped (with test DB) · 549 passed, 24 skipped (without test DB — postgres tests auto-skip)

**Coverage:** 96.57% — enforced via `pytest --cov=app --cov-fail-under=80`

Coverage gaps are limited to abstract interfaces (Protocols/ABCs), defensive error-handling branches, and environment-dependent failure paths.

---

## 🤝 AI-Assisted Development

This project demonstrates **responsible AI-assisted engineering** where the human developer retains full architectural and decision-making control.

✔ Human-defined architecture, features, and constraints
✔ AI-assisted implementation and test scaffolding
✔ No autonomous AI commits — every commit is human-validated
✔ Test suite as the validation gate for all AI-generated code

**AI Role:** Technical copilot
**Human Role:** Architect & decision-maker

Full traceability in [`docs/AI_ASSISTED_DEVELOPMENT.md`](./docs/AI_ASSISTED_DEVELOPMENT.md).

---

## 🚀 Quick Start (Docker — Recommended)

> **Docker is the only fully guaranteed way to run this project.**
> It handles PostgreSQL, migrations, storage volumes, and the application
> in a single command. Use local development only if you have a specific reason to.

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Run

```bash
git clone https://github.com/Elirjimenez/CrossStitchPatterns.git
cd CrossStitchPatterns

docker-compose -f docker/docker-compose.yml up --build
```

The system automatically starts PostgreSQL, applies Alembic migrations, and launches FastAPI.

Access the application at **<http://localhost:8000>**
Interactive API docs at **<http://localhost:8000/api/docs>**

---

## 💻 Local Development (without Docker)

> ⚠️ **Global Python installations are not supported.** Dependencies must be
> installed inside a clean virtual environment. Installing packages globally or
> into a pre-existing environment with conflicting packages may cause import
> errors or version conflicts that are outside the scope of this project.

### Setup

```bash
# Clone and set up
git clone https://github.com/Elirjimenez/CrossStitchPatterns.git
cd CrossStitchPatterns

# Create and activate a clean virtual environment (required)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies into the venv
pip install -r requirements.txt -r requirements-dev.txt

# Configure environment
cp .env.example .env             # edit DATABASE_URL at minimum

# Apply migrations and start
alembic upgrade head
uvicorn app.main:app --reload
```

### Code Quality

```bash
black app/ tests/                          # format
ruff check app/ tests/                     # lint
mypy app/                                  # type check
pytest --cov=app --cov-fail-under=80       # tests + coverage
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/crossstitch` |
| `STORAGE_DIR` | Directory for uploaded files and PDFs | `storage` |
| `MAX_COLORS` | Maximum palette colours allowed | `20` |
| `MAX_TARGET_WIDTH` | Maximum pattern width in stitches | `300` |
| `MAX_TARGET_HEIGHT` | Maximum pattern height in stitches | `300` |
| `MAX_TARGET_PIXELS` | Maximum total stitches (W × H) | `90000` |
| `MAX_INPUT_PIXELS` | Maximum source image pixels | `2000000` |
| `DEFAULT_AIDA_COUNT` | Default Aida fabric count | `14` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000,http://localhost:8000` |

See [`.env.example`](./.env.example) for a ready-to-copy template.

---

## 🌐 Live Demo

- **Web UI:** <https://crossstitchpatterns-production.up.railway.app>
- **API Documentation:** <https://crossstitchpatterns-production.up.railway.app/api/docs>
- **Health Check:** <https://crossstitchpatterns-production.up.railway.app/health>

> ⚠️ Free-tier hosting — instance may sleep after inactivity. Allow a few seconds on first load.

---

## 📦 Deployment

The application is deployed on **Railway** using a Docker container, managed PostgreSQL, and a persistent storage volume.

Alembic migrations run automatically on every startup.

See [`docs/deployment.md`](./docs/deployment.md) for full deployment instructions (Railway + Docker).

---

## 📚 Documentation

| Document | Description |
|---|---|
| [`docs/AI_ASSISTED_DEVELOPMENT.md`](./docs/AI_ASSISTED_DEVELOPMENT.md) | Responsible AI collaboration traceability |
| [`docs/ARCHITECTURE_AND_MVP_PLAN.md`](./docs/ARCHITECTURE_AND_MVP_PLAN.md) | MVP scope and architecture rationale |
| [`docs/architecture/clean_architecture.md`](./docs/architecture/clean_architecture.md) | Clean Architecture boundaries and dependency rule |
| [`docs/deployment.md`](./docs/deployment.md) | Deployment instructions (Docker / Railway) |
| [`docs/postgres_testing.md`](./docs/postgres_testing.md) | How to run PostgreSQL integration tests |
| [`docs/technical_decisions/`](./docs/technical_decisions/) | Architectural Decision Records (ADRs) |
| [`docs/features/`](./docs/features/) | Feature-by-feature technical notes |
| [`docs/reviewer_guide.md`](./docs/reviewer_guide.md) | Pre-generated demo projects and review walkthrough |

---

## ⚠️ Known Limitations

- Free-tier Railway hosting may sleep after inactivity
- Storage volume is limited by Railway plan
- Pattern generation time scales with image size and stitch count

---

## 📊 Project Statistics

| Metric | Value |
|---|---|
| Lines of code | ~7,000 LOC |
| Total tests | 573 (549 passing) |
| Code coverage | 96.57% |
| API endpoints | 13 |
| Database tables | 2 |
| DMC colours | 489 |
| Docker image | Multi-stage build |

---

## 🎓 TFM Information

**Programme:** Master in Development with AI
**Academic year:** 2025–2026
**Deadline:** 23 February 2026

**Deliverables:**

| Deliverable | Status |
|---|---|
| Working deployed application | ✅ Live on Railway |
| Public GitHub repository | ✅ With meaningful commit history |
| Complete README.md | ✅ This document |
| Test coverage ≥ 80% | ✅ 96.57% |
| Production-ready Docker setup | ✅ Multi-stage build |
| Responsible AI-assisted workflow | ✅ Documented in `docs/AI_ASSISTED_DEVELOPMENT.md` |
| Presentation slides | ✅ [Google Slides](https://docs.google.com/presentation/d/1XdOjYuN_Mn1H045irWmQ7l2YrPtPeq-ATks2H5zYsQM/edit?usp=sharing) |

---

## 👨‍💻 Author

**Elisabet Ruiz Jimenez**
Master in AI Development - BigSchool
GitHub: [@Elirjimenez](https://github.com/Elirjimenez)

---

## 🙏 Acknowledgments

- **Claude AI (Anthropic)** - AI pair programming assistant
- **Chat GPT** - AI planning assistant
- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Robust relational database
- **DMC** - Embroidery thread color standards
- **Cross-stitch community** - For inspiring this project

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Elirjimenez/CrossStitchPatterns/issues)
- **Documentation**: [docs/](./docs)
- **Local API Docs**: http://localhost:8000/api/docs
- **Production API Docs**: https://crossstitchpatterns-production.up.railway.app/api/docs

---

**Made with ❤️ and AI assistance for the Master in AI Development TFM**
This project demonstrates how AI-assisted development can be integrated responsibly within a rigorous software 
engineering process.
