FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual env
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Install only the runtime C libs (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 cultivax && \
    useradd --uid 1000 --gid cultivax --create-home cultivax

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Cloud Run deployment vars (set via gcloud run deploy --set-env-vars)
ENV APP_ENV=production \
    GCS_BUCKET_NAME="" \
    GOOGLE_CLOUD_PROJECT=""

# Copy application code
COPY --chown=cultivax:cultivax . .

# Create uploads directory (local fallback)
RUN mkdir -p /app/uploads/media && chown -R cultivax:cultivax /app/uploads

# Create entrypoint script that runs migrations then starts the server
RUN printf '#!/bin/sh\necho "Running database migrations..."\npython -m alembic upgrade head 2>&1 || echo "Migration warning (non-fatal)"\necho "Starting CultivaX backend..."\nexec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Switch to non-root user
USER cultivax

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run entrypoint (migrations + uvicorn)
CMD ["/app/entrypoint.sh"]
