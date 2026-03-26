#!/usr/bin/env bash
# ============================================================
# CultivaX — Cloud SQL Instance Setup
#
# Creates a PostgreSQL 15 instance on Cloud SQL, configures
# the database and user, and stores credentials in Secret Manager.
#
# Usage:
#   ./deploy/setup-cloud-sql.sh <PROJECT_ID> [REGION]
#
# Prerequisites:
#   - gcloud CLI authenticated with appropriate permissions
#   - APIs enabled: sqladmin.googleapis.com, secretmanager.googleapis.com
# ============================================================

set -euo pipefail

# ── Arguments ────────────────────────────────────────────────
PROJECT_ID="${1:?Usage: $0 <PROJECT_ID> [REGION]}"
REGION="${2:-asia-south1}"

INSTANCE_NAME="cultivax-db"
DB_NAME="cultivax_db"
DB_USER="cultivax_user"
DB_PASS=$(openssl rand -base64 24 | tr -d '/+=')
TIER="db-f1-micro"  # Free-tier eligible; upgrade for production

echo "╔══════════════════════════════════════════════════════╗"
echo "║   CultivaX — Cloud SQL Setup                        ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Project:   ${PROJECT_ID}"
echo "║  Region:    ${REGION}"
echo "║  Instance:  ${INSTANCE_NAME}"
echo "║  Database:  ${DB_NAME}"
echo "║  Tier:      ${TIER}"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Enable required APIs ────────────────────────────────────
echo "▶ Enabling required APIs..."
gcloud services enable sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}" --quiet

# ── Create Cloud SQL instance ───────────────────────────────
echo "▶ Creating Cloud SQL instance '${INSTANCE_NAME}'..."
gcloud sql instances create "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --database-version=POSTGRES_15 \
  --tier="${TIER}" \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time="03:00" \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --availability-type=zonal \
  --root-password="${DB_PASS}" \
  --database-flags=log_checkpoints=on,log_connections=on

echo "✓ Instance created."

# ── Create database ─────────────────────────────────────────
echo "▶ Creating database '${DB_NAME}'..."
gcloud sql databases create "${DB_NAME}" \
  --instance="${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --charset=UTF8 \
  --collation=en_US.UTF8

echo "✓ Database created."

# ── Create user ─────────────────────────────────────────────
echo "▶ Creating user '${DB_USER}'..."
gcloud sql users create "${DB_USER}" \
  --instance="${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --password="${DB_PASS}"

echo "✓ User created."

# ── Store password in Secret Manager ────────────────────────
echo "▶ Storing credentials in Secret Manager..."
printf "%s" "${DB_PASS}" | gcloud secrets create cultivax-db-password \
  --project="${PROJECT_ID}" \
  --replication-policy="automatic" \
  --data-file=-

echo "✓ Secret stored as 'cultivax-db-password'."

# ── Print connection info ───────────────────────────────────
CONNECTION_NAME=$(gcloud sql instances describe "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" --format="value(connectionName)")

echo ""
echo "══════════════════════════════════════════════════════"
echo "  SETUP COMPLETE"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  Connection name:  ${CONNECTION_NAME}"
echo "  Database:         ${DB_NAME}"
echo "  User:             ${DB_USER}"
echo ""
echo "  DATABASE_URL (for Cloud Run):"
echo "  postgresql://${DB_USER}:<password>@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"
echo ""
echo "  Password stored in Secret Manager: cultivax-db-password"
echo "══════════════════════════════════════════════════════"
