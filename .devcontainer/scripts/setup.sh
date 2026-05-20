#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up AI Lab development environment..."

cd /workspace

# Copy .env if not present
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example - please update with your API keys"
  fi
fi

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
for i in $(seq 1 30); do
  if pg_isready -h db -U ailab -d ailab >/dev/null 2>&1; then
    echo "✅ PostgreSQL ready"
    break
  fi
  sleep 2
done

# Run migrations
echo "🗃️  Running migrations..."
alembic upgrade head || echo "⚠️ Migration failed - check your DATABASE_URL"

# Create uploads directory
mkdir -p uploads

echo ""
echo "🎉 Dev container ready!"
echo ""
echo "Quick start:"
echo "  uvicorn app.main:app --reload  # Start API with hot reload"
echo "  pytest                          # Run tests"
echo "  alembic upgrade head            # Apply migrations"
echo ""
