# Multi-stage Dockerfile for Cross-Stitch Pattern Generator
#
# Stage 1: Builder - Install dependencies into a venv
# Stage 2: Runtime - Minimal production image (runtime fixes perms, then drops to appuser)

# ============================================================================
# BUILDER STAGE
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

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

# Create non-root user in runtime
RUN useradd -m -u 1000 appuser

# Runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create dirs (mounts may override /app/storage at runtime; entrypoint will fix perms)
RUN mkdir -p /app/storage /app/tmp

# Copy app code with non-root ownership
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

# Env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STORAGE_DIR=/app/storage \
    TMPDIR=/app/tmp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# ---------------------------------------------------------------------------
# ENTRYPOINT (generated inline to avoid missing file in build context)
# ---------------------------------------------------------------------------
RUN cat > /entrypoint.sh <<'EOF'
#!/bin/sh
set -e

: "${STORAGE_DIR:=/app/storage}"

mkdir -p "${STORAGE_DIR}/projects"
chown -R appuser:appuser "${STORAGE_DIR}"

# Preserve args properly
exec su -s /bin/sh appuser -c "$@"
EOF
RUN chmod +x /entrypoint.sh

# Start as root so we can chown mounted volumes; entrypoint drops to appuser
ENTRYPOINT ["/entrypoint.sh"]

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]