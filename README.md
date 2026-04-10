# CultivaX 🌱

**Intelligent Crop Lifecycle Management & Service Orchestration Platform**

CultivaX is a production-grade, event-driven agricultural management platform that gives farmers chronologically-accurate crop timeline tracking, AI-backed recommendations, a service marketplace, and government scheme discovery — all in 5 languages (English, Hindi, Tamil, Telugu, Marathi).

[![Backend](https://img.shields.io/badge/backend-FastAPI%203.11-green)](http://localhost:8000/docs)
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-blue)](http://localhost:3000)
[![DB](https://img.shields.io/badge/database-PostgreSQL%2015-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-Academic-orange)](#license)

---

## Documentation

For deeper technical detail, refer to these docs:

| Document | Covers |
|----------|--------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, CTIS internals, SOE, ML module, event dispatcher, database overview, infrastructure |
| [API.md](docs/API.md) | Every API endpoint — auth requirements, request/response shapes, error codes, rate limits |
| [DATA_MODEL.md](docs/DATA_MODEL.md) | All 35+ database tables, column types, constraints, and entity relationships |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | How to add models, endpoints, pages, events; testing guide; debugging scenarios; git conventions |
| [TECH_STACK.md](docs/TECH_STACK.md) | Rationale for every technology choice |
| [SECURITY.md](docs/SECURITY.md) | Security hardening, middleware stack, RBAC |
| [SECRETS_ROTATION.md](docs/SECRETS_ROTATION.md) | Key rotation and secret management runbook |

---

## Table of Contents

1. [Quick Start (Docker)](#1-quick-start-docker--5-minutes)
2. [Manual Setup](#2-manual-setup)
3. [Environment Variables](#3-environment-variables)
4. [Demo Accounts](#4-demo-accounts)
5. [Features](#5-features)
6. [Frontend Pages](#6-frontend-pages)
7. [API Reference](#7-api-reference)
8. [Project Structure](#8-project-structure)
9. [Running Tests](#9-running-tests)
10. [Cloud Deployment (GCP)](#10-cloud-deployment-gcp)
11. [Architecture](#11-architecture)
12. [Team](#12-team)

---

## 1. Quick Start (Docker) — 5 Minutes

> **Requirements:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose) — nothing else needed.

### Step 1 — Clone the repository

```bash
git clone https://github.com/malikarpit/cultivax.git
cd cultivax
```

### Step 2 — Create the environment file

```bash
# Copy the template (no values required for basic local dev)
cp .env.example .env
```

> **Optional:** If you want real SMS OTPs or live weather data, edit `.env` and fill in your Twilio and OpenWeatherMap keys. The app works fully without them using stub providers.

### Step 3 — Start everything

```bash
docker compose up
```

This single command:
- Starts **PostgreSQL 15** on port `5432`
- Runs **all Alembic database migrations** automatically
- Seeds **3 demo accounts** (admin, farmer, provider)
- Starts the **FastAPI backend** on port `8000`
- Starts the **Next.js frontend** on port `3000`

> First run takes ~3–5 minutes to build Docker images. Subsequent starts are instant.

### Step 4 — Open the app

| Service | URL |
|---------|-----|
| 🌐 Frontend | http://localhost:3000 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| 🔍 API Health | http://localhost:8000/api/v1/health |

Log in with any [demo account](#4-demo-accounts) — you're ready to go.

### Stopping the app

```bash
# Stop (keep data)
docker compose stop

# Stop and remove containers + volumes (full reset)
docker compose down -v
```

---

## 2. Manual Setup

Use this if you prefer to run services directly without Docker.

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| PostgreSQL | 15+ | [postgresql.org](https://postgresql.org) |

### 2a — Database

```bash
# Create PostgreSQL user and database
psql -U postgres << 'EOF'
CREATE USER cultivax_user WITH PASSWORD 'cultivax_pass';
CREATE DATABASE cultivax_db OWNER cultivax_user;
EOF
```

### 2b — Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env — set DATABASE_URL to: postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db

# Run database migrations
alembic upgrade head

# Seed demo accounts
python -m scripts.seed_demo_users

# Start the API server
uvicorn app.main:app --reload --port 8000
```

Backend is available at http://localhost:8000

### 2c — Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the dev server
npm run dev
```

Frontend is available at http://localhost:3000

---

## 3. Environment Variables

### Root `.env` (Docker Compose reads this)

Create this file at the project root. You can copy `.env.example` as a starting point.

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENWEATHER_API_KEY` | No | Live weather data. [Get free key](https://openweathermap.org/api) | Falls back to Open-Meteo (free, no key) |
| `SMS_PROVIDER` | No | SMS backend: `stub` (logs to console) or `twilio` | `stub` |
| `TWILIO_ACCOUNT_SID` | Only if `SMS_PROVIDER=twilio` | Twilio account SID | — |
| `TWILIO_AUTH_TOKEN` | Only if `SMS_PROVIDER=twilio` | Twilio auth token | — |
| `TWILIO_FROM_NUMBER` | Only if `SMS_PROVIDER=twilio` | Twilio sender phone e.g. `+1...` | — |

### Backend `backend/.env` (Manual setup only)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db` |
| `SECRET_KEY` | JWT signing secret — **change in production** | `some-random-secret-64-chars` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | `60` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `APP_ENV` | `development` or `production` | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `GCS_BUCKET_NAME` | GCS bucket for media uploads (empty = local disk) | `""` |

### Frontend `frontend/.env.local` (Manual setup only)

| Variable | Description | Value |
|----------|-------------|-------|
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://localhost:8000` |

---

## 4. Demo Accounts

These accounts are automatically created when the app starts (via seed script).

| Role | Phone | Password | Access |
|------|-------|----------|--------|
| **Admin** | `+919999999991` | `password123` | Full admin panel, user management, system health |
| **Farmer** | `+919999999992` | `password123` | Crops, timeline, services, schemes, alerts |
| **Provider** | `+919999999993` | `password123` | Equipment management, incoming service requests |

> Login uses phone number + password. OTP is **not required** for demo accounts.

---

## 5. Features

### 🌾 CTIS — Crop Timeline Intelligence System
- **Deterministic Replay Engine** — Rebuilds crop state from the full action log with snapshot checkpoints for fast recovery
- **Crop State Machine** — Enforces valid state transitions: `Created → Active → Harvested / Closed`
- **Stress Score Engine** — Multi-signal stress computation with deviation tracking across growth stages
- **What-If Simulation** — Test hypothetical actions in isolated memory (non-persistent) context
- **Drift Enforcement** — Clamps timeline drift to ±max per lifecycle stage
- **Behavioral Adapter** — Detects recurring farmer patterns, computes bounded ±7-day offsets
- **Temporal Anomaly Detection** — Rejects backdated/future-dated offline sync actions
- **Yield Verification** — Separates Farmer Truth vs ML Truth with biological limit caps
- **Snapshot Manager** — Periodic checkpoints every N actions for fast replay recovery

### 🛒 SOE — Service Orchestration Ecosystem
- **Service Marketplace** — Browse and book equipment & labor providers by region
- **Trust Score Engine** — 6-factor weighted trust computation with temporal decay
- **Exposure Fairness Engine** — Provider ranking with 70% exposure cap and regional saturation control
- **Fraud Detection** — 3-signal analysis (review patterns, rating spikes, timing anomalies)
- **Service Request Lifecycle** — State machine with event emission on every transition
- **Escalation Policy Engine** — Complaint routing and resolution workflows

### 🏛️ Government Schemes Browser
- Browse official government agricultural schemes filtered by region and category
- Categories: subsidy, insurance, advisory, loan
- Direct portal redirect with audit trail logging

### 🤖 ML Module
- **Risk Predictor** — Rule-based fallback with ML Kill Switch (graceful degradation)
- **Model Registry** — Version lifecycle management (register, activate, deactivate)
- **Inference Audit** — Every inference is logged with confidence scores and model version

### 🔔 Smart Notifications & Recommendations
- **Alert Service** — System-generated alerts with throttling (max 3 per crop per 24h)
- **Recommendation Engine** — Daily prioritized action suggestions based on stress/risk/stage
- **SMS Notifications** — OTP and critical alerts via Twilio (or `stub` for development)

### 🌍 Internationalization (i18n)
- Full UI translation in **5 languages**: English, Hindi (हिंदी), Tamil (தமிழ்), Telugu (తెలుగు), Marathi (मराठी)
- Language switcher in the navigation header
- All labels, error messages, and dynamic text are translated

### 📱 Offline PWA
- Service worker for offline capability
- Offline action queue — actions logged without internet sync automatically when reconnected
- Optimistic UI updates with SWR

---

## 6. Frontend Pages

| Page | Route | Who Sees It |
|------|-------|-------------|
| Landing | `/` | Everyone |
| Login | `/login` | Everyone |
| Register | `/register` | Everyone |
| Dashboard | `/dashboard` | Farmers |
| Crop List | `/crops` | Farmers |
| Crop Detail | `/crops/[id]` | Farmers |
| New Crop | `/crops/new` | Farmers |
| Log Action | `/crops/[id]/log-action` | Farmers |
| Crop History | `/crops/[id]/history` | Farmers |
| Simulate | `/crops/[id]/simulate` | Farmers |
| Land Parcels | `/land-parcels` | Farmers |
| Weather | `/weather` | Farmers |
| Services | `/services` | Farmers |
| Labor | `/labor` | Farmers |
| Alerts | `/alerts` | Farmers |
| Schemes | `/schemes` | Farmers |
| Disputes | `/disputes` | Farmers |
| Profile | `/profile` | All logged-in |
| Settings | `/settings` | All logged-in |
| Privacy | `/privacy` | Everyone |
| Terms | `/terms` | Everyone |
| Support | `/support` | Everyone |
| Provider Dashboard | `/provider` | Providers |
| Equipment | `/provider/equipment` | Providers |
| Provider Onboarding | `/provider/onboarding` | Providers |
| Reviews | `/provider/reviews` | Providers |
| Admin Dashboard | `/admin` | Admins |
| User Management | `/admin/users` | Admins |
| Provider Management | `/admin/providers` | Admins |
| Templates | `/admin/templates` | Admins |
| System Health | `/admin/health` | Admins |
| Dead Letters | `/admin/dead-letters` | Admins |
| ML Models | `/admin/ml-models` | Admins |
| Feature Flags | `/admin/features` | Admins |
| Security | `/admin/security` | Admins |
| Analytics | `/admin/analytics` | Admins |
| Reports | `/admin/reports` | Admins |

---

## 7. API Reference

Full interactive documentation: **http://localhost:8000/docs**

| Module | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| **Health** | `/api/v1/health` | GET | Service health check |
| **Auth** | `/api/v1/auth/register` | POST | Register new user |
| | `/api/v1/auth/login` | POST | Login — returns JWT |
| | `/api/v1/auth/refresh` | POST | Refresh access token |
| **Crops** | `/api/v1/crops/` | GET, POST | List / create crop instances |
| | `/api/v1/crops/{id}` | GET, PUT, DELETE | Crop detail / update / delete |
| | `/api/v1/crops/{id}/actions` | POST | Log a farmer action |
| | `/api/v1/crops/{id}/simulate` | POST | What-if simulation |
| | `/api/v1/crops/{id}/yield` | POST | Submit harvest yield |
| | `/api/v1/crops/{id}/recommendations` | GET | Prioritized action suggestions |
| | `/api/v1/crops/{id}/history` | GET | Full action log + replay |
| **Providers** | `/api/v1/providers/` | GET, POST | Browse / register providers |
| **Equipment** | `/api/v1/equipment/` | GET, POST | Equipment management |
| **Labor** | `/api/v1/labor/` | GET, POST | Labor listing |
| **Service Requests** | `/api/v1/service-requests/` | GET, POST | Create / list requests |
| | `/api/v1/service-requests/{id}` | PUT | Accept / complete / cancel |
| **Reviews** | `/api/v1/reviews/` | POST | Submit service review |
| **Alerts** | `/api/v1/alerts/` | GET | Farmer notifications |
| **Schemes** | `/api/v1/schemes/` | GET | Browse government schemes |
| | `/api/v1/schemes/{id}/redirect` | POST | Log scheme portal visit |
| **Weather** | `/api/v1/weather/` | GET | Current weather for region |
| **Land Parcels** | `/api/v1/land-parcels/` | GET, POST | Field/parcel management |
| **Rules** | `/api/v1/rules/` | GET, POST, PUT | Crop rule templates |
| **Features** | `/api/v1/features/` | GET, PUT | Feature flag management |
| **ML Models** | `/api/v1/ml/models` | GET, POST | Model registry |
| **Media** | `/api/v1/media/upload` | POST | File upload (GCS / local) |
| **Sync** | `/api/v1/sync/` | POST | Bulk offline action sync |
| **Analytics** | `/api/v1/analytics/` | GET | Platform analytics |
| **Admin** | `/api/v1/admin/*` | GET, PUT | User mgmt, provider governance |
| **Disputes** | `/api/v1/disputes/` | GET, POST | Dispute management |
| **Reports** | `/api/v1/reports/` | GET | Generated reports |

---

## 8. Project Structure

```
cultivax/
├── backend/                         # FastAPI backend (Python 3.11)
│   ├── app/
│   │   ├── api/v1/                  # 30+ REST API modules
│   │   │   ├── auth.py              # Registration, login, OTP, JWT refresh
│   │   │   ├── crops.py             # Crop CRUD + action logging
│   │   │   ├── schemes.py           # Government schemes browser
│   │   │   ├── disputes.py          # Dispute resolution
│   │   │   └── ...                  # (all other controllers)
│   │   ├── models/                  # 35+ SQLAlchemy ORM models
│   │   │   ├── official_scheme.py   # Government schemes
│   │   │   ├── dispute_case.py      # Dispute cases
│   │   │   ├── user_consent.py      # GDPR-style consent logs
│   │   │   └── ...
│   │   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── ctis/                # Replay, stress, drift, simulation engines
│   │   │   ├── soe/                 # Trust, exposure, fraud engines
│   │   │   ├── ml/                  # Risk predictor, model registry
│   │   │   ├── event_dispatcher/    # DB-backed FIFO event processing
│   │   │   ├── notifications/       # SMS + in-app alerts
│   │   │   ├── recommendations/     # Priority-scored suggestions
│   │   │   ├── media/               # File upload service (GCS + local)
│   │   │   └── weather/             # Weather API integration
│   │   ├── middleware/              # Rate limiting, error handling, idempotency
│   │   ├── security/                # JWT, bcrypt, RBAC guards
│   │   └── main.py                  # FastAPI app entrypoint
│   ├── alembic/
│   │   └── versions/                # 15+ database migration files
│   ├── scripts/
│   │   └── seed_demo_users.py       # Creates demo accounts on startup
│   ├── tests/                       # pytest test suite (280+ tests)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                        # Next.js 14 (App Router)
│   └── src/
│       ├── app/                     # 30+ pages using file-based routing
│       │   ├── admin/               # Admin panel pages
│       │   ├── crops/               # Crop management pages
│       │   ├── schemes/             # Government schemes browser
│       │   ├── disputes/            # Dispute management
│       │   └── ...
│       ├── components/              # Reusable UI components
│       │   ├── Sidebar.tsx          # Role-based navigation
│       │   ├── LanguageSwitcher.tsx # i18n language toggle
│       │   └── ...
│       ├── context/                 # Auth context, SWR provider
│       ├── hooks/                   # useFetch, useOfflineActions, etc.
│       ├── lib/
│       │   ├── i18n.ts              # Inline translation dictionaries (5 languages)
│       │   └── api.ts               # Typed API client
│       └── worker/                  # PWA service worker
│
├── deploy/                          # GCP deployment scripts
│   ├── deploy-backend.sh            # Cloud Run deploy
│   ├── run-migrations.sh            # Cloud SQL migrations
│   └── setup-cloud-sql.sh           # Cloud SQL provisioning
│
├── docs/                            # SRS, MSDD, TDD, architecture docs
├── docker-compose.yml               # Local dev orchestration
├── .env                             # Secrets file (gitignored — create from .env.example)
├── .env.example                     # Template for .env
└── pyrightconfig.json               # Pyright type checking config
```

---

## 9. Running Tests

```bash
# Run all backend tests
cd backend
pytest

# Run with coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view coverage

# Run a specific test module
pytest tests/test_official_schemes.py -v
pytest tests/test_dispute_resolution.py -v
pytest tests/test_soe_flow.py -v

# Run tests matching a keyword
pytest -k "trust" -v

# Run inside Docker (no local Python needed)
docker compose exec backend pytest
```

---

## 10. Cloud Deployment (GCP)

### Prerequisites

```bash
# Install gcloud CLI and authenticate
gcloud auth login
gcloud auth configure-docker
```

### Step 1 — Provision Cloud SQL

```bash
./deploy/setup-cloud-sql.sh <YOUR_GCP_PROJECT_ID>
```

### Step 2 — Deploy Backend to Cloud Run

```bash
./deploy/deploy-backend.sh <YOUR_GCP_PROJECT_ID> [REGION] [IMAGE_TAG]
# Example:
./deploy/deploy-backend.sh my-project asia-south1 v1.0
```

This will:
- Enable required GCP APIs (Cloud Run, Cloud Build, Cloud SQL)
- Build the Docker image via Cloud Build
- Push to Google Container Registry
- Deploy to Cloud Run with Cloud SQL connectivity
- Auto-run `alembic upgrade head` on startup

### Step 3 — Run Migrations Manually (if needed)

```bash
./deploy/run-migrations.sh <YOUR_GCP_PROJECT_ID>
```

### Step 4 — Verify

```bash
SERVICE_URL=$(gcloud run services describe cultivax-backend \
  --project=<PROJECT_ID> --region=asia-south1 --format="value(status.url)")

curl ${SERVICE_URL}/api/v1/health
open ${SERVICE_URL}/docs
```

---

## 11. Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Next.js 14 Frontend                 │
│  30+ pages · 5 languages · PWA offline · SWR cache  │
└──────────────────────────┬───────────────────────────┘
                           │ HTTP / REST
┌──────────────────────────▼───────────────────────────┐
│                  FastAPI Backend (Python 3.11)        │
│   30+ API modules · JWT RBAC · idempotent endpoints  │
└───┬──────────────────────┬─────────────────────┬─────┘
    │                      │                     │
┌───▼────────┐   ┌─────────▼──────┐   ┌─────────▼──────┐
│   CTIS      │   │     SOE        │   │   ML Module    │
│ ─────────── │   │ ─────────────  │   │ ──────────── ─ │
│ Replay Eng  │   │ Trust Engine   │   │ Risk Predictor │
│ State Mach  │   │ Fraud Detect   │   │ Model Registry │
│ Stress Eng  │   │ Exposure Eng   │   │ Inference Audit│
│ Drift Enf   │   │ Request Svc    │   │ Kill Switch    │
│ WhatIf Sim  │   │ Escalation     │   └────────────────┘
│ Yield Verif │   └────────────────┘
└─────────────┘
    │
┌───▼──────────────┐   ┌────────────────┐   ┌────────────────┐
│  Event Dispatcher │   │   PostgreSQL 15 │   │  Cloud Storage │
│  DB-backed FIFO   │   │  35+ tables    │   │  GCS + local   │
│  SKIP LOCKED      │   │  15+ migrations│   │  Signed URLs   │
└───────────────────┘   └────────────────┘   └────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| DB-backed event queue (not Redis) | Eliminates external dependency; ACID-safe; survives restarts |
| Inline i18n dictionary (not remote API) | Full offline support; no translation CDN dependency |
| Snapshot checkpoints in CTIS | Fast replay recovery without re-processing entire history |
| Idempotency keys on mutations | Safe to retry offline-synced actions |
| JWT + bcrypt (no OAuth) | Simpler auth for low-connectivity rural environments |
| Open-Meteo as primary weather | Completely free, no API key required |

---

## 12. Team

| Member | Role & Contributions |
|--------|----------------------|
| **Arpit** | Lead Developer — Core FastAPI architecture, CTIS engines (stress, drift, simulator), recommendation & alert systems, i18n system (5-language dictionaries), infrastructure & Cloud Run deployment |
| **Shivam Yadav** | Full-Stack — ML inference runtime & model registry, media analysis workers, frontend PWA service worker, offline sync hooks |
| **Ravi Patel** | Full-Stack — V1 API controllers & RBAC, SOE trust module, government schemes & analytics APIs, admin dashboard UI, provider/service marketplace frontend |
| **Ayush Kumar Meena** | Full-Stack — CTIS replay engine & DB-backed event dispatcher, auth system & security middleware, dispute resolution API, testing infrastructure |
| **Prince** | Frontend — All UI pages (30+), MapLibre GL integration, data grids, charts, stat cards, offline sync UI, overall frontend polish |

---

## License

Developed as part of the Software Engineering course at the Faculty of Technology, Delhi University.

> This project is for academic evaluation purposes. Production deployment with real API keys (Twilio, GCS) requires proper secret management — never commit `.env` to version control.
