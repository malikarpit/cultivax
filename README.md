# CultivaX 🌱

**Intelligent Crop Lifecycle Management & Service Orchestration Platform**

CultivaX is a deterministic, event-driven agricultural management system that provides farmers with chronologically accurate crop timeline tracking, intelligent recommendations, and a service marketplace — all built with replay-safe architecture.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 15 (Cloud SQL) |
| Frontend | Next.js 14, React 18, TailwindCSS |
| Auth | JWT (python-jose), bcrypt |
| Cloud Storage | Google Cloud Storage (signed URLs) |
| Deployment | Google Cloud Run, Cloud Build |
| Containerization | Docker, docker-compose |
| Type Checking | Pyright, Pyre2 |

---

## Features

### 🌾 CTIS — Crop Timeline Intelligence System
- **Deterministic Replay Engine** — Rebuilds crop state from action logs with snapshot checkpoints
- **Crop State Machine** — Enforces valid state transitions (Created → Active → Harvested/Closed)
- **Stress Score Engine** — Multi-signal stress computation with deviation tracking
- **What-If Simulation** — Test hypothetical actions in isolated memory context (MSDD 1.14)
- **Drift Enforcement** — Clamps timeline drift to ±max per stage (MSDD 1.9)
- **Behavioral Adapter** — Detects recurring farmer patterns, computes bounded ±7 day offsets (ML Enhancement 6)
- **Temporal Anomaly Detection** — Rejects backdated/future-dated offline sync actions (MSDD 1.7.1)
- **Yield Verification** — Farmer Truth vs ML Truth separation with biological limit caps (MSDD 1.12)
- **Snapshot Manager** — Periodic checkpoints every N actions for fast replay recovery

### 🛒 SOE — Service Orchestration Ecosystem
- **Trust Score Engine** — 6-factor weighted trust computation with temporal decay
- **Exposure Fairness Engine** — Provider ranking with 70% exposure cap and regional saturation control
- **Fraud Detection** — 3-signal analysis (review patterns, rating spikes, timing anomalies)
- **Service Request Lifecycle** — State machine with event emission on every transition
- **Escalation Policy Engine** — Complaint routing and resolution workflows

### 🤖 ML Module
- **Risk Predictor** — Rule-based fallback with ML Kill Switch
- **Model Registry** — Version lifecycle management (register, activate, deactivate)

### 🔔 Notifications & Recommendations
- **Alert Service** — System-generated alerts with throttling (max 3 per crop per 24h)
- **Recommendation Engine** — Daily prioritized action suggestions based on stress/risk/stage

---

## API Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| **Auth** | `POST /api/v1/auth/register` | User registration |
| | `POST /api/v1/auth/login` | JWT login |
| **Crops** | `GET/POST /api/v1/crops/` | List/create crop instances |
| | `GET /api/v1/crops/{id}` | Crop detail with computed state |
| **Actions** | `POST /api/v1/crops/{id}/actions` | Log farmer action |
| **Simulation** | `POST /api/v1/crops/{id}/simulate` | What-if simulation |
| **Yield** | `POST /api/v1/crops/{id}/yield` | Submit harvest yield |
| **Recommendations** | `GET /api/v1/crops/{id}/recommendations` | Prioritized action suggestions |
| **Providers** | `GET/POST /api/v1/providers/` | Service provider CRUD |
| **Equipment** | `GET/POST /api/v1/equipment/` | Equipment management |
| **Service Requests** | `POST /api/v1/service-requests/` | Create/accept/complete requests |
| **Reviews** | `POST /api/v1/reviews/` | Submit service reviews |
| **Alerts** | `GET /api/v1/alerts/` | Farmer alerts |
| **Rules** | `GET/POST/PUT /api/v1/rules/` | Crop rule template CRUD |
| **Features** | `GET/PUT /api/v1/features/` | Feature flag management |
| **ML Models** | `GET/POST /api/v1/ml/models` | ML model registry |
| **Sync** | `POST /api/v1/offline-sync/` | Offline bulk action sync |
| **Admin** | `GET/PUT /api/v1/admin/*` | User management, provider governance |
| **Media** | `POST /api/v1/media/upload` | File uploads (GCS / local) |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | Crop cards with stats overview |
| Crop List | `/crops` | Filterable crop instance list |
| Crop Detail | `/crops/[id]` | Stats grid, timeline, action log |
| New Crop | `/crops/new` | Crop creation form |
| Yield Submission | `/crops/[id]/yield` | Harvest yield entry form |
| Log Action | `/crops/[id]/log-action` | Action logging form |
| Simulate | `/crops/[id]/simulate` | What-if simulation UI |
| Services | `/services` | Service marketplace |
| Labor | `/labor` | Labor management |
| Provider Dashboard | `/provider` | Provider-side overview |
| Admin | `/admin` | Admin dashboard with stats |
| User Management | `/admin/users` | User CRUD |
| Provider Management | `/admin/providers` | Provider governance |
| Health Monitor | `/admin/health` | System health dashboard |
| Dead Letters | `/admin/dead-letters` | Failed event queue |
| Templates | `/admin/templates` | Crop rule template management |
| Login | `/login` | JWT authentication |
| Register | `/register` | User registration |

---

## Project Structure

```
cultivax/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/             # 17 REST endpoint modules
│   │   ├── models/             # 26 SQLAlchemy models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ctis/           # Replay, stress, drift, simulation engines
│   │   │   ├── soe/            # Trust, exposure, fraud engines
│   │   │   ├── ml/             # Risk predictor, model registry
│   │   │   ├── event_dispatcher/  # DB-backed FIFO event processing
│   │   │   ├── notifications/  # Alert service with throttling
│   │   │   ├── recommendations/ # Priority-scored recommendations
│   │   │   ├── media/          # File upload service (GCS + local)
│   │   │   └── weather/        # Weather API integration
│   │   ├── middleware/         # Error handling, idempotency, rate limiting
│   │   └── security/          # JWT, password hashing, RBAC
│   ├── alembic/                # Database migrations
│   ├── scripts/                # Seed data & utilities
│   └── tests/                  # pytest test suite
├── frontend/                   # Next.js 14 frontend
│   └── src/
│       ├── app/                # 18 pages (App Router)
│       ├── components/         # 16 reusable UI components
│       ├── context/            # Auth context
│       ├── hooks/              # Custom hooks (useApi)
│       └── lib/                # API client, auth utilities
├── deploy/                     # Cloud Run deployment scripts
│   ├── deploy-backend.sh       # Build → push → deploy to Cloud Run
│   ├── run-migrations.sh       # Run Alembic migrations on Cloud SQL
│   └── setup-cloud-sql.sh      # Provision Cloud SQL instance
├── docs/                       # Project documentation (SRS, MSDD, TDD)
├── docker-compose.yml          # Local development setup
└── pyrightconfig.json          # Type checking configuration
```

---

## Prerequisites

Before you begin, ensure you have:

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| PostgreSQL | 15+ | Database (or use Docker) |
| Docker | 20.10+ | Containerized development |
| docker-compose | 2.0+ | Multi-service orchestration |
| gcloud CLI | Latest | Cloud Run deployment (optional) |

---

## Local Development Setup

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/malikarpit/cultivax.git
cd cultivax

# Start all services (PostgreSQL + backend + frontend)
docker-compose up -d

# Verify
curl http://localhost:8000/health     # Backend health check
open http://localhost:3000             # Frontend
open http://localhost:8000/docs        # API documentation (Swagger)
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate            # macOS/Linux
# venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Seed demo data (optional)
python -m scripts.seed_data

# Start the development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Ensure NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db` |
| `SECRET_KEY` | JWT signing key (**change in prod!**) | `your-secret-key-change-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `60` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:3000,http://localhost:8000` |
| `APP_ENV` | Environment (`development` / `production`) | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket (empty = local storage) | `""` |
| `GCS_SIGNED_URL_EXPIRY_MINUTES` | Signed URL expiry | `60` |
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL instance (for Cloud Run) | `""` |
| `CLOUD_SQL_DB_NAME` | Cloud SQL database name | `cultivax_db` |
| `CLOUD_SQL_DB_USER` | Cloud SQL user | `cultivax_user` |
| `CLOUD_SQL_DB_PASSWORD` | Cloud SQL password | `""` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## Database Setup

### Using Docker (automatic)

```bash
docker-compose up -d postgres
```

This starts PostgreSQL 15 on port 5432 with:
- User: `cultivax_user`
- Password: `cultivax_pass`
- Database: `cultivax_db`

### Using Local PostgreSQL

```bash
# Create database and user
psql -U postgres -c "CREATE USER cultivax_user WITH PASSWORD 'cultivax_pass';"
psql -U postgres -c "CREATE DATABASE cultivax_db OWNER cultivax_user;"

# Run migrations
cd backend
alembic upgrade head
```

### Seed Data

```bash
cd backend
python -m scripts.seed_data
```

Creates:
- 1 admin, 4 farmers, 3 providers (password: `Test@1234`)
- 3 crop rule templates (wheat, rice, cotton)
- 5 crop instances in various states
- 3 sample service requests

---

## Deployment (Google Cloud Run)

### 1. Set Up Cloud SQL

```bash
./deploy/setup-cloud-sql.sh <PROJECT_ID>
```

### 2. Deploy Backend

```bash
./deploy/deploy-backend.sh <PROJECT_ID> [REGION] [TAG]
```

This will:
- Enable required GCP APIs
- Build the Docker image via Cloud Build
- Deploy to Cloud Run with Cloud SQL connectivity
- Auto-run database migrations on startup

### 3. Run Migrations (Manual)

```bash
./deploy/run-migrations.sh <PROJECT_ID>
```

### 4. Verify Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe cultivax-backend \
  --project=<PROJECT_ID> --region=asia-south1 --format="value(status.url)")

# Health check
curl ${SERVICE_URL}/health

# API docs
open ${SERVICE_URL}/docs
```

---

## Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_soe_flow.py -v

# Run security tests
pytest tests/test_security.py -v
```

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Next.js UI    │────▶│   FastAPI REST    │────▶│   PostgreSQL     │
│  (React 18)     │     │   (17 endpoints)  │     │   (26 tables)    │
└─────────────────┘     └──────┬───────────┘     └──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │     CTIS     │   │     SOE      │   │   ML Module  │
   │ Replay Engine│   │ Trust Engine │   │ Risk Predict │
   │ State Machine│   │ Exposure Eng │   │ Model Regist │
   │ Stress Score │   │ Fraud Detect │   │ Kill Switch  │
   │ What-If Sim  │   │ Request Svc  │   └──────────────┘
   │ Drift Enforce│   │ Escalation   │
   │ Yield Verify │   └──────────────┘
   └──────────────┘
          │
   ┌──────────────┐   ┌──────────────┐
   │Event Dispatch │   │ Cloud Storage│
   │ DB-backed     │   │ GCS + Local  │
   │ FIFO Queue    │   │ Signed URLs  │
   └──────────────┘   └──────────────┘
```

---

## Team

| Member | Role | Key Contributions |
|--------|------|-------------------|
| **Arpit** | Lead | Backend architecture, CTIS engines (replay, stress, drift, simulation), event system, deployment |
| **Ayush Kumar Meena** | Backend | Auth system, middleware, admin APIs, feature flags, test fixtures |
| **Ravi Patel** | Backend | SOE module (trust engine, exposure fairness, fraud detection), service requests, reviews |
| **Prince** | Frontend | All UI pages (18), components (16), dashboard, crop management, admin panel |
| **Shivam Yadav** | Backend | ML module (risk predictor, model registry), media uploads, weather API, seed data |

---

## License

This project is developed as part of the Software Engineering course at FOT, DU.
