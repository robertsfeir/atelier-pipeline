#!/usr/bin/env bash
# Manual schema setup for local PostgreSQL (not Docker)
# Docker users: schema auto-applies via docker-entrypoint-initdb.d mount
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="${SCRIPT_DIR}/schema.sql"

DATABASE_URL="${DATABASE_URL:-postgresql://atelier:atelier@localhost:5432/atelier_brain}"

echo "Atelier Brain: schema setup"
echo "Database: ${DATABASE_URL%%@*}@***"

# Wait for PostgreSQL to be ready
MAX_RETRIES=30
RETRY_INTERVAL=1
for i in $(seq 1 "$MAX_RETRIES"); do
  if psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1; then
    echo "PostgreSQL is ready."
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "Error: PostgreSQL not ready after ${MAX_RETRIES}s" >&2
    exit 1
  fi
  echo "Waiting for PostgreSQL... (${i}/${MAX_RETRIES})"
  sleep "$RETRY_INTERVAL"
done

# Check if schema already exists
TABLE_COUNT=$(psql "$DATABASE_URL" -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('thoughts', 'thought_links');" \
  2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -ge 2 ]; then
  echo "Schema already exists (${TABLE_COUNT} tables found). Skipping."
else
  echo "Applying schema from ${SCHEMA_FILE}..."
  if [ ! -f "$SCHEMA_FILE" ]; then
    echo "Error: schema.sql not found at ${SCHEMA_FILE}" >&2
    exit 1
  fi
  psql "$DATABASE_URL" -f "$SCHEMA_FILE"
  echo "Schema applied successfully."
fi

echo "Atelier Brain: database ready."
