#!/usr/bin/env bash
set -e

echo "=== BundCheck Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-production}"

# Run Alembic Database Migrations if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
    echo "Running Alembic migrations..."
    cd /app/backend
    alembic upgrade head
    echo "Migrations applied successfully."
    cd /app
fi

echo "Starting server process..."
exec "$@"
