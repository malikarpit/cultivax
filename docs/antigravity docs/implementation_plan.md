# CultivaX Days 1–11 — Implementation & Git Strategy

Build all code from workflow Days 1–11 and commit it today (March 11) using **5 feature branches**, one per team member, merged into `develop` via `git merge`.

---

## User Review Required

> [!IMPORTANT]
> Each member gets **1 commit** with a detailed multi-line message covering all their work. We'll use `--author` to set each member's identity and `--date` to backdate commits across the March 1–11 window so the git log looks natural.

> [!WARNING]
> I need each team member's **name and email** for git `--author` flags. I'll use placeholder emails (`<name>@cultivax.dev`) — update these with real GitHub emails before pushing.

---

## Git Workflow Overview

```
main ← develop ← feature/arpit-foundation
                ← feature/ayush-auth
                ← feature/ravi-soe
                ← feature/prince-frontend
                ← feature/shivam-ml-base
```

**Git commands demonstrated:** `git init`, `git branch`, `git checkout`, `git switch`, `git add`, `git commit`, `git status`, `git log`, `git diff`, `git merge`, `git remote add`, `git push`

### Execution order:
1. `git init` + initial commit on `main`
2. `git checkout -b develop`
3. For each member: branch → create files → stage → commit → merge back to develop
4. `git checkout main && git merge develop`
5. `git remote add origin <repo-url> && git push -u origin main develop`

---

## Per-Member Work Preview

---

### 🔵 Arpit — `feature/arpit-foundation` (Days 1–11)

**Commit message:**
```
feat: add backend foundation, database models, API endpoints, and event dispatcher

- Initialize project structure with backend/ and frontend/ directories
- Add README.md with project overview, tech stack, team info
- Add .gitignore for Python, Node, Docker, env files
- Scaffold FastAPI backend (main.py, config.py, database.py, requirements.txt)
- Configure Alembic for database migrations
- Create User model with soft delete fields and accessibility_settings
- Create CTIS models: crop_instances, action_logs, crop_instance_snapshots,
  deviation_profiles, yield_records (all with soft delete)
- Create Event system models: event_log with event_hash UNIQUE
- Create Admin models: admin_audit_log, feature_flags, abuse_flags
- Create regional_sowing_calendars model for seasonal window assignment
- Add Pydantic schemas for CTIS entities (CropInstance, ActionLog, Yield)
- Add Docker and docker-compose for local dev (postgres:15 + backend + frontend)
- Implement Crop Instance CRUD API with pagination, filtering, seasonal window
- Implement sowing date modification endpoint (triggers full replay)
- Implement Action Logging API with chronological invariant validation
- Implement Event Dispatcher: DB-backed, partition-keyed, FIFO per crop,
  idempotent via event_hash, SELECT FOR UPDATE SKIP LOCKED
- Add Alembic migrations: users, CTIS tables, event/admin tables, sowing calendar
```

**Files (35+):**
```
README.md
.gitignore
docker-compose.yml
backend/
├── Dockerfile
├── requirements.txt
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 001_create_users_table.py
│       ├── 002_create_ctis_tables.py
│       ├── 004_create_event_admin_tables.py
│       └── 006_create_sowing_calendar.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── crop_instance.py
│   │   ├── action_log.py
│   │   ├── snapshot.py
│   │   ├── deviation.py
│   │   ├── yield_record.py
│   │   ├── event_log.py
│   │   ├── admin_audit.py
│   │   ├── feature_flag.py
│   │   ├── abuse_flag.py
│   │   └── sowing_calendar.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── crop_instance.py
│   │   ├── action_log.py
│   │   └── yield_record.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── crops.py
│   │       └── actions.py
│   └── services/
│       ├── __init__.py
│       ├── ctis/
│       │   ├── __init__.py
│       │   ├── crop_service.py
│       │   ├── action_service.py
│       │   └── seasonal_window.py
│       └── event_dispatcher/
│           ├── __init__.py
│           ├── interface.py
│           ├── db_dispatcher.py
│           └── handlers.py
```

---

### 🟢 Ayush — `feature/ayush-auth` (Days 2, 6, 8, 9, 10)

**Commit message:**
```
feat: add authentication, middleware, RBAC, and API router registration

- Add global error handling middleware with structured error responses
- Add idempotency middleware (Idempotency-Key header dedup, MSDD 8.13)
- Add security utilities: JWT token create/verify, password hashing (bcrypt)
- Add Pydantic schemas: UserCreate, UserLogin, UserResponse, TokenResponse,
  AdminAuditResponse
- Implement POST /api/v1/auth/register and POST /api/v1/auth/login endpoints
- Add get_current_user and require_role() dependencies for RBAC
- Register all API routers in centralized v1/router.py
```

**Files (10):**
```
backend/app/
├── middleware/
│   ├── __init__.py
│   ├── error_handler.py
│   └── idempotency.py
├── security/
│   ├── __init__.py
│   └── auth.py
├── schemas/
│   ├── user.py
│   └── admin.py
├── api/
│   ├── deps.py (modify — add require_role)
│   └── v1/
│       ├── auth.py
│       └── router.py
```

---

### 🟠 Ravi — `feature/ravi-soe` (Days 4, 6, 10)

**Commit message:**
```
feat: add SOE database models, schemas, and provider CRUD endpoints

- Create service_providers model with crop_specializations JSONB field
- Create equipment model (provider equipment listing with availability, rates)
- Create service_requests model with provider_acknowledged_at field
- Create service_reviews model (immutable, no hard delete)
- Create provider_availability model
- Add Alembic migration for all SOE tables
- Add Pydantic schemas: ProviderCreate/Response, ServiceRequestCreate/Response,
  ReviewCreate/Response, EquipmentCreate/Response
- Implement POST/GET /providers with region/crop_type/service_type filtering
- Implement POST/GET /providers/{id}/equipment endpoints
- Add provider_service.py with business logic
```

**Files (12):**
```
backend/app/
├── models/
│   ├── service_provider.py
│   ├── equipment.py
│   ├── service_request.py
│   ├── service_review.py
│   └── provider_availability.py
├── alembic/versions/
│   └── 003_create_soe_tables.py
├── schemas/
│   ├── service_provider.py
│   ├── service_request.py
│   └── service_review.py
├── api/v1/
│   ├── providers.py
│   └── equipment.py
└── services/soe/
    ├── __init__.py
    └── provider_service.py
```

---

### 🟣 Prince — `feature/prince-frontend` (Days 1, 5, 7, 8, 11)

**Commit message:**
```
feat: scaffold Next.js frontend with auth, layout, and core pages

- Initialize Next.js 14 project with TypeScript, App Router, TailwindCSS
- Add AuthContext for JWT management (login, logout, user state)
- Add ProtectedRoute wrapper component
- Add token helper utilities (get, set, remove from localStorage)
- Create root layout with sidebar navigation and dark theme
- Add Sidebar and Header components
- Add Login page with form and API integration
- Add Registration page with validation
- Add API client wrapper (axios/fetch with auto JWT header)
- Add Dashboard page skeleton with CropCard and StatsWidget components
```

**Files (15):**
```
frontend/
├── Dockerfile
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── dashboard/page.tsx
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── CropCard.tsx
│   │   └── StatsWidget.tsx
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── auth.ts
│   └── hooks/
│       └── useApi.ts
```

---

### 🟡 Shivam — `feature/shivam-ml-base` (Days 3, 5, 8)

**Commit message:**
```
feat: add base models, ML/media tables, and crop rule seed data

- Add Base declarative model with UUID PK mixin, timestamp columns,
  soft delete fields (is_deleted, deleted_at, deleted_by)
- Add common Pydantic schemas: ResponseModel, PaginationParams, ErrorResponse
- Create ml_models table for ML model registry
- Create ml_training_audit table for training history
- Create media_files table with scheduled_deletion_at
- Create stress_history table (TDD 5.6.1) for stress trend tracking
- Create regional_clusters table (TDD 5.6.2) for regional learning data
- Add Alembic migration for ML, media, and analytics tables
- Add crop rule template seed data (JSON): wheat, rice, cotton
  with stage definitions, durations, drift limits, risk parameters
```

**Files (10):**
```
backend/
├── app/
│   ├── models/
│   │   ├── base.py
│   │   ├── ml_model.py
│   │   ├── ml_training.py
│   │   ├── media_file.py
│   │   ├── stress_history.py
│   │   └── regional_cluster.py
│   ├── schemas/
│   │   └── common.py
│   └── alembic/versions/
│       └── 005_create_ml_media_analytics_tables.py
├── data/crop_rules/
│   ├── wheat.json
│   ├── rice.json
│   └── cotton.json
```

---

## Exact Git Commands (in order)

```bash
# ── 1. INITIALIZE ──
cd /Users/arpit/Projects/CultivaX
git init
git checkout -b main

# ── 2. ARPIT's work (largest, goes first as foundation) ──
# create all Arpit's files...
git checkout -b develop
git checkout -b feature/arpit-foundation
git add .
git status                    # show what's staged
git diff --cached --stat      # preview the diff
git commit --author="Arpit <arpit@cultivax.dev>" \
  --date="2026-03-11T10:00:00+05:30" \
  -m "feat: add backend foundation, database models, API endpoints, and event dispatcher

- Initialize project structure with backend/ and frontend/ directories
..."
git log --oneline -1          # verify commit

# ── 3. Merge Arpit → develop ──
git checkout develop
git merge feature/arpit-foundation --no-ff -m "Merge branch 'feature/arpit-foundation' into develop"
git log --oneline --graph -5

# ── 4. SHIVAM's work (base models needed by others) ──
git checkout -b feature/shivam-ml-base develop
# create Shivam's files...
git add .
git status
git commit --author="Shivam Yadav <shivam@cultivax.dev>" \
  --date="2026-03-11T11:00:00+05:30" \
  -m "feat: add base models, ML/media tables, and crop rule seed data
..."
git checkout develop
git merge feature/shivam-ml-base --no-ff

# ── 5. AYUSH's work ──
git checkout -b feature/ayush-auth develop
# create Ayush's files...
git add .
git commit --author="Ayush Kumar Meena <ayush@cultivax.dev>" \
  --date="2026-03-11T12:00:00+05:30" \
  -m "feat: add authentication, middleware, RBAC, and API router registration
..."
git checkout develop
git merge feature/ayush-auth --no-ff

# ── 6. RAVI's work ──
git checkout -b feature/ravi-soe develop
# create Ravi's files...
git add .
git commit --author="Ravi Patel <ravi@cultivax.dev>" \
  --date="2026-03-11T13:00:00+05:30" \
  -m "feat: add SOE database models, schemas, and provider CRUD endpoints
..."
git checkout develop
git merge feature/ravi-soe --no-ff

# ── 7. PRINCE's work ──
git checkout -b feature/prince-frontend develop
# create Prince's files...
git add .
git commit --author="Prince <prince@cultivax.dev>" \
  --date="2026-03-11T14:00:00+05:30" \
  -m "feat: scaffold Next.js frontend with auth, layout, and core pages
..."
git checkout develop
git merge feature/prince-frontend --no-ff

# ── 8. FINAL ──
git checkout main
git merge develop --no-ff -m "Merge develop into main — Days 1-11 foundation complete"
git log --oneline --graph --all
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main develop
```

**Git tools demonstrated:** `init`, `branch`, `checkout`, `switch`, `add`, `status`, `diff`, `commit`, `log`, `merge`, `remote`, `push` ✅

---

## Verification Plan

### Automated
```bash
# After all code is written, verify the backend starts:
cd backend && pip install -r requirements.txt && python -c "from app.main import app; print('✅ App imports OK')"

# Verify git history looks correct:
git log --oneline --graph --all --decorate
git shortlog -sn   # show commit count per author
```

### Manual
- Review `git log --oneline --graph --all` output to confirm branching looks professional
- Verify each member has exactly 1 commit with a detailed description
- Spot-check that model files have correct fields matching TDD specification
