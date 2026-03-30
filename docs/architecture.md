# CultivaX — System Architecture Document

> **Version**: 1.0.0  
> **Last Updated**: March 30, 2026  
> **Authors**: Arpit Malik, Shivam Yadav

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [CTIS — Crop Timeline Intelligence System](#4-ctis--crop-timeline-intelligence-system)
5. [SOE — Service Orchestration Ecosystem](#5-soe--service-orchestration-ecosystem)
6. [Event Dispatcher](#6-event-dispatcher)
7. [ML Module](#7-ml-module)
8. [Media Pipeline](#8-media-pipeline)
9. [Notifications & Recommendations](#9-notifications--recommendations)
10. [Security Architecture](#10-security-architecture)
11. [Database Schema](#11-database-schema)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Data Flow Diagrams](#13-data-flow-diagrams)

---

## 1. System Overview

CultivaX is a **deterministic, event-driven** agricultural management platform designed for smallholder farmers. The system provides:

- **Chronologically accurate** crop timeline tracking with replay-safe architecture
- **Intelligent recommendations** based on stress, risk, and weather signals
- **Service marketplace** connecting farmers with equipment and labor providers
- **Offline-first** design supporting field conditions with limited connectivity

### Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Deterministic Replay** | All crop state is derived from ordered action logs via the Replay Engine |
| **Event Sourcing** | State transitions emit events processed by the DB-backed Event Dispatcher |
| **Chronological Invariant** | Actions must be temporally ordered — no backdating past the last action |
| **Dual-Truth Model** | Farmer-reported and ML-predicted values coexist without overwriting |
| **Fail-Safe ML** | ML predictions include confidence scores; kill switch for degraded models |
| **Offline Tolerance** | Temporal anomaly detection for sync'd offline actions |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT TIER                          │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │    Next.js UI     │    │  WhatsApp Bot    │  (future)    │
│  │  (React 18 / SSR) │    │  (Session-based) │              │
│  └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                         │
│           └───────┬───────────────┘                         │
│                   ▼                                         │
│           ┌──────────────┐                                  │
│           │  REST API     │  HTTPS / JWT Bearer             │
│           │  Gateway      │                                  │
│           └──────┬───────┘                                  │
└──────────────────┼──────────────────────────────────────────┘
                   │
┌──────────────────┼──────────────────────────────────────────┐
│              APPLICATION TIER (FastAPI)                      │
│                  │                                           │
│  ┌──────────┬────┴────┬──────────┬──────────┐              │
│  │ Middleware│  API v1 │  Deps    │  Security│              │
│  │ Layer    │  Router │  (DI)    │  Module  │              │
│  └────┬─────┴────┬────┴────┬─────┴────┬─────┘              │
│       │          │         │          │                      │
│  ┌────┴──────────┴─────────┴──────────┴─────┐              │
│  │           SERVICE LAYER                    │              │
│  │  ┌─────┐ ┌─────┐ ┌────┐ ┌─────┐ ┌──────┐│              │
│  │  │CTIS │ │ SOE │ │ ML │ │Media│ │Notif ││              │
│  │  │     │ │     │ │    │ │     │ │      ││              │
│  │  └──┬──┘ └──┬──┘ └─┬──┘ └──┬──┘ └──┬───┘│              │
│  │     └───────┴──────┴───────┴───────┘     │              │
│  │              Event Dispatcher             │              │
│  └──────────────────┬───────────────────────┘              │
│                     │                                       │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│               DATA TIER                                      │
│  ┌──────────────────┴──────────────┐  ┌────────────────┐    │
│  │  PostgreSQL 15                   │  │ Google Cloud   │    │
│  │  (Cloud SQL)                     │  │ Storage (GCS)  │    │
│  │  26 tables, Alembic migrations   │  │ Signed URLs    │    │
│  └─────────────────────────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Backend Architecture

### Application Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app initialization, middleware, lifecycle events
│   ├── config.py               # Settings via pydantic-settings (env-based)
│   ├── database.py             # SQLAlchemy engine, session factory, get_db dependency
│   ├── api/
│   │   ├── deps.py             # Dependency injection: get_current_user, RBAC
│   │   └── v1/
│   │       ├── router.py       # Aggregates all 18 route modules
│   │       ├── auth.py         # Registration, login, token refresh
│   │       ├── crops.py        # Crop CRUD with seasonal window
│   │       ├── actions.py      # Action logging with chronological validation
│   │       ├── simulation.py   # What-if simulation endpoint
│   │       ├── yield.py        # Harvest yield submission
│   │       └── ...             # 12 more endpoint modules
│   ├── models/                 # 26 SQLAlchemy ORM models
│   ├── schemas/                # Pydantic v2 request/response schemas
│   ├── services/               # Business logic layer
│   │   ├── ctis/               # 10 CTIS engines
│   │   ├── soe/                # 5 SOE engines
│   │   ├── ml/                 # 2 ML services
│   │   ├── event_dispatcher/   # DB-backed event system
│   │   ├── notifications/      # Alert service
│   │   ├── recommendations/    # Recommendation engine
│   │   ├── media/              # Upload + analysis
│   │   └── weather/            # External weather API
│   ├── middleware/             # Error handling, idempotency, rate limiting
│   └── security/              # JWT, password hashing, RBAC guards
├── alembic/                    # Database migrations
├── tests/                      # pytest test suite (10 test modules)
└── scripts/                    # Seed data, utilities
```

### Middleware Stack

Middleware is applied in order (outermost executes first):

```
Request → ErrorHandler → RateLimit → Idempotency → CORS → Route Handler → Response
```

| Middleware | Purpose |
|-----------|---------|
| `ErrorHandlerMiddleware` | Catches unhandled exceptions, returns structured error responses |
| `RateLimitMiddleware` | Per-IP request rate limiting with configurable limits |
| `IdempotencyMiddleware` | Caches responses by `Idempotency-Key` header for safe retries |
| `CORSMiddleware` | Cross-origin resource sharing for frontend communication |

### Dependency Injection

FastAPI's `Depends()` system provides:

| Dependency | Provider | Usage |
|-----------|----------|-------|
| `get_db` | `database.py` | Database session per request |
| `get_current_user` | `api/deps.py` | JWT validation → User object |
| `require_role(role)` | `api/deps.py` | RBAC enforcement |

---

## 4. CTIS — Crop Timeline Intelligence System

CTIS is the core subsystem that maintains chronologically accurate crop state. All crop state is **derived** — never directly mutated — through deterministic replay of ordered action logs.

### Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       CTIS Module                            │
│                                                              │
│  ┌─────────────┐     ┌─────────────────┐                    │
│  │ CropService  │────▶│  Replay Engine   │                    │
│  │ (CRUD + API) │     │  (Deterministic) │                    │
│  └──────┬──────┘     └────┬──────┬──────┘                    │
│         │                 │      │                            │
│    ┌────┴────┐    ┌───────┘      └────────┐                  │
│    │         │    │                        │                  │
│  ┌─┴──────┐ ┌┴──────────┐  ┌──────────────┴──┐              │
│  │Action  │ │State      │  │Snapshot Manager  │              │
│  │Service │ │Machine    │  │(Checkpointing)   │              │
│  └────────┘ └───────────┘  └─────────────────┘              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │Stress Engine │  │Drift Enforcer│  │Deviation Tracker │   │
│  │(Multi-signal)│  │(±max/stage)  │  │(Profile + Bias)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │What-If Engine│  │Risk Calculator│  │Behavioral Adapter│   │
│  │(Simulation)  │  │(Composite)   │  │(±7 day offsets)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────────┐                      │
│  │Yield Service │  │Seasonal Window   │                      │
│  │(Dual Truth)  │  │(Calendar Assign) │                      │
│  └──────────────┘  └──────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

### Replay Engine

The Replay Engine is the heart of CTIS. It rebuilds crop state by replaying all action logs in chronological order.

**Algorithm:**
1. Load the most recent snapshot (if any) to skip already-replayed actions
2. Load remaining actions from the action log, ordered by `effective_date`
3. For each action, apply it through the State Machine
4. Compute stress score after each action via the Stress Engine
5. Enforce drift limits via the Drift Enforcer
6. Save a new snapshot every N actions for performance

**Guarantees:**
- Same action sequence → same final state (determinism)
- Snapshot isolation: replay never touches real DB during simulation
- Circuit breaker: if replay fails 3 times, it halts and raises an alert

### State Machine

Valid state transitions for crop instances:

```
     ┌──────────┐
     │ CREATED  │
     └────┬─────┘
          │ (sowing date reached)
     ┌────▼─────┐
     │  ACTIVE  │
     └──┬────┬──┘
        │    │
  ┌─────▼┐  ┌▼──────────┐
  │HARV- │  │  CLOSED    │
  │ESTED │  │ (abnormal) │
  └──────┘  └────────────┘
```

### Stress Score Engine

Multi-signal stress computation:

```
stress_score = w1 * weather_stress
             + w2 * pest_stress
             + w3 * nutrient_stress
             + w4 * water_stress
             + w5 * growth_deviation
```

Where each component is normalized to [0, 1] range with stage-aware weighting.

### What-If Simulation

1. Deep-copy the crop's current state into an isolated memory context
2. Apply hypothetical actions through the same replay pipeline
3. Compute projected stress, risk, and growth stage
4. Return delta metrics (change from current state)
5. **No mutations** to the real database

---

## 5. SOE — Service Orchestration Ecosystem

SOE manages the service marketplace connecting farmers with equipment/labor providers.

### Component Architecture

```
┌─────────────────────────────────────────────┐
│                SOE Module                    │
│                                              │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │Provider Service  │  │Request Service   │  │
│  │(CRUD + Search)   │  │(State Machine)   │  │
│  └────────┬────────┘  └────────┬─────────┘  │
│           │                    │              │
│  ┌────────▼────────┐  ┌───────▼──────────┐  │
│  │ Trust Engine     │  │Escalation Policy │  │
│  │ (6-factor score) │  │(Complaint Route) │  │
│  └────────┬────────┘  └──────────────────┘  │
│           │                                  │
│  ┌────────▼────────┐  ┌──────────────────┐  │
│  │Exposure Fairness│  │Fraud Detector    │  │
│  │(70% cap + rank) │  │(3-signal)        │  │
│  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────┘
```

### Trust Score Engine

The trust score is a composite metric computed from 6 weighted factors:

```
trust_score = (
    w_rating   * avg_rating           +
    w_complete * completion_rate       +
    w_response * response_time_score   +
    w_age      * account_age_score     +
    w_review   * review_consistency    +
    w_decay    * temporal_decay_factor
)
```

Features:
- **Temporal decay**: Score decays over time without activity
- **Consistency scoring**: Penalizes rating volatility
- **Fraud resistance**: Anomalous review patterns reduce trust

### Exposure Fairness Engine

Prevents marketplace monopolization:

- **70% exposure cap**: No provider gets more than 70% of search impressions
- **Regional saturation control**: Distributes exposure across providers in same region
- **Trust-weighted ranking**: Higher trust = higher default rank, but capped

### Fraud Detection

3-signal analysis engine:

| Signal | Detection Method |
|--------|-----------------|
| **Review Pattern** | Sudden rating spikes, repetitive review text |
| **Timing Anomaly** | Reviews submitted abnormally fast after service completion |
| **Rating Distribution** | Statistical outlier detection on provider's rating curve |

---

## 6. Event Dispatcher

The event system enables loose coupling between subsystems via a database-backed FIFO queue.

### Architecture

```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│   Producer     │────▶│  event_log      │────▶│  Consumer      │
│ (API Handler)  │     │  (PostgreSQL)   │     │ (Background    │
│                │     │                 │     │  Loop)         │
└────────────────┘     └─────────────────┘     └───────┬────────┘
                                                       │
                                               ┌───────▼────────┐
                                               │   Handlers     │
                                               │ ┌────────────┐ │
                                               │ │CTIS Handler│ │
                                               │ │SOE Handler │ │
                                               │ │ML Handler  │ │
                                               │ │Alert Handlr│ │
                                               │ └────────────┘ │
                                               └────────────────┘
```

### Event Lifecycle

```
Created → Processing → Completed
              │
              └──→ Failed → (retry) → Processing
                      │
                      └──→ DeadLettered (max retries exceeded)
```

### Background Processor

- Runs as an `asyncio.Task` created on FastAPI startup
- Polls `event_log` table every 5 seconds for `Created` events
- Processes events in FIFO order
- **Crash recovery**: On startup, resets any events stuck in `Processing` state
- **Circuit breaker**: After 3 consecutive handler failures, pauses processing for 60 seconds
- **Graceful shutdown**: Waits up to 10 seconds for current event to complete

---

## 7. ML Module

### Risk Predictor

Provides crop risk scores with a rule-based fallback:

```
if ml_enabled AND model_available AND dataset_size >= 200:
    return ml_model.predict(features)
else:
    return rule_based_prediction(crop_state, weather, stage)
```

**Features Used:**
- Current growth stage
- Days since last action
- Stress score history
- Weather forecast
- Deviation profile

### Model Registry

Manages ML model versions with lifecycle states:

```
Registered → Active → Deactivated
                │
                └──→ Deprecated
```

Only one model per type can be active at a time. Activation automatically deactivates the previous version.

### Kill Switch

The global `ml_enabled` feature flag immediately falls back all ML predictions to rule-based when disabled. This is critical for:
- Model degradation scenarios
- Data quality issues
- Emergency response

---

## 8. Media Pipeline

### Upload Flow

```
Client → POST /media/upload → Upload Service → Storage Backend → MediaFile record
                                    │
                                    ├── GCS (production)
                                    │   └── Returns signed URL (expiry: 60 min)
                                    └── Local (development)
                                        └── Saves to uploads/ directory
```

### Analysis Service

Processes uploaded media asynchronously via the Event Dispatcher:

1. **Image quality validation** — Blur/brightness scoring
2. **Growth stage detection** — CNN-based classification (stub)
3. **Stress identification** — Visual stress indicators (stub)
4. **Event emission** — `MediaAnalyzed` event with results

---

## 9. Notifications & Recommendations

### Alert Service

Generates system alerts based on:
- High stress scores exceeding thresholds
- Drift enforcement violations
- Service request state changes
- ML model confidence drops

**Throttling**: Maximum 3 alerts per crop per 24-hour sliding window.

### Recommendation Engine

Daily recommendation generation pipeline:

1. Query all active crops
2. For each crop, compute priority score:
   ```
   priority = stress_weight * stress_score
            + risk_weight * risk_index
            + stage_weight * stage_urgency
            + weather_weight * weather_factor
   ```
3. Generate top-N recommendations per crop
4. Filter out recently dismissed recommendations

---

## 10. Security Architecture

### Authentication Flow

```
┌────────┐     ┌─────────┐     ┌──────────┐
│ Client │────▶│ /login   │────▶│ Verify   │
│        │     │          │     │ Password │
│        │◀────│          │◀────│ + Issue  │
│  JWT   │     │          │     │   JWT    │
└────────┘     └─────────┘     └──────────┘
     │
     │  Authorization: Bearer <token>
     ▼
┌────────┐     ┌─────────┐     ┌──────────┐
│ Client │────▶│ API v1   │────▶│ Verify   │
│        │     │          │     │ JWT +    │
│        │     │          │     │ RBAC     │
└────────┘     └─────────┘     └──────────┘
```

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "role": "farmer",
  "exp": 1711800000,
  "iat": 1711796400,
  "type": "access"
}
```

### Security Layers

| Layer | Implementation |
|-------|---------------|
| **Password Storage** | bcrypt hashing with salt |
| **JWT Tokens** | HS256 signed, configurable expiry |
| **Refresh Tokens** | Separate longer-lived tokens for session continuity |
| **RBAC** | Role-based access via `require_role()` dependency |
| **Rate Limiting** | Per-IP rate limits with configurable thresholds |
| **Idempotency** | `Idempotency-Key` header prevents duplicate mutations |
| **CORS** | Whitelisted origins only |
| **Input Validation** | Pydantic v2 schema validation on all inputs |

---

## 11. Database Schema

### Entity Relationship Overview

The database contains **26 tables** organized into subsystem groups:

#### Core (CTIS)
| Table | Description |
|-------|-------------|
| `users` | User accounts with role, region, preferences |
| `crop_instances` | Crop lifecycle state, sowing date, seasonal window |
| `action_logs` | Chronologically ordered farmer actions |
| `snapshots` | Replay checkpoint state captures |
| `deviation_profiles` | Per-crop deviation tracking |
| `yield_records` | Farmer Truth + ML Truth yield data |
| `crop_rule_templates` | Growth stage rules with versioning |
| `regional_sowing_calendars` | Region-based seasonal window data |

#### SOE
| Table | Description |
|-------|-------------|
| `service_providers` | Provider profiles with trust scores |
| `equipment` | Equipment inventory per provider |
| `labor` | Labor availability records |
| `service_requests` | Request lifecycle with state machine |
| `service_request_events` | State transition audit trail |
| `service_reviews` | Farmer reviews with ratings |
| `provider_availability` | Schedule and capacity |

#### System
| Table | Description |
|-------|-------------|
| `event_log` | Event dispatcher queue |
| `admin_audit` | Admin action audit trail |
| `feature_flags` | Feature toggle states |
| `abuse_flags` | Manipulation detection records |
| `media_files` | Uploaded file metadata |
| `alerts` | System-generated notifications |
| `recommendations` | Action suggestions |
| `system_health` | Subsystem health records |

#### ML & Analytics
| Table | Description |
|-------|-------------|
| `ml_models` | Model version registry |
| `ml_training` | Training job audit log |
| `stress_history` | Historical stress scores |
| `regional_clusters` | Regional farm groupings |

### Migration Strategy

Alembic manages database migrations with 8 migration files:

```
001_create_users.py
002_create_ctis_tables.py
003_create_soe_tables.py
004_create_system_tables.py
005_create_ml_analytics_tables.py
006_create_sowing_calendar.py
007_create_remaining_tables_add_columns.py
008_create_phase2_tables.py
```

---

## 12. Deployment Architecture

### Google Cloud Run

```
┌─────────────────────────────────────────────────┐
│                 Google Cloud                     │
│                                                  │
│  ┌──────────────┐    ┌──────────────────────┐   │
│  │ Cloud Build   │───▶│ Container Registry   │   │
│  │ (CI/CD)       │    │ (Docker images)      │   │
│  └──────────────┘    └──────────┬───────────┘   │
│                                 │                │
│  ┌──────────────────────────────▼──────────┐    │
│  │          Cloud Run Service               │    │
│  │  ┌────────────────────────────────────┐  │    │
│  │  │  cultivax-backend                   │  │    │
│  │  │  (FastAPI + Uvicorn)               │  │    │
│  │  │  Auto-scaling: 0 → 10 instances    │  │    │
│  │  └─────────────┬──────────────────────┘  │    │
│  └────────────────┼─────────────────────────┘    │
│                   │                               │
│  ┌────────────────▼─────────────────────────┐    │
│  │          Cloud SQL (PostgreSQL 15)        │    │
│  │  ┌────────────────────────────────────┐  │    │
│  │  │  Instance: cultivax-db-instance    │  │    │
│  │  │  Database: cultivax_db             │  │    │
│  │  │  Region: asia-south1              │  │    │
│  │  └────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │          Cloud Storage (GCS)              │    │
│  │  Bucket: cultivax-media                   │    │
│  │  Signed URLs for secure access            │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### Docker Configuration

The backend Dockerfile uses a multi-stage approach:

```dockerfile
# Stage 1: Dependencies
FROM python:3.11-slim AS base
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application
FROM base
COPY app/ /app/app/
COPY alembic/ /app/alembic/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Local Development

`docker-compose.yml` orchestrates:

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL 15 database |
| `backend` | 8000 | FastAPI backend (hot reload) |
| `frontend` | 3000 | Next.js frontend (hot reload) |

---

## 13. Data Flow Diagrams

### Action Logging Flow

```
Farmer → POST /crops/{id}/actions
           │
           ▼
     ActionService.log_action()
           │
           ├── Validate chronological invariant
           ├── Check idempotency key
           ├── Insert ActionLog record
           ├── Trigger replay via ReplayEngine
           │        │
           │        ├── Load latest snapshot
           │        ├── Replay remaining actions
           │        ├── Compute stress via StressEngine
           │        ├── Enforce drift via DriftEnforcer
           │        └── Save new snapshot (if checkpoint)
           │
           ├── Emit "ActionLogged" event
           │        │
           │        └── EventDispatcher → DB event_log
           │              │
           │              └── Background processor
           │                    ├── Update deviation profile
           │                    ├── Generate recommendations
           │                    └── Create alerts (if threshold)
           │
           └── Return ActionLogResponse
```

### Service Request Flow

```
Farmer → POST /service-requests/
           │
           ▼
     RequestService.create()
           │
           ├── Validate farmer identity
           ├── Insert ServiceRequest (state: CREATED)
           ├── Emit "ServiceRequested" event
           └── Return ServiceRequest
                    │
    Provider ← GET /service-requests/ (filtered)
           │
           ▼
     PUT /service-requests/{id}/accept
           │
           ├── State: CREATED → ACCEPTED
           ├── Emit "ServiceAccepted" event
           └── Alert: Notify farmer

    Provider → PUT /service-requests/{id}/complete
           │
           ├── State: ACCEPTED → COMPLETED
           ├── Emit "ServiceCompleted" event
           ├── Update trust score via TrustEngine
           └── Alert: "Service completed — please review"

    Farmer → POST /reviews/
           │
           ├── Verify eligibility (request is COMPLETED)
           ├── Insert Review
           ├── Recalculate provider trust score
           ├── Check fraud signals
           └── Emit "ReviewSubmitted" event
```

---

## Appendix A: Technology Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI** over Django | Async support, auto-generated OpenAPI docs, better performance |
| **SQLAlchemy 2.0** over raw SQL | Type-safe ORM with migration support, complex relationship modeling |
| **DB-backed events** over message queue | Transactional consistency, simpler infrastructure, sufficient for current scale |
| **Deterministic replay** over mutable state | Audit trail, debugging, simulation support, temporal consistency |
| **Pydantic v2** for validation | Runtime type safety, auto-serialization, OpenAPI schema generation |
| **Next.js** for frontend | SSR for SEO, file-system routing, React Server Components |

## Appendix B: Scalability Considerations

| Component | Current | Scale Target |
|-----------|---------|-------------|
| Database | Single Cloud SQL instance | Read replicas + connection pooling |
| Event Processing | Single background task | Multiple workers with partitioned queues |
| Media Storage | GCS with signed URLs | CDN layer for frequently accessed assets |
| API | Single Cloud Run service | Auto-scaling 0–10 instances |
| Search | SQL LIKE queries | Full-text search index for providers |
