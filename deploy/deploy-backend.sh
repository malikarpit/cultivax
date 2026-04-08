#!/usr/bin/env bash
# ============================================================
# CultivaX — Backend Deployment to Cloud Run
#
# Builds the container, pushes to GCR, and deploys to Cloud Run
# with Cloud SQL connectivity.
#
# Usage:
#   ./deploy/deploy-backend.sh <PROJECT_ID> [REGION] [TAG]
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - Cloud SQL instance created (run setup-cloud-sql.sh first)
#   - APIs enabled: run.googleapis.com, containerregistry.googleapis.com
# ============================================================

set -euo pipefail

# ── Arguments ────────────────────────────────────────────────
PROJECT_ID="${1:?Usage: $0 <PROJECT_ID> [REGION] [TAG]}"
REGION="${2:-asia-south1}"
TAG="${3:-latest}"

SERVICE_NAME="cultivax-backend"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${TAG}"
INSTANCE_NAME="cultivax-db"

echo "╔══════════════════════════════════════════════════════╗"
echo "║   CultivaX — Deploy Backend to Cloud Run            ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Project:  ${PROJECT_ID}"
echo "║  Region:   ${REGION}"
echo "║  Image:    ${IMAGE}"
echo "║  Service:  ${SERVICE_NAME}"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Enable required APIs ────────────────────────────────────
echo "▶ Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}" --quiet

# ── Build the Docker image ──────────────────────────────────
echo "▶ Building Docker image..."
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE}" \
  ./backend

echo "✓ Image built and pushed: ${IMAGE}"

# ── Get Cloud SQL connection name ───────────────────────────
CONNECTION_NAME=$(gcloud sql instances describe "${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" --format="value(connectionName)")

echo "▶ Cloud SQL connection: ${CONNECTION_NAME}"

# ── Retrieve DB password from Secret Manager ────────────────
DB_PASS=$(gcloud secrets versions access latest \
  --secret="cultivax-db-password" \
  --project="${PROJECT_ID}")

# ── Deploy to Cloud Run ─────────────────────────────────────
echo "▶ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=12 \
  --timeout=120 \
  --concurrency=120 \
  --add-cloudsql-instances="${CONNECTION_NAME}" \
  --set-env-vars="\
APP_ENV=production,\
DEBUG=false,\
DATABASE_URL=postgresql://cultivax_user:${DB_PASS}@/${INSTANCE_NAME}?host=/cloudsql/${CONNECTION_NAME},\
CORS_ORIGINS=https://cultivax.web.app,\
LOG_LEVEL=INFO\
"

echo "✓ Deployment complete."

# ── Get the service URL ─────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")

echo ""
echo "══════════════════════════════════════════════════════"
echo "  DEPLOYMENT SUCCESSFUL"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  Service URL:  ${SERVICE_URL}"
echo "  Health check: ${SERVICE_URL}/health"
echo "  API docs:     ${SERVICE_URL}/docs"
echo ""
echo "  Next steps:"
echo "    1. Run migrations: ./deploy/run-migrations.sh ${PROJECT_ID}"
echo "    2. Verify health:  curl ${SERVICE_URL}/health"
echo "    3. Update CORS if frontend URL differs"
echo "══════════════════════════════════════════════════════"
