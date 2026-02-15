# Deployment Guide

Complete guide for deploying the Cross-Stitch Pattern Generator application.

## Table of Contents

1. [Quick Start with Docker Compose](#quick-start-with-docker-compose)
2. [Production Deployment](#production-deployment)
3. [Environment Variables](#environment-variables)
4. [Health Checks](#health-checks)
5. [Database Migrations](#database-migrations)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start with Docker Compose

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### 1. Start the Application

```bash
# From project root
docker-compose -f docker/docker-compose.yml up --build

# Or run in detached mode
docker-compose -f docker/docker-compose.yml up -d --build
```

### 2. Verify Deployment

```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# Check application health
curl http://localhost:8000/health

# View logs
docker-compose -f docker/docker-compose.yml logs -f web
```

### 3. Access the Application

- **API Documentation**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### 4. Stop the Application

```bash
# Stop containers
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker/docker-compose.yml down -v
```

---

## Production Deployment

### Docker Image

The application uses a **multi-stage Dockerfile** for optimal production deployment:

**Features**:
- ✅ Multi-stage build (builder + runtime)
- ✅ Minimal base image (python:3.11-slim)
- ✅ Non-root user for security
- ✅ Health checks included
- ✅ Production dependencies only
- ✅ Automatic database migrations on startup

### Build Production Image

```bash
# Build the image
docker build -f docker/Dockerfile -t crossstitch-api:latest .

# Run the container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/crossstitch \
  -e STORAGE_DIR=/app/storage \
  --name crossstitch-api \
  crossstitch-api:latest
```

### Docker Compose for Production

**File**: `docker/docker-compose.yml`

```bash
# Production deployment with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# Scale the web service (if needed)
docker-compose -f docker/docker-compose.yml up -d --scale web=3
```

---

## Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/crossstitch` | `postgresql://user:pass@db:5432/crossstitch` |
| `STORAGE_DIR` | Directory for file storage | `storage` | `/app/storage` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_PATTERN_SIZE` | Maximum pattern dimension | `500` |
| `DEFAULT_AIDA_COUNT` | Default fabric count | `14` |
| `APP_VERSION` | Application version | `0.1.0` |

### Configuration Methods

#### 1. Environment File (.env)

```bash
# .env file
DATABASE_URL=postgresql://user:pass@db:5432/crossstitch
STORAGE_DIR=/app/storage
MAX_PATTERN_SIZE=500
```

```bash
# Use with docker-compose
docker-compose --env-file .env -f docker/docker-compose.yml up -d
```

#### 2. Docker Compose Environment

Edit `docker/docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/crossstitch
      - STORAGE_DIR=/app/storage
```

#### 3. Command Line

```bash
docker run -e DATABASE_URL=postgresql://... crossstitch-api:latest
```

---

## Health Checks

### Endpoint

**URL**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

### Docker Health Check

The Dockerfile includes automatic health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"
```

### Manual Health Check

```bash
# Check from host
curl http://localhost:8000/health

# Check from inside container
docker exec crossstitch-api curl http://localhost:8000/health

# Check using docker-compose
docker-compose -f docker/docker-compose.yml exec web curl http://localhost:8000/health
```

---

## Database Migrations

### Automatic Migrations

The Docker container automatically runs migrations on startup:

```bash
# This happens automatically in the container
alembic upgrade head
```

### Manual Migrations

#### Run Migration Manually

```bash
# Using docker-compose
docker-compose -f docker/docker-compose.yml exec web alembic upgrade head

# Using docker directly
docker exec crossstitch-api alembic upgrade head
```

#### Check Migration Status

```bash
# Show current migration version
docker-compose -f docker/docker-compose.yml exec web alembic current

# Show migration history
docker-compose -f docker/docker-compose.yml exec web alembic history
```

#### Create New Migration

```bash
# Generate migration from model changes
docker-compose -f docker/docker-compose.yml exec web \
  alembic revision --autogenerate -m "description"
```

---

## Cloud Deployment

### Deploy to Cloud Platforms

#### 1. Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create crossstitch-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Deploy
heroku container:push web
heroku container:release web

# Open app
heroku open /api/docs
```

#### 2. Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/crossstitch-api

# Deploy to Cloud Run
gcloud run deploy crossstitch-api \
  --image gcr.io/PROJECT-ID/crossstitch-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://...
```

#### 3. AWS ECS / Fargate

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -f docker/Dockerfile -t crossstitch-api .
docker tag crossstitch-api:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/crossstitch-api:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/crossstitch-api:latest

# Deploy using ECS task definition
aws ecs update-service --cluster crossstitch --service api --force-new-deployment
```

#### 4. DigitalOcean App Platform

1. Connect GitHub repository
2. Configure build command: `docker build -f docker/Dockerfile .`
3. Add PostgreSQL database
4. Set environment variables
5. Deploy!

---

## Monitoring & Logging

### View Logs

```bash
# Real-time logs
docker-compose -f docker/docker-compose.yml logs -f web

# Last 100 lines
docker-compose -f docker/docker-compose.yml logs --tail=100 web

# Logs for specific time period
docker-compose -f docker/docker-compose.yml logs --since 2024-01-01T00:00:00
```

### Structured Logging

The application uses `structlog` for structured JSON logging:

```json
{
  "event": "application_startup",
  "level": "info",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "logger": "app.main"
}
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs web

# Check if database is ready
docker-compose -f docker/docker-compose.yml logs db

# Restart services
docker-compose -f docker/docker-compose.yml restart
```

### Database Connection Issues

```bash
# Test database connection from web container
docker-compose -f docker/docker-compose.yml exec web \
  python -c "import psycopg2; psycopg2.connect('postgresql://user:pass@db:5432/crossstitch')"

# Check database is accepting connections
docker-compose -f docker/docker-compose.yml exec db \
  pg_isready -U user -d crossstitch
```

### Migration Failures

```bash
# Check current migration version
docker-compose -f docker/docker-compose.yml exec web alembic current

# Downgrade one version
docker-compose -f docker/docker-compose.yml exec web alembic downgrade -1

# Force upgrade
docker-compose -f docker/docker-compose.yml exec web alembic upgrade head
```

### Storage Issues

```bash
# Check storage directory permissions
docker-compose -f docker/docker-compose.yml exec web ls -la /app/storage

# Fix permissions (if needed)
docker-compose -f docker/docker-compose.yml exec -u root web \
  chown -R appuser:appuser /app/storage
```

### Port Already in Use

```bash
# Find what's using port 8000
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 on host instead
```

---

## Security Best Practices

1. **Non-root User**: Container runs as `appuser` (UID 1000)
2. **Minimal Image**: Uses slim base image
3. **No Dev Dependencies**: Production image excludes testing tools
4. **Environment Variables**: Sensitive data via env vars, not hardcoded
5. **CORS Configuration**: Configure `allow_origins` for production
6. **HTTPS**: Use reverse proxy (nginx, Traefik) for SSL termination

### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.crossstitch.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Performance Optimization

### Database Connection Pooling

SQLAlchemy manages connection pooling automatically. Configure in production:

```python
# app/infrastructure/persistence/database.py
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

### Uvicorn Workers

For production, use multiple workers:

```dockerfile
# In Dockerfile CMD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Or with docker-compose:

```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Backup & Restore

### Database Backup

```bash
# Backup database
docker-compose -f docker/docker-compose.yml exec db \
  pg_dump -U user crossstitch > backup.sql

# Backup with timestamp
docker-compose -f docker/docker-compose.yml exec db \
  pg_dump -U user crossstitch > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore

```bash
# Restore from backup
cat backup.sql | docker-compose -f docker/docker-compose.yml exec -T db \
  psql -U user crossstitch
```

---

## Next Steps

1. **Set up CI/CD** - Automate builds and deployments
2. **Configure monitoring** - Add Prometheus, Grafana, or cloud monitoring
3. **Set up alerts** - Email/Slack notifications for errors
4. **Load testing** - Test with Apache Bench, Locust, or k6
5. **Security scanning** - Use Trivy or Snyk for vulnerability scanning
