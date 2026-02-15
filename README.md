# Cross-Stitch Pattern Generator

> **TFM (Final Master Project)** - Master in AI Development
> AI-assisted development with Clean Architecture and Test-Driven Development

Convert images into printable cross-stitch patterns with automatic fabric calculations, DMC thread matching, and PDF export.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-288%20passing-success.svg)](./tests)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://crossstitchpatterns-production.up.railway.app/api/docs)

---

## 🎯 Features

### Pattern Creation
- ✅ **Image to Pattern Conversion** - Convert any image to cross-stitch pattern
- ✅ **DMC Thread Matching** - Automatic matching to 400+ DMC embroidery colors
- ✅ **Color Reduction** - Intelligent palette reduction (3-20 colors)
- ✅ **Custom Dimensions** - Resize patterns or use original image size
- ✅ **PDF Export** - Printable patterns with legend and grid

### Calculations
- ✅ **Fabric Size Calculator** - Automatic fabric requirements based on Aida count
- ✅ **Floss Estimation** - Thread usage calculation per color
- ✅ **Margin Calculation** - Customizable fabric margins

### Project Management
- ✅ **Project Tracking** - Save and manage multiple patterns
- ✅ **Status Workflow** - Track pattern creation progress
- ✅ **File Storage** - Store source images and generated PDFs
- ✅ **Pattern History** - Retrieve past patterns and results

### Developer Features
- ✅ **Complete Workflow API** - Single endpoint for end-to-end pattern creation
- ✅ **REST API** - Full API with OpenAPI documentation
- ✅ **Health Checks** - Built-in monitoring endpoints
- ✅ **Database Migrations** - Automatic schema management with Alembic

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) 20.10+
- [Docker Compose](https://docs.docker.com/compose/) 2.0+

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Elirjimenez/CrossStitchPatterns.git
cd CrossStitchPatterns

# Start the application
docker-compose -f docker/docker-compose.yml up --build

# Access the application
open http://localhost:8000/api/docs
```

That's it! 🎉 The application will:
1. Start PostgreSQL database
2. Run migrations automatically
3. Launch the FastAPI application
4. Be ready at `http://localhost:8000`

### Quick Test

Once running, test the complete workflow:

1. Open **Swagger UI**: http://localhost:8000/api/docs
2. Find `POST /api/projects/complete`
3. Click "Try it out"
4. Upload an image and fill in:
   - **name**: "My First Pattern"
   - **file**: Any PNG/JPG image
   - **num_colors**: 5
5. Click "Execute"
6. Download your PDF from the response URL!

---

## 🌐 Live Demo

The application is deployed and accessible at:

- **API Documentation**: https://crossstitchpatterns-production.up.railway.app/api/docs
- **Health Check**: https://crossstitchpatterns-production.up.railway.app/health

Try it out! Upload an image and generate your cross-stitch pattern.

⚠️ **Note:** Free tier hosting, may sleep after inactivity.

---

## 📦 Deployment

### Railway (Production)

The application is currently deployed on Railway with automatic PostgreSQL provisioning.

**Quick Deploy:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Link to project or create new
railway link  # or: railway init

# Deploy
railway up
```

**Required Environment Variables:**
```env
DATABASE_URL=<automatically provided by Railway PostgreSQL>
STORAGE_DIR=/app/storage
MAX_PATTERN_SIZE=500
```

**Live Instance**: https://crossstitchpatterns-production.up.railway.app

### Docker Deployment (Generic)

Deploy to any platform that supports Docker:

**Build and Run:**
```bash
# Build the Docker image
docker build -f docker/Dockerfile -t crossstitch-api .

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# Or run standalone (requires PostgreSQL)
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/crossstitch \
  -e STORAGE_DIR=/app/storage \
  -v $(pwd)/storage:/app/storage \
  crossstitch-api
```

**Requirements:**
- PostgreSQL 15+ database
- Persistent storage volume for files
- Port 8000 exposed

The Docker image can be deployed to any container platform (Heroku, GCP, AWS, DigitalOcean, etc.) that supports PostgreSQL and persistent storage.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109
- **Python**: 3.11+
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic

### Image Processing
- **Library**: Pillow (PIL)
- **Color Matching**: CIE Lab color space (Delta E 2000)
- **DMC Palette**: 400+ embroidery thread colors

### PDF Generation
- **Library**: ReportLab 4.0
- **Features**: Multi-page patterns, color legend, grid overlay

### Testing
- **Framework**: pytest
- **Coverage**: 288 tests (80%+ coverage)
- **Types**: Unit, Integration, Security, PostgreSQL tests

### DevOps
- **Container**: Docker (multi-stage build)
- **Orchestration**: Docker Compose
- **CI/CD Ready**: GitHub Actions compatible

---

## 📡 API Endpoints

### Complete Workflow
```http
POST /api/projects/complete
```
Upload image → Generate pattern → Export PDF → Save to database
**Single API call** for entire workflow!

### Pattern Operations
```http
POST /api/patterns/convert          # Convert image to pattern
POST /api/patterns/export-pdf       # Export pattern to PDF
POST /api/patterns/calculate-fabric # Calculate fabric requirements
```

### Project Management
```http
GET    /api/projects              # List all projects
POST   /api/projects              # Create project
GET    /api/projects/{id}         # Get project details
PATCH  /api/projects/{id}/status  # Update status
POST   /api/projects/{id}/patterns # Save pattern result
```

### File Downloads
```http
GET /api/projects/files/{path}  # Download PDFs and images
```

### Health & Monitoring
```http
GET /health  # Health check endpoint
```

📖 **Interactive API Docs**: http://localhost:8000/api/docs

---

## 🏗️ Architecture

The project follows **Clean Architecture** principles:

```
app/
├── domain/              # Business logic (framework-independent)
│   ├── model/          # Entities: Pattern, Project, Palette
│   ├── services/       # Domain services: fabric calculations, color matching
│   └── repositories/   # Repository interfaces
├── application/        # Use cases and application services
│   ├── use_cases/     # Business workflows
│   └── ports/         # Adapter interfaces
├── infrastructure/     # External concerns
│   ├── persistence/   # PostgreSQL repositories, Alembic migrations
│   ├── pdf_export/    # ReportLab PDF generation
│   ├── image_processing/ # Pillow image resizing
│   └── storage/       # File storage (local/cloud)
└── web/               # Web layer (FastAPI)
    └── api/
        ├── routes/    # API endpoints
        └── dependencies.py # Dependency injection
```

**Key Principles**:
- Domain layer has **NO** dependencies on outer layers
- All entities are **immutable** (frozen dataclasses)
- **Dependency injection** for all repositories and services
- **Port & Adapter** pattern for external integrations

---

## 🧪 Testing

### Run All Tests

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/Mac

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### PostgreSQL Integration Tests

```bash
# Start test database
docker-compose -f docker/docker-compose.test.yml up -d

# Run PostgreSQL tests
pytest -m postgres -v

# Stop test database
docker-compose -f docker/docker-compose.test.yml down
```

📖 **PostgreSQL Testing Guide**: [docs/postgres_testing.md](./docs/postgres_testing.md)

### Test Coverage

- **Total Tests**: 288 (+ 23 PostgreSQL-specific tests)
- **Coverage**: 80%+
- **Unit Tests**: 239 tests (including security tests)
- **Integration Tests**: 49 tests (SQLite)
- **PostgreSQL Tests**: 23 integration tests

---

## 💻 Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/Elirjimenez/CrossStitchPatterns.git
cd CrossStitchPatterns

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Code Quality

```bash
# Format code
black app/ tests/

# Type checking
mypy app/

# Linting
ruff check app/ tests/

# Run all checks
black --check . && mypy app/ && ruff check .
```

### Development Commands

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Run tests with coverage
pytest --cov=app --cov-report=term --cov-fail-under=80

# Run tests in watch mode
pytest-watch
```

---

## 📝 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/crossstitch` | Yes |
| `STORAGE_DIR` | Directory for file storage | `storage` | Yes |
| `MAX_PATTERN_SIZE` | Maximum pattern dimension | `500` | No |
| `DEFAULT_AIDA_COUNT` | Default fabric count | `14` | No |
| `APP_VERSION` | Application version | `0.1.0` | No |

**Example `.env` file**:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/crossstitch
STORAGE_DIR=storage
MAX_PATTERN_SIZE=500
```

---

## 📚 Documentation

- **[Deployment Guide](./docs/deployment.md)** - Complete deployment instructions
- **[PostgreSQL Testing](./docs/postgres_testing.md)** - Database testing guide
- **[CLAUDE.md](./CLAUDE.md)** - AI collaboration guidelines
- **[API Docs](http://localhost:8000/api/docs)** - Interactive OpenAPI documentation

---

## 🤝 AI-Assisted Development

This project demonstrates **responsible AI-assisted development**:

- ✅ AI proposes, human decides
- ✅ Strict Test-Driven Development (TDD)
- ✅ All code changes pass tests before commit
- ✅ Human validates architecture decisions
- ✅ Transparent collaboration process

**AI Role**: Copilot (not autopilot)
**Human Role**: Architect, decision-maker, validator

See [CLAUDE.md](./CLAUDE.md) for full AI collaboration guidelines.

---

## 📊 Project Statistics

- **Lines of Code**: ~7,000 (3,100 app + 3,800 tests)
- **Tests**: 288 (311 total with PostgreSQL, 80%+ coverage)
- **API Endpoints**: 13
- **Database Tables**: 2 (projects, pattern_results)
- **DMC Colors**: 489 embroidery thread colors
- **Docker Image Size**: 460MB (multi-stage build)

---

## 🎓 TFM Information

**Program**: Master in AI Development
**Institution**: BigSchool
**Academic Year**: 2025-2026
**Deadline**: February 23, 2026

### TFM Deliverables

✅ **Working Application** - Deployed and accessible
✅ **GitHub Repository** - Public with meaningful commits
✅ **README.md** - Complete project documentation
✅ **Test Coverage** - 80%+ coverage requirement met
✅ **Production Deployment** - Railway public instance available
✅ **Presentation Slides** - Architecture and features documented

### Key Achievements

- Real, deployable application with practical use case
- Clean Architecture applied pragmatically
- Test-Driven Development throughout
- Production-ready Docker deployment
- Comprehensive documentation
- AI-assisted development with human oversight

---

## 🛡️ License

This project is part of an academic thesis (TFM) and is provided for educational purposes.

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
- **API Docs**: http://localhost:8000/api/docs

---

**Made with ❤️ and AI assistance for the Master in AI Development TFM**
