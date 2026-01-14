#!/usr/bin/env bash
set -e

echo "Starting Video Studio API..."
echo "Running migrations..."
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8080
