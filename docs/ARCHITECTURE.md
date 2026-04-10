# CultivaX — System Architecture

> **Last Updated:** April 2026  
> **Version:** Phase 3 (Production-Ready)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [CTIS — Crop Timeline Intelligence System](#3-ctis--crop-timeline-intelligence-system)
4. [SOE — Service Orchestration Ecosystem](#4-soe--service-orchestration-ecosystem)
5. [ML Module](#5-ml-module)
6. [Event Dispatcher](#6-event-dispatcher)
7. [Notification & Recommendation Engine](#7-notification--recommendation-engine)
8. [Security Architecture](#8-security-architecture)
9. [Database Schema Overview](#9-database-schema-overview)
10. [API Layer](#10-api-layer)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [Key Design Decisions & Rationale](#13-key-design-decisions--rationale)
14. [Explicitly Deferred Features](#14-explicitly-deferred-features)

---

## 1. System Overview

CultivaX is a **deterministic, event-driven agricultural management platform** built for Indian farmers. It tracks crop lifecycles with chronological accuracy, connects farmers to service providers, discovers government schemes, and provides AI-backed recommendations — intelligently degrading when connectivity is poor.

### Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Determinism** | Replay engine reconstructs crop state identically from action logs every time |
| **Event-only mutation** | All CTIS state changes go through the event dispatcher; direct writes are blocked at the DB session level |
| **Soft delete everywhere** | No hard deletes on any major table — all records carry `is_deleted`, `deleted_at`, `deleted_by` |
| **Idempotency** | Every mutation endpoint uses an `Idempotency-Key` header; duplicate requests are identified by `event_hash` UNIQUE constraint |
| **Graceful degradation** | ML predictions fall back to deterministic rule-based logic when models are unavailable |
| **Offline-first** | Actions logged offline are queued and synced via bulk endpoint with temporal anomaly detection |

---

## 2. High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                   Next.js 14 Frontend (PWA)                     │
│  30+ pages  ·  5 languages  ·  Offline queue  ·  SWR cache     │
└──────────────────────────┬─────────────────────────────────────┘
                           │ HTTPS / REST
                           │ JWT Bearer tokens
┌──────────────────────────▼─────────────────────────────────────┐
│              FastAPI Backend — Python 3.11                       │
│   30+ API modules  ·  Pydantic v2 validation  ·  JWT RBAC      │
│   Idempotency middleware  ·  Rate limiting  ·  Correlation IDs  │
└──────┬──────────────────┬───────────────────┬──────────────────┘
       │                  │                   │
  ┌────▼──────┐    ┌──────▼──────┐    ┌───────▼───────┐
  │   CTIS    │    │    SOE      │    │   ML Module   │
  │           │    │             │    │               │
  │ Replay    │    │ Trust Eng   │    │ Risk Predictor│
  │ State     │    │ Exposure    │    │ Model Registry│
  │ Machine   │    │ Fraud Det   │    │ Inference     │
  │ Stress    │    │ Escalation  │    │ Audit Trail   │
  │ Drift Enf │    │ Request Svc │    │ Kill Switch   │
  │ WhatIf    │    │ Labor Mgmt  │    └───────────────┘
  │ Yield Svc │    └─────────────┘
  └─────┬─────┘
        │ All state changes via events only
┌───────▼──────────────────────────────────────────────────────┐
│                   Event Dispatcher (DB-backed)                  │
│   publish() → event_log table → process_pending_events()        │
│   FIFO per partition  ·  SKIP LOCKED  ·  Dead Letter Queue      │
└───────────────────────────────────────────────────────────────┘
        │                         │                    │
┌───────▼───────┐    ┌────────────▼────┐    ┌─────────▼─────────┐
│  PostgreSQL   │    │  Cloud Storage  │    │  SMS / Twilio     │
│  35+ tables   │    │  Media uploads  │    │  OTP + Alerts     │
│  15+ migrations│   │  Signed URLs    │    │  (stub in dev)    │
└───────────────┘    └─────────────────┘    └───────────────────┘
```

---

## 3. CTIS — Crop Timeline Intelligence System

CTIS is the heart of CultivaX. It maintains a chronologically accurate, deterministic record of every crop's lifecycle.

### 3.1 Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Replay Engine** | `services/ctis/replay_engine.py` | Rebuilds crop state by re-applying all action logs from the beginning (or from latest snapshot). Uses `SELECT FOR UPDATE` row locking to prevent concurrent replays. |
| **State Machine** | `services/ctis/state_machine.py` | Enforces valid crop state transitions. Transitions emit `StageChanged` events. |
| **Stress Engine** | `services/ctis/stress_engine.py` | Multi-signal stress integration: ML risk + weather + deviation penalty + edge signal, with exponential smoothing. |
| **Risk Calculator** | `services/ctis/risk_calculator.py` | Computes `risk_index = weather_risk × 0.7 + farmer_signal × 0.3`, clamped to [0,1]. |
| **Risk Pipeline** | `services/ctis/risk_pipeline.py` | Unified adapter so Replay Engine and What-If Engine use the identical risk computation path (prevents result divergence). |
| **Drift Enforcer** | `services/ctis/drift_enforcer.py` | Clamps `stage_offset_days` to `max_allowed_drift` per lifecycle stage. |
| **Snapshot Manager** | `services/ctis/snapshot_manager.py` | Creates periodic checkpoints every N actions for fast replay recovery without re-processing the full history. |
| **What-If Engine** | `services/ctis/whatif_engine.py` | Deep-copies the entire crop state (stress history, deviation history, seasonal category, weather snapshot) into isolated memory. Runs replay. **Never persists**. |
| **Yield Service** | `services/ctis/yield_service.py` | Handles yield submission. Separates Farmer Truth (raw reported yield, immutable) from ML Truth (capped at biological limit). Updates regional clusters prospectively only. |
| **Behavioral Adapter** | `services/ctis/behavioral_adapter.py` | Detects recurring farmer timing patterns (consistently early/late irrigations etc.) and applies a bounded ±N day offset. Reversible. Expires at season end. Never modifies baseline rule template. |
| **Deviation Tracker** | `services/ctis/deviation_tracker.py` | Tracks `consecutive_deviation_count`, `deviation_trend_slope`, and `recurring_pattern_flag`. |
| **Seasonal Window** | `services/ctis/seasonal_window.py` | Assigns `Early/Optimal/Late` seasonal category on crop creation by comparing sowing date against `regional_sowing_calendars`. Frozen at creation — never changes. |
| **Sync Service** | `services/ctis/sync_service.py` | Validates bulk offline action submissions. Detects temporal anomalies (backdated actions, future actions, batch size anomalies, monotonic counter resets). Flags to `abuse_flags` when anomaly score exceeds threshold. |
| **Action Service** | `services/ctis/action_service.py` | Validates individual action chronological invariants, inserts `action_log`, publishes `ActionLogged` event. |
| **Crop Service** | `services/ctis/crop_service.py` | CRUD for `CropInstance`. State changes happen via event publish, not direct DB writes. |
| **Regional Cluster Service** | `services/ctis/regional_cluster_service.py` | Incremental (streaming) update of `regional_clusters` table from new yield submissions, using running average. Prospective only. |

### 3.2 Crop State Machine

```
                        ┌─────────────┐
                        │   Created   │──────────────────────────┐
                        └──────┬──────┘                          │
                               │                                 │
                        ┌──────▼──────┐                          │
                        │   Active    │◄────────────────┐        │
                        └──┬──────┬───┘                 │        │
                           │      │                     │        │
               ┌───────────▼──┐  ┌▼──────────┐         │        │
               │   Delayed    │  │  AtRisk    │─────────┘        │
               └───────┬──────┘  └──────┬─────┘                  │
                       │                │                         │
                       └────────┬───────┘                         │
                                │                                 │
                      ┌─────────▼──────────┐                      │
                      │  ReadyToHarvest    │                      │
                      └─────────┬──────────┘                      │
                                │                                 │
                      ┌─────────▼──────────┐                      │
                      │     Harvested      │                      │
                      └─────────┬──────────┘                      │
                                │                                 │
                      ┌─────────▼──────────┐                      │
                      │      Closed        │                      │
                      └─────────┬──────────┘                      │
                                │                                 │
                      ┌─────────▼──────────┐                      │
                      │      Archived      │                      │
                      └────────────────────┘                      │
                                                                  │
                      ┌────────────────────┐                      │
                      │  RecoveryRequired  │◄─────────────────────┘
                      │  (replay failure)  │  (Admin resolves → Active)
                      └────────────────────┘
```

Every transition emits a `StageChanged` event. Direct writes to `CropInstance.state` are blocked at the SQLAlchemy session level by a `before_flush` hook (mutation guard).

### 3.3 Replay Algorithm (TDD 4.4)

```
1. Acquire SELECT FOR UPDATE row lock on CropInstance
2. Load latest snapshot (if any)
3. Load action_logs ordered chronologically after snapshot
4. For each action:
   a. Validate chronological invariants
   b. Apply action (stress += deviation_penalty etc.)
   c. Compute stress via multi-signal integration
   d. Compute risk_index via unified RiskPipeline
   e. Enforce stage_offset_days drift clamp
   f. Check/create snapshot if action count threshold met
5. Update CropInstance row (inside allow_ctis_mutation() context)
6. Commit transaction

On failure:
   - Lock CropInstance, set state = 'RecoveryRequired'
   - Log error, notify admin
   - Block further action logging until resolved
```

### 3.4 Yield Verification (MSDD 1.12, 4.3)

| Truth Type | Field | Mutability |
|-----------|-------|------------|
| **Farmer Truth** | `reported_yield` | Immutable — shown as-is to farmer forever |
| **ML Truth** | `ml_yield_value` | Capped at biological limit. Used for model training only. |
| **Regional Truth** | `regional_clusters.avg_yield` | Updated prospectively only (new yields). Historical yields are never rewritten. |

---

## 4. SOE — Service Orchestration Ecosystem

### 4.1 Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Provider Service** | `services/soe/provider_service.py` | Provider CRUD, verification lifecycle (Pending → Verified → Suspended → Rejected). Unverified providers excluded from marketplace. |
| **Trust Engine** | `services/soe/trust_engine.py` | Computes provider trust score (0-1). |
| **Exposure Engine** | `services/soe/exposure_engine.py` | Ranks providers for marketplace with fairness constraints. |
| **Fraud Detector** | `services/soe/fraud_detector.py` | Detects review pattern anomalies, rating spikes, and IP correlations. |
| **Escalation Policy** | `services/soe/escalation_policy.py` | Evaluates complaint ratio → Warning / TemporarySuspension / PermanentSuspension. |
| **Request Service** | `services/soe/request_service.py` | Service request lifecycle. Emits `ServiceRequestEvent` on every state transition. |

### 4.2 Trust Score Formula (TDD 5.5, SOE Enhancements 2, 5)

```
trust = w1 × CompletionRate
      + w2 × (1 − ComplaintRatio)
      + w3 × NormalizedRating
      + w4 × VerificationBonus
      + w5 × ConsistencyScore
      - w6 × EscalationPenalty

ConsistencyScore = 1 − variance(completion_time, resolution_score)   ← SOE Enhancement 5
trust *= 0.98 per month of inactivity                                 ← SOE Enhancement 2 (temporal decay)
trust  = clamp(trust, 0.0, 1.0)
```

### 4.3 Exposure Fairness Algorithm (SOE Enhancement 1, 9, 11)

```
ranking_score = trust_score × 0.85
              + random_factor × 0.10
              + regional_weight × 0.05
```

**Constraints:**
- Top 3 providers cannot exceed 70% combined exposure over rolling 30 days
- Regional Saturation Control: if a micro-region is over-saturated, enforce minimum exposure rotation for less-visible providers
- Providers with `is_flagged=True` (fraud detection) get reduced trust weight
- Trust score breakdown shown in farmer UI (weight constants hidden)

### 4.4 Service Request State Machine

```
Created → Accepted → InProgress → Completed → (Review submitted)
       ↘ Rejected
       ↘ Cancelled
```

Every transition writes a row to `service_request_events` table with `event_type`, `previous_state`, `new_state`, `actor_id`, `actor_role`, `timestamp`.

### 4.5 SOE ↔ CTIS Isolation (SOE Enhancement 6)

SOE modules **cannot directly mutate CTIS state** (`CropInstance.state`, `CropInstance.stage`, etc.). This is enforced by:
1. Architectural invariant test (`test_architecture_invariants.py`)
2. SQLAlchemy `before_flush` mutation guard that raises `RuntimeError` on any direct CTIS field write outside the event handler context

---

## 5. ML Module

| Component | File | Responsibility |
|-----------|------|----------------|
| **Risk Predictor** | `services/ml/risk_predictor.py` | Primary ML inference path. Falls back to deterministic rule-based scoring when no active model is registered or ML Kill Switch is enabled. |
| **Inference Runtime** | `services/ml/inference_runtime.py` | Loads registered model artifact (`joblib`), caches in memory, executes `predict_proba`. |
| **Model Registry** | `services/ml/model_registry.py` | Manages model versions: register → activate → deactivate. Only one model can be `Active` at a time. |

### 5.1 Every ML Output Includes (ML Enhancement 2 — Confidence Propagation)

```json
{
  "risk_probability": 0.72,
  "confidence_score": 0.85,
  "data_sufficiency_index": 0.91,
  "model_version": "v2",
  "inference_source": "registry_ml_inference"
}
```

Low confidence → softer recommendation tone. `risk_adjusted = prediction × confidence`.

### 5.2 ML Kill Switch (ML Enhancement 10)

Feature flags (`ml_enabled`, `clustering_enabled`, `risk_prediction_enabled`, `behavioral_adaptation_enabled`) can be toggled from the admin panel. When `ml_enabled=False`, the system falls back entirely to the rule-based risk calculator. The CTIS engine continues operating deterministically.

### 5.3 Every Inference is Audited

Each call to `RiskPredictor.predict()` writes a row to `ml_inference_audit` with: `crop_instance_id`, `model_id`, `model_version`, `inference_source`, `features` (JSONB), `output` (JSONB). Queryable via `GET /api/v1/ml/inference-audits`.

---

## 6. Event Dispatcher

### 6.1 Why DB-Backed (Not Redis/Kafka)

Using the application's PostgreSQL as the event bus was a deliberate design decision:
- **Zero extra infrastructure** — no Redis, no Kafka, no separate broker to maintain
- **ACID-safe** — events are committed in the same transaction as the mutation that caused them
- **Survives restarts** — events in `Created` status are re-processed after any crash
- **Idempotency** — `event_hash` UNIQUE constraint prevents duplicate processing under retries

### 6.2 Processing Model

```
publish(event_type, entity_type, entity_id, payload)
  └─ INSERT INTO event_log (status='Created', event_hash=sha256(...))

Background loop (every 2 seconds):
  SELECT * FROM event_log
  WHERE status = 'Created'
  ORDER BY created_at ASC
  FOR UPDATE SKIP LOCKED     ← Safe for multi-worker deployment
  LIMIT 50

  For each event:
    status → 'Processing'
    call handler(db, event)
    status → 'Processed'

  On failure (max 3 retries):
    status → 'DeadLetter'
```

### 6.3 Event Type Catalog

| Category | Event Types |
|----------|------------|
| **CTIS** | `ActionLogged`, `ReplayTriggered`, `StageChanged`, `StressUpdated`, `YieldSubmitted` |
| **SOE** | `ServiceRequested`, `ProviderContacted`, `RequestCompleted`, `ReviewSubmitted` |
| **ML** | `RiskComputed`, `MediaAnalyzed`, `ClusterUpdated`, `ModelRegistered` |
| **Admin** | `UserRoleChanged`, `ProviderVerified`, `ProviderSuspended`, `FeatureToggled` |
| **Notification** | `AlertGenerated`, `RecommendationCreated`, `AlertAcknowledged` |
| **CTIS Mutation** | `ctis.crop_state_change_requested`, `ctis.crop_metrics_update_requested` |

### 6.4 Dead Letter Queue

Events that fail after 3 retries are moved to `DeadLetter` status. Admins can:
- `GET /api/v1/admin/dead-letters` — list all failed events
- `POST /api/v1/admin/dead-letters/{id}/retry` — retry a single event
- `POST /api/v1/admin/dead-letters/bulk-retry` — retry filtered batch with limit
- `DELETE /api/v1/admin/dead-letters/{id}` — discard an event

---

## 7. Notification & Recommendation Engine

### 7.1 Alert System (MSDD Enhancement 14)

**Alert Types:** `weather_alert`, `stress_alert`, `pest_alert`, `action_reminder`, `market_alert`, `harvest_approaching`

**Throttling:** Maximum 3 alerts per crop per 24 hours (configurable per alert type). Prevents notification fatigue.

**Channels:**
- In-app (`GET /api/v1/alerts/`) with acknowledgment tracking
- SMS via Twilio (OTP and critical alerts)
- Future: Push notifications (FCM/APNs), WhatsApp

### 7.2 Recommendation Engine Priority Formula (MSDD Patch 15)

```python
priority_score = URGENCY_WEIGHTS[type]  # harvest_prep > irrigation > fertilizer > general
              × stage_criticality
              + risk_index × 0.4
              + days_until_deadline × -0.1

# Top 3 recommendations surfaced per crop per day
```

---

## 8. Security Architecture

### 8.1 Authentication

- **JWT** (python-jose, HS256) with configurable expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- **bcrypt** password hashing via passlib
- Phone number + password login (no OAuth, keeping it simple for low-connectivity rural environments)
- Token refresh endpoint via `POST /api/v1/auth/refresh`

### 8.2 Authorization (RBAC)

Three roles with progressively expanding permissions:

| Role | Abilities |
|------|-----------|
| `farmer` | Own crops, alerts, recommendations, service requests, schemes |
| `provider` | Own equipment/labor, received service requests, own reviews |
| `admin` | Everything above + user management, provider governance, system health, DLQ, feature flags, ML models |

Route-level enforcement via `require_role()` FastAPI dependency.

### 8.3 Middleware Stack (in order)

```
Request → CorrelationID → RequestLogging → RateLimiter → BodySizeLimiter
       → InputSanitization → Idempotency → ErrorHandler → Response
```

### 8.4 Mutation Guard

A SQLAlchemy `before_flush` event listener blocks any direct write to protected `CropInstance` fields (`state`, `stage`, `stress_score`, `risk_index`, `current_day_number`, `stage_offset_days`) unless the write occurs inside the `allow_ctis_mutation()` context manager (which only event handlers use).

### 8.5 Soft Delete Policy (MSDD 5.10)

All major tables include:
- `is_deleted: Boolean` (default False)
- `deleted_at: DateTime` (nullable)
- `deleted_by: UUID` (nullable, references user)

No hard deletes are ever performed. Admin "delete" operations set these fields.

---

## 9. Database Schema Overview

### 9.1 Tables by Module

| Module | Tables |
|--------|--------|
| **Auth / Users** | `users` |
| **CTIS** | `crop_instances`, `action_logs`, `crop_instance_snapshots`, `deviation_profiles`, `yield_records`, `crop_rule_templates`, `regional_sowing_calendars`, `regional_clusters`, `stress_history`, `seasonal_windows` |
| **SOE** | `service_providers`, `equipment`, `labor`, `service_requests`, `service_reviews`, `provider_availability`, `service_request_events` |
| **ML** | `ml_models`, `ml_training_audit`, `ml_inference_audit`, `media_files`, `pest_alert_history` |
| **Events** | `event_log` |
| **Notifications** | `alerts`, `recommendations` |
| **Admin** | `admin_audit_log`, `feature_flags`, `abuse_flags` |
| **Gov Schemes** | `official_schemes`, `scheme_redirect_logs` |
| **Comms** | `sms_delivery_log`, `whatsapp_sessions`, `otp_codes`, `active_sessions` |
| **Governance** | `user_consents`, `dispute_cases`, `user_reports` |
| **Config** | `region_configs` |

### 9.2 Alembic Migration Strategy

Migrations are stored in `backend/alembic/versions/` and run automatically on Docker startup:
```
alembic upgrade head
```

All models must be imported in `backend/app/models/__init__.py` for Alembic's `autogenerate` to detect them.

---

## 10. API Layer

### 10.1 Response Envelope

All API responses follow a consistent envelope:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "request_id": "abc-123"
}
```

Errors include a structured `code` + `message`:
```json
{
  "success": false,
  "data": null,
  "error": { "code": "INVALID_STATE_TRANSITION", "message": "Cannot transition from Closed to Active" }
}
```

### 10.2 Idempotency

POST/PUT endpoints accept an optional `Idempotency-Key` header. If the same key is seen within the TTL window, the original response is returned without re-executing. Duplicates are identified by `event_hash = SHA256(entity_id + event_type + payload)` stored in `event_log`.

### 10.3 Versioning

All endpoints are prefixed `/api/v1/`. Future major versions will use `/api/v2/` etc.

---

## 11. Frontend Architecture

### 11.1 Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | TailwindCSS with custom `cultivax-*` design tokens |
| Icons | Lucide React |
| Charts | Recharts |
| Maps | MapLibre GL JS |
| Data fetching | SWR (stale-while-revalidate) |
| Auth state | React Context (`AuthContext`) |
| i18n | Custom inline dictionary (`src/lib/i18n.ts`) |
| PWA | Custom service worker (`src/worker/`) |
| Offline queue | `src/services/offlineQueue.ts` |

### 11.2 i18n — 5 Language Support

All UI strings are served from `src/lib/i18n.ts`, an inline dictionary that requires no network CDN:

| Code | Language |
|------|----------|
| `en` | English |
| `hi` | हिंदी (Hindi) |
| `ta` | தமிழ் (Tamil) |
| `te` | తెలుగు (Telugu) |
| `mr` | मराठी (Marathi) |

This approach enables full offline translation on low-bandwidth connections.

### 11.3 PWA Offline Strategy

1. Service worker caches key API responses (crop list, alerts, recommendations)
2. Actions logged without connectivity are added to `offlineQueue` (localStorage)
3. On reconnection, `useOnlineSync` hook sends queued actions to `POST /api/v1/sync/`
4. Optimistic UI shows pending actions immediately

### 11.4 Design System

- **Primary color:** `#34D399` (Emerald 400)
- **Accent:** `#F59E0B` (Amber 500)
- **Dark background:** `#0B1120`
- **Typography:** Inter (body) + JetBrains Mono (code/numbers)
- **Glassmorphism:** `backdrop-filter: blur(16px) saturate(180%)` on all cards
- **Theme tokens:** All colors exposed as CSS variables (`--cultivax-primary`, `--cultivax-surface`, etc.)

---

## 12. Infrastructure & Deployment

### 12.1 Local Development (Docker Compose)

Three services: `db` (PostgreSQL 15) → `backend` (FastAPI) → `frontend` (Next.js). Backend startup sequence: `alembic upgrade head && python -m scripts.seed_demo_users && uvicorn ...`

### 12.2 Production (Google Cloud Run)

```
Cloud Build → Docker image → Artifact Registry
                                    ↓
                          Cloud Run (backend)
                          - Max 12 instances
                          - 2 vCPU, 1Gi RAM
                          - Concurrency: 120
                          - Connected to Cloud SQL via Unix socket

Cloud SQL (PostgreSQL 15)
  - Private IP, VPC connector
  - Alembic runs on container startup

Cloud Storage (GCS)
  - Media file uploads
  - Signed URLs with 60-minute expiry
```

### 12.3 Autoscaling Target

The system is benchmarked (via k6) to handle **600 concurrent users** with:
- `p95` response time < 500ms
- Error rate < 1%

At 600 VUs, Cloud Run scales to ~12 instances at concurrency=120.

---

## 13. Key Design Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| **DB-backed event queue, not Redis/Kafka** | Zero external dependencies. ACID consistency. Survives restarts. Works on a single Postgres instance. |
| **Inline i18n dictionary** | Full offline operation without CDN. Works in rural low-bandwidth conditions. |
| **Snapshot manager every N actions** | Makes replay O(1) amortized — crop with 10,000 actions replays from last checkpoint (e.g., action 9,950) not from action 1. |
| **Idempotency keys on all mutations** | Offline sync actions can be safely retried if the network drops mid-send. |
| **Farmer Truth / ML Truth separation** | Legal/ethical requirement — farmer's reported yield is preserved exactly as stated. Only ML predictions are post-processed. |
| **Open-Meteo as primary weather** | 100% free, no API key needed, reliable fallback. OpenWeatherMap is secondary. |
| **JWT only, no OAuth** | Simpler implementation. Target farmers often share phones, making social OAuth inappropriate. |
| **Phone number as primary identifier** | More universally available in rural India than email. |

---

## 14. Explicitly Deferred Features

These are **documented in MSDD/TDD but intentionally not implemented** in the current prototype scope:

| Feature | Source | Reason |
|---------|--------|--------|
| Edge AI (TFLite on-device) | MSDD 4.5 | Requires trained models and mobile app |
| Regional Clustering batch job | MSDD 4.2 Layer 4 | Advanced — incremental prospective update is sufficient now |
| WhatsApp bot webhook | MSDD 7.12 | Separate microservice — post-MVP |
| Voice note intent parsing | MSDD 6.8 | Complex NLP — post-MVP |
| Voice Assist Mode | MSDD 7.11 | Requires speech-to-text integration |
| Video CNN/YOLO-lite processing | MSDD 4.6 | Requires trained pest detection models |
| Market data integration (ARIMA) | MSDD 4.7 | No live market data API source yet |
| Model Drift Monitoring | ML Enhancement 5 | Requires deployed models with sufficient inference history |
| Push Notifications (FCM/APNs) | MSDD 14 | Requires mobile app configuration |
| Multi-region deployment | Infra | Post-prototype scale |
| PgBouncer / connection pooling | Infra | Only needed at >200 concurrent DB connections |
| Storage & Transport Suggestion | MSDD 2.3 | Not critical for prototype |
