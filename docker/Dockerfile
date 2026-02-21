# Multi-stage Dockerfile for Cross-Stitch Pattern Generator
#
# Stage 1: Builder - Install dependencies into a venv
# Stage 2: Runtime - Minimal production image (non-root)

# ============================================================================
# BUILDER STAGE
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for building wheels (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# ============================================================================
# RUNTIME STAGE
# ============================================================================
FROM python:3.11-slim

# Create non-root user in RUNTIME (important!)
# Use a fixed UID to avoid surprises in some platforms
RUN useradd -m -u 1000 appuser

# Runtime deps:
# - libpq5 is the runtime library (libpq-dev is for compiling, not needed here)
# - postgresql-client only if you actually need psql inside container (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create writable dirs BEFORE switching user
# /tmp is usually writable, but we make it explicit
RUN mkdir -p /app/storage /app/tmp && \
    chown -R appuser:appuser /app

# Copy application code with correct ownership (avoid root-owned files)
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

# Env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STORAGE_DIR=/app/storage \
    TMPDIR=/app/tmp

# Switch to non-root user (the security fix)
USER appuser

EXPOSE 8000

# Health check (requires httpx in requirements-prod.txt)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run migrations and start
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]