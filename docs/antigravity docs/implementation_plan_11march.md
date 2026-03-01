# CultivaX Days 1–11 — Phased Implementation Plan

**Repo:** `https://github.com/malikarpit/cultivax.git`
**Scope:** Strictly Days 1–11 from workflow.md only.
**Strategy:** Build all code → verify → commit per member → push.

---

## Phase 1: Project Skeleton
> Files everyone depends on. Created first.

| File | Owner | Purpose |
|------|-------|---------|
| `README.md` | Arpit | Project overview, tech stack, team |
| `.gitignore` | Arpit | Python, Node, Docker, .env patterns |
| `backend/app/__init__.py` | Arpit | Empty package init |
| `backend/requirements.txt` | Arpit | FastAPI, SQLAlchemy, Alembic, Pydantic, uvicorn, python-jose, bcrypt, etc. |
| `backend/.env.example` | Arpit | DATABASE_URL, SECRET_KEY, etc. |

**Verify:** Files exist, .gitignore is correct.

---

## Phase 2: Backend Core (FastAPI Scaffold)
> App entrypoint + database connection + config.

| File | Owner | Purpose |
|------|-------|---------|
| `backend/app/main.py` | Arpit | FastAPI app, CORS, lifespan, health endpoint |
| `backend/app/config.py` | Arpit | Pydantic Settings (DB URL, JWT secret, etc.) |
| `backend/app/database.py` | Arpit | SQLAlchemy engine, SessionLocal, get_db |

**Verify:** `python -c "from app.config import settings; print(settings)"` works.

---

## Phase 3: Database Models (ALL tables)
> Every model for every member. Built together so imports resolve.

| File | Owner | Table(s) | Key Fields |
|------|-------|----------|------------|
| `models/base.py` | Shivam | — | Base mixin: UUID PK, created_at, updated_at, is_deleted, deleted_at, deleted_by |
| `models/user.py` | Arpit | `users` | user_id, full_name, phone, role, password_hash, region, accessibility_settings JSONB, is_onboarded |
| `models/crop_instance.py` | Arpit | `crop_instances` | crop_instance_id, farmer_id FK, crop_type, sowing_date, state, stage, stress_score, risk_index, seasonal_window_category, land_area, region |
| `models/action_log.py` | Arpit | `action_logs` | action_id, crop_instance_id FK, action_type, effective_date, category, metadata JSONB, local_seq_no |
| `models/snapshot.py` | Arpit | `crop_instance_snapshots` | snapshot_id, crop_instance_id FK, snapshot_data JSONB, action_count_at_snapshot |
| `models/deviation.py` | Arpit | `deviation_profiles` | deviation_id, crop_instance_id FK, consecutive_count, trend_slope, recurring_flag |
| `models/yield_record.py` | Arpit | `yield_records` | yield_id, crop_instance_id FK, reported_yield, ml_yield_value, bio_cap_applied |
| `models/event_log.py` | Arpit | `event_log` | event_id, event_type, entity_id, payload JSONB, status, event_hash UNIQUE, partition_key |
| `models/admin_audit.py` | Arpit | `admin_audit_log` | audit_id, admin_id FK, action, entity_type, entity_id, before_value, after_value |
| `models/feature_flag.py` | Arpit | `feature_flags` | flag_id, flag_name UNIQUE, is_enabled, description |
| `models/abuse_flag.py` | Arpit | `abuse_flags` | abuse_id, farmer_id FK, flag_type, severity, details |
| `models/sowing_calendar.py` | Arpit | `regional_sowing_calendars` | calendar_id, crop_type, region, optimal_start, optimal_end, version_id |
| `models/service_provider.py` | Ravi | `service_providers` | provider_id, user_id FK, service_type, region, crop_specializations JSONB, is_verified, trust_score |
| `models/equipment.py` | Ravi | `equipment` | equipment_id, provider_id FK, type, availability, hourly_rate |
| `models/service_request.py` | Ravi | `service_requests` | request_id, farmer_id FK, provider_id FK, service_type, status, provider_acknowledged_at |
| `models/service_review.py` | Ravi | `service_reviews` | review_id, request_id FK, rating, comment, complaint_category |
| `models/provider_availability.py` | Ravi | `provider_availability` | availability_id, provider_id FK, date, is_available |
| `models/ml_model.py` | Shivam | `ml_models` | model_id, model_name, version, status, file_path |
| `models/ml_training.py` | Shivam | `ml_training_audit` | audit_id, model_id FK, dataset_size, accuracy, trained_at |
| `models/media_file.py` | Shivam | `media_files` | media_id, crop_instance_id FK, file_type, storage_path, analysis_status, scheduled_deletion_at |
| `models/stress_history.py` | Shivam | `stress_history` | stress_id, crop_instance_id FK, stress_score, stage, computed_at |
| `models/regional_cluster.py` | Shivam | `regional_clusters` | cluster_id, crop_type, region, avg_delay, avg_yield, sample_size, std_dev_yield |
| `models/__init__.py` | Arpit | — | Import all models for Alembic auto-detect |

**Verify:** `python -c "from app.models import *; print('All models OK')"` works.

---

## Phase 4: Alembic Migrations

| File | Owner | Tables |
|------|-------|--------|
| `alembic/env.py` | Arpit | Configure target_metadata |
| `alembic.ini` | Arpit | DB URL from env |
| `versions/001_create_users.py` | Arpit | users |
| `versions/002_create_ctis.py` | Arpit | crop_instances, action_logs, snapshots, deviations, yields |
| `versions/003_create_soe.py` | Ravi | service_providers, equipment, requests, reviews, availability |
| `versions/004_create_event_admin.py` | Arpit | event_log, admin_audit, feature_flags, abuse_flags |
| `versions/005_create_ml_media.py` | Shivam | ml_models, ml_training, media_files, stress_history, regional_clusters |
| `versions/006_create_sowing_cal.py` | Arpit | regional_sowing_calendars |

**Verify:** Migration files import correctly.

---

## Phase 5: Pydantic Schemas

| File | Owner | Schemas |
|------|-------|---------|
| `schemas/__init__.py` | Shivam | — |
| `schemas/common.py` | Shivam | ResponseModel, PaginationParams, ErrorResponse |
| `schemas/crop_instance.py` | Arpit | CropInstanceCreate, CropInstanceResponse, CropInstanceUpdate |
| `schemas/action_log.py` | Arpit | ActionLogCreate, ActionLogResponse |
| `schemas/yield_record.py` | Arpit | YieldSubmission, YieldResponse |
| `schemas/user.py` | Ayush | UserCreate, UserLogin, UserResponse, TokenResponse |
| `schemas/admin.py` | Ayush | AdminAuditResponse |
| `schemas/service_provider.py` | Ravi | ProviderCreate, ProviderResponse, EquipmentCreate, EquipmentResponse |
| `schemas/service_request.py` | Ravi | ServiceRequestCreate, ServiceRequestResponse |
| `schemas/service_review.py` | Ravi | ReviewCreate, ReviewResponse |

**Verify:** All schemas import without errors.

---

## Phase 6: Security + Middleware (Ayush)

| File | Owner | Purpose |
|------|-------|---------|
| `security/__init__.py` | Ayush | — |
| `security/auth.py` | Ayush | create_access_token, verify_token, hash_password, verify_password |
| `middleware/__init__.py` | Ayush | — |
| `middleware/error_handler.py` | Ayush | Global exception-to-JSON handler |
| `middleware/idempotency.py` | Ayush | Idempotency-Key header dedup middleware |

**Verify:** JWT creation and password hashing work.

---

## Phase 7: API Endpoints + Dependencies

| File | Owner | Endpoints |
|------|-------|-----------|
| `api/__init__.py` | Arpit | — |
| `api/deps.py` | Ayush | get_db, get_current_user, require_role() |
| `api/v1/__init__.py` | Arpit | — |
| `api/v1/router.py` | Ayush | Aggregate all v1 routers |
| `api/v1/auth.py` | Ayush | POST /register, POST /login |
| `api/v1/crops.py` | Arpit | POST /crops, GET /crops, GET /crops/{id}, PUT /crops/{id}, PUT /crops/{id}/sowing-date |
| `api/v1/actions.py` | Arpit | POST /crops/{id}/actions |
| `api/v1/providers.py` | Ravi | POST /providers, GET /providers, GET /providers/{id} |
| `api/v1/equipment.py` | Ravi | POST /providers/{id}/equipment, GET /providers/{id}/equipment |

**Verify:** `python -c "from app.api.v1.router import api_router"` works.

---

## Phase 8: Services (Business Logic)

| File | Owner | Logic |
|------|-------|-------|
| `services/__init__.py` | Arpit | — |
| `services/ctis/__init__.py` | Arpit | — |
| `services/ctis/crop_service.py` | Arpit | create, list, get, update crop instances |
| `services/ctis/action_service.py` | Arpit | log action + chronological validation |
| `services/ctis/seasonal_window.py` | Arpit | assign Early/Optimal/Late from sowing_calendar |
| `services/soe/__init__.py` | Ravi | — |
| `services/soe/provider_service.py` | Ravi | Provider CRUD + filtering logic |
| `services/event_dispatcher/__init__.py` | Arpit | — |
| `services/event_dispatcher/interface.py` | Arpit | Abstract EventDispatcher |
| `services/event_dispatcher/db_dispatcher.py` | Arpit | publish(), process_pending(), idempotent |
| `services/event_dispatcher/handlers.py` | Arpit | Event-type → handler map |

**Verify:** All services import without circular dependencies.

---

## Phase 9: Docker

| File | Owner | Purpose |
|------|-------|---------|
| `docker-compose.yml` | Arpit | postgres:15 + backend + frontend |
| `backend/Dockerfile` | Arpit | Python 3.11, pip install, uvicorn |
| `frontend/Dockerfile` | Prince | Node 18, npm install, next dev |

---

## Phase 10: Frontend (Next.js)

| File | Owner | Purpose |
|------|-------|---------|
| Next.js project scaffold | Prince | `npx create-next-app` |
| `src/app/layout.tsx` | Prince | Root layout, sidebar, dark theme |
| `src/app/globals.css` | Prince | CSS vars, dark theme, typography |
| `src/app/page.tsx` | Prince | Redirect to /dashboard |
| `src/app/login/page.tsx` | Prince | Login form |
| `src/app/register/page.tsx` | Prince | Registration form |
| `src/app/dashboard/page.tsx` | Prince | Dashboard with crop cards |
| `src/components/Sidebar.tsx` | Prince | Navigation sidebar |
| `src/components/Header.tsx` | Prince | Top header bar |
| `src/components/ProtectedRoute.tsx` | Prince | Redirect if not auth'd |
| `src/components/CropCard.tsx` | Prince | Crop status card |
| `src/components/StatsWidget.tsx` | Prince | Stat counter widget |
| `src/context/AuthContext.tsx` | Prince | JWT login/logout state |
| `src/lib/api.ts` | Prince | Fetch wrapper with JWT header |
| `src/lib/auth.ts` | Prince | Token get/set/remove localStorage |

---

## Phase 11: Seed Data

| File | Owner | Content |
|------|-------|---------|
| `backend/data/crop_rules/wheat.json` | Shivam | Wheat stages, durations, drift limits, risk params |
| `backend/data/crop_rules/rice.json` | Shivam | Rice stages |
| `backend/data/crop_rules/cotton.json` | Shivam | Cotton stages |

---

## Phase 12: Verification
```bash
cd backend && python -c "from app.main import app; print('✅ Backend OK')"
cd frontend && npm run build 2>&1 | tail -5   # or npm run lint
```

---

## Phase 13: Git Workflow & Commits

**Order:** Arpit → Shivam → Ayush → Ravi → Prince (each on feature branch, merged to develop)

For each member:
```bash
git checkout -b feature/<name>-foundation develop
git add <member's specific files>
git status
git diff --cached --stat
# ASK USER for member's GitHub name+email
git commit --author="<Name> <email>" --date="<date>" -m "<message>"
git checkout develop
git merge feature/<name>-foundation --no-ff
git log --oneline --graph -3
```

Final:
```bash
git checkout main && git merge develop --no-ff
git log --oneline --graph --all
git remote add origin https://github.com/malikarpit/cultivax.git
git push -u origin main develop
```
