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
| Deployment | Google Cloud Run, Cloud Storage |
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
| **Media** | `POST /api/v1/media/upload` | File uploads |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | Crop cards with stats overview |
| Crop List | `/crops` | Filterable crop instance list |
| Crop Detail | `/crops/[id]` | Stats grid, timeline, action log |
| New Crop | `/crops/new` | Crop creation form |
| Log Action | `/crops/[id]/log-action` | Action logging form |
| Simulate | `/crops/[id]/simulate` | What-if simulation UI |
| Admin | `/admin` | Admin dashboard with stats |
| User Management | `/admin/users` | User CRUD |
| Provider Management | `/admin/providers` | Provider governance |
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
│   │   │   ├── media/          # File upload service
│   │   │   └── weather/        # Weather API integration
│   │   ├── middleware/         # Error handling, idempotency
│   │   └── security/          # JWT, password hashing, RBAC
│   ├── alembic/                # Database migrations
│   ├── data/                   # Seed data (crop rules)
│   └── tests/                  # pytest test suite
├── frontend/                   # Next.js 14 frontend
│   └── src/
│       ├── app/                # 12 pages (App Router)
│       ├── components/         # 11 reusable UI components
│       ├── context/            # Auth context
│       ├── hooks/              # Custom hooks (useApi)
│       └── lib/                # API client, auth utilities
├── docs/                       # Project documentation (SRS, design docs)
├── docker-compose.yml          # Local development setup
└── pyrightconfig.json          # Type checking configuration
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & docker-compose
- PostgreSQL 15 (or use Docker)

### Local Development

```bash
# Clone the repo
git clone https://github.com/malikarpit/cultivax.git
cd cultivax

# Start all services via Docker
docker-compose up -d

# Backend only
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm run dev
```

### API Documentation
Once running, visit: `http://localhost:8000/docs` (Swagger UI)

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
   ┌──────────────┐
   │Event Dispatch │
   │ DB-backed     │
   │ FIFO Queue    │
   └──────────────┘
```

---

## Team

| Member | Role | Key Contributions |
|--------|------|-------------------|
| **Arpit** | Lead | Backend architecture, CTIS engines (replay, stress, drift, simulation), event system, deployment |
| **Ayush Kumar Meena** | Backend | Auth system, middleware, admin APIs, feature flags, test fixtures |
| **Ravi Patel** | Backend | SOE module (trust engine, exposure fairness, fraud detection), service requests, reviews |
| **Prince** | Frontend | All UI pages (12), components (11), dashboard, crop management, admin panel |
| **Shivam Yadav** | Backend | ML module (risk predictor, model registry), media uploads, weather API, seed data |

---

## License

This project is developed as part of the Software Engineering course at FOT, DU.
