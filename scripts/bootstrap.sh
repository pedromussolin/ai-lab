#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Bootstrapping AI Lab development environment..."

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h db -U ailab -d ailab 2>/dev/null; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

# Run migrations
echo "🗃️  Running database migrations..."
alembic upgrade head

echo "✅ Bootstrap complete! API is starting..."
