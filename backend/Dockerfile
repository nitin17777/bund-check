# ==============================================================================
# BundCheck Backend — Production Multi-Stage Dockerfile (Non-Root)
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime Environment
FROM python:3.11-slim AS runner

# Create non-root system user and group
RUN groupadd -g 10001 bundcheck && \
    useradd -u 10001 -g bundcheck -s /bin/bash -m bundcheck

WORKDIR /app

# Install runtime shared libraries required by PyMuPDF and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application source code and migrations
COPY --chown=bundcheck:bundcheck backend /app/backend
COPY --chown=bundcheck:bundcheck ml /app/ml
COPY --chown=bundcheck:bundcheck backend/entrypoint.sh /app/entrypoint.sh

# Grant execution rights to startup script
RUN chmod +x /app/entrypoint.sh

# Create local data and log directories owned by non-root user
RUN mkdir -p /app/data && chown -R bundcheck:bundcheck /app/data

# Switch to non-root user
USER bundcheck:bundcheck

ENV PYTHONPATH="/app" \
    PYTHONUNBUFFERED="1" \
    PORT="8000" \
    ENVIRONMENT="production"

EXPOSE 8000

# Health check probe against API health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
