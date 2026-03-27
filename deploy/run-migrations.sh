#!/usr/bin/env bash
# ============================================================
# CultivaX — Cloud SQL Migration Runner
#
# Connects to Cloud SQL via the Cloud SQL Auth Proxy and runs
# Alembic migrations against the production database.
#
# Usage:
#   ./deploy/run-migrations.sh <PROJECT_ID> [REGION]
#
# Modes:
#   - LOCAL PROXY: Uses cloud-sql-proxy binary for local dev
#   - CLOUD RUN:   Uses built-in /cloudsql socket (auto-detected)
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - cloud-sql-proxy installed (for local mode)
#   - Python venv with alembic installed
# ============================================================

set -euo pipefail

PROJECT_ID="${1:?Usage: $0 <PROJECT_ID> [REGION]}"
REGION="${2:-asia-south1}"

INSTANCE_NAME="cultivax-db"
DB_NAME="cultivax_db"
DB_USER="cultivax_user"

echo "╔══════════════════════════════════════════════════════╗"
echo "║   CultivaX — Cloud SQL Migration Runner             ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Project:   ${PROJECT_ID}"
echo "║  Region:    ${REGION}"
echo "║  Instance:  ${INSTANCE_NAME}"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Resolve connection name ─────────────────────────────────
CONNECTION_NAME=$(gcloud sql instances describe "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" --format="value(connectionName)" 2>/dev/null || true)

if [ -z "${CONNECTION_NAME}" ]; then
  echo "❌  Could not resolve Cloud SQL instance '${INSTANCE_NAME}'."
  echo "    Run deploy/setup-cloud-sql.sh first."
  exit 1
fi

echo "✓ Resolved connection: ${CONNECTION_NAME}"

# ── Fetch DB password from Secret Manager ───────────────────
echo "▶ Fetching database password from Secret Manager..."
DB_PASS=$(gcloud secrets versions access latest \
  --secret="cultivax-db-password" \
  --project="${PROJECT_ID}")

if [ -z "${DB_PASS}" ]; then
  echo "❌  Could not fetch secret 'cultivax-db-password'."
  exit 1
fi

echo "✓ Password retrieved."

# ── Determine connection mode ───────────────────────────────
PROXY_SOCKET="/cloudsql/${CONNECTION_NAME}"

if [ -S "${PROXY_SOCKET}/.s.PGSQL.5432" ] 2>/dev/null; then
  # Running inside Cloud Run / Cloud Build — socket exists
  echo "▶ Detected Cloud Run environment — using built-in socket."
  DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=${PROXY_SOCKET}"
else
  # Local development — start Cloud SQL Auth Proxy
  echo "▶ Local environment — starting Cloud SQL Auth Proxy..."

  PROXY_DIR="/tmp/cloudsql"
  mkdir -p "${PROXY_DIR}"

  # Kill any existing proxy
  pkill -f "cloud-sql-proxy" 2>/dev/null || true
  sleep 1

  cloud-sql-proxy "${CONNECTION_NAME}" \
    --unix-socket="${PROXY_DIR}" \
    --quiet &
  PROXY_PID=$!

  # Wait for proxy to be ready
  echo "  Waiting for proxy to start..."
  for i in $(seq 1 15); do
    if [ -S "${PROXY_DIR}/${CONNECTION_NAME}/.s.PGSQL.5432" ] 2>/dev/null; then
      break
    fi
    sleep 1
  done

  DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=${PROXY_DIR}/${CONNECTION_NAME}"

  # Trap to clean up proxy on exit
  trap "kill ${PROXY_PID} 2>/dev/null || true; echo '✓ Proxy stopped.'" EXIT
fi

echo "✓ Database URL configured."
echo ""

# ── Run Alembic migrations ──────────────────────────────────
echo "▶ Running Alembic migrations..."
echo "  alembic upgrade head"
echo ""

cd "$(dirname "$0")/../backend"

DATABASE_URL="${DATABASE_URL}" alembic upgrade head

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ✅ MIGRATIONS COMPLETE"
echo "══════════════════════════════════════════════════════"
echo ""

# ── Verify migration status ────────────────────────────────
echo "▶ Current migration status:"
DATABASE_URL="${DATABASE_URL}" alembic current

echo ""
echo "▶ Migration history:"
DATABASE_URL="${DATABASE_URL}" alembic history --verbose | head -20
