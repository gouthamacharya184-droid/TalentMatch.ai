# ==============================================================================
# TalentMatch.ai - Production Multi-Stage Dockerfile
# Security Hardened, Minimal Attack Surface, Non-Root Execution
# ==============================================================================

# ── Stage 1: Build Frontend ──────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Build Backend & Production Runtime ─────────────
FROM python:3.12-slim-bookworm AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER_CONTAINER=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production

# Install system dependencies required for compiling wheels and PDF parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install uvicorn[standard] gunicorn

# Create unprivileged user for secure execution
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

# Copy backend source
COPY backend /app/backend
COPY api /app/api
COPY pytest.ini /app/pytest.ini

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Ensure proper ownership and permissions
RUN mkdir -p /app/storage/uploads /app/backups && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
