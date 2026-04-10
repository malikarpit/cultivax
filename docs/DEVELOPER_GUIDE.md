# CultivaX — Developer Guide

> Complete reference for contributing to, extending, and debugging CultivaX.

---

## Table of Contents

1. [Repository Layout](#1-repository-layout)
2. [Backend — Deep Dive](#2-backend--deep-dive)
3. [Frontend — Deep Dive](#3-frontend--deep-dive)
4. [Database Migrations](#4-database-migrations)
5. [Event System — How to Add a New Event](#5-event-system--how-to-add-a-new-event)
6. [Adding a New API Endpoint](#6-adding-a-new-api-endpoint)
7. [Adding a New Frontend Page](#7-adding-a-new-frontend-page)
8. [Testing Guide](#8-testing-guide)
9. [Performance Testing](#9-performance-testing)
10. [Common Debugging Scenarios](#10-common-debugging-scenarios)
11. [Git Conventions](#11-git-conventions)
12. [Code Style](#12-code-style)

---

## 1. Repository Layout

```
cultivax/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/                  # One file per resource group
│   │   │       ├── router.py        # Aggregates all sub-routers
│   │   │       ├── auth.py
│   │   │       ├── crops.py
│   │   │       ├── schemes.py
│   │   │       └── ...
│   │   ├── models/
│   │   │   ├── __init__.py          # ⚠️ MUST import every model for Alembic autogenerate
│   │   │   ├── base.py              # UUID PK mixin, timestamps, soft delete fields
│   │   │   └── ...
│   │   ├── schemas/                 # Pydantic v2 request/response models
│   │   ├── services/
│   │   │   ├── ctis/                # All crop timeline logic
│   │   │   ├── soe/                 # All service orchestration logic
│   │   │   ├── ml/                  # ML inference and registry
│   │   │   ├── event_dispatcher/    # DB-backed event bus
│   │   │   ├── notifications/       # Alert service
│   │   │   ├── recommendations/     # Recommendation engine
│   │   │   ├── media/               # File upload / analysis
│   │   │   └── weather/             # Weather API integration
│   │   ├── middleware/              # FastAPI middleware stack
│   │   ├── security/                # JWT, RBAC, mutation guard
│   │   ├── core/                    # Logging config
│   │   ├── config.py                # Pydantic settings
│   │   ├── database.py              # SQLAlchemy engine, session factory
│   │   ├── main.py                  # FastAPI app, middleware, startup events
│   │   └── events/
│   │       └── handlers.py          # App-level startup/shutdown handlers
│   ├── alembic/
│   │   ├── env.py                   # Alembic connects to database.py metadata
│   │   └── versions/                # Migration files
│   ├── scripts/
│   │   └── seed_demo_users.py       # Creates 3 demo accounts on startup
│   ├── tests/                       # pytest test suite
│   │   ├── conftest.py              # DB fixtures, test client, auth headers
│   │   ├── perf/                    # Performance benchmark tests
│   │   └── test_*.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── pytest.ini
│   └── alembic.ini
│
├── frontend/
│   └── src/
│       ├── app/                     # Next.js App Router — one dir per route
│       │   ├── layout.tsx           # Root layout (sidebar, header, auth gate)
│       │   ├── globals.css          # Design tokens, CSS variables, TailwindCSS config
│       │   └── [route]/page.tsx
│       ├── components/              # Reusable React components
│       │   ├── Sidebar.tsx
│       │   ├── Header.tsx
│       │   ├── LanguageSwitcher.tsx
│       │   └── ...
│       ├── context/
│       │   ├── AuthContext.tsx      # JWT storage, login/logout, user state
│       │   └── SWRProvider.tsx      # SWR global config
│       ├── hooks/
│       │   ├── useFetch.ts          # SWR-based data fetching hook
│       │   ├── useOfflineActions.ts
│       │   └── useOnlineSync.ts
│       ├── lib/
│       │   ├── api.ts               # Typed API client (fetch wrapper + JWT)
│       │   ├── auth.ts              # Token helpers (get/set/remove from localStorage)
│       │   └── i18n.ts              # Inline translation dictionaries (en/hi/ta/te/mr)
│       ├── services/
│       │   └── offlineQueue.ts      # Offline action queue (localStorage-backed)
│       └── worker/                  # PWA service worker
│
├── deploy/
│   ├── deploy-backend.sh            # Cloud Run deploy script
│   ├── run-migrations.sh            # Cloud SQL Alembic migration script
│   └── setup-cloud-sql.sh           # Cloud SQL instance provisioning
│
├── docs/                            # This documentation
├── extra/                           # Build history scripts (gitignored in CI)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 2. Backend — Deep Dive

### 2.1 Settings & Config

All configuration is in `backend/app/config.py` via `pydantic-settings`. Values are read from environment variables:

```python
from app.config import settings

print(settings.DATABASE_URL)
print(settings.SECRET_KEY)
print(settings.APP_ENV)  # "development" or "production"
```

### 2.2 Database Session

```python
from app.database import SessionLocal

# In an API route (via dependency injection):
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In routes:
@router.get("/crops/")
async def list_crops(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ...
```

### 2.3 Adding a New Model

1. Create `backend/app/models/my_model.py`:

```python
from app.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, String

class MyModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "my_models"
    name = Column(String(255), nullable=False)
```

2. **Import it in `backend/app/models/__init__.py`** — this is mandatory for Alembic to detect it:

```python
from app.models.my_model import MyModel  # noqa: F401
```

3. Generate + apply migration:
```bash
cd backend
alembic revision --autogenerate -m "add my_models table"
alembic upgrade head
```

### 2.4 Mutation Guard

Never write directly to `CropInstance` protected fields. Use the event system:

```python
# ❌ Wrong — will raise RuntimeError
crop.state = "Active"
db.commit()

# ✅ Correct — publish an event
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.services.event_dispatcher.event_types import CTISEvents

DBEventDispatcher(db).publish(
    event_type=CTISEvents.CROP_STATE_CHANGE_REQUESTED,
    entity_type="CropInstance",
    entity_id=crop.id,
    payload={"target_state": "Active", "requested_by": str(user_id)},
)
db.commit()
```

### 2.5 RBAC in Routes

```python
from app.security.guards import require_role

@router.get("/admin/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    ...
```

---

## 3. Frontend — Deep Dive

### 3.1 API Client

All API calls go through `src/lib/api.ts`:

```typescript
import { api } from "@/lib/api";

// GET
const crops = await api.get("/api/v1/crops/");

// POST
const newCrop = await api.post("/api/v1/crops/", { crop_type: "wheat", ... });
```

The client automatically attaches the JWT from localStorage and handles 401 by redirecting to login.

### 3.2 i18n Usage

```typescript
import { useTranslation } from "@/lib/i18n";

const { t } = useTranslation();

return <h1>{t("dashboard.title")}</h1>;
```

To add a new translation key, edit `src/lib/i18n.ts` and add the key under all 5 language objects.

### 3.3 AuthContext

```typescript
import { useAuth } from "@/context/AuthContext";

const { user, login, logout, isLoading } = useAuth();
```

`user` contains `{ id, full_name, phone, role, region, preferred_language }`.

### 3.4 Protected Pages

Pages that require authentication use the `ProtectedRoute` wrapper (or check `useAuth` directly in the layout). Unauthenticated requests are redirected to `/login`.

### 3.5 Custom Hooks

| Hook | Purpose |
|------|---------|
| `useFetch(url, options?)` | SWR-backed data fetch with loading/error states |
| `useOfflineActions()` | Read/write to the offline action queue |
| `useOnlineSync()` | Trigger sync when connectivity is restored |

### 3.6 Design Token Usage

Use `cultivax-*` Tailwind classes, not raw color values:

```tsx
// ✅ Correct
<div className="bg-cultivax-surface border border-cultivax-border text-cultivax-text-primary">

// ❌ Avoid
<div className="bg-zinc-900 border border-zinc-700 text-white">
```

Custom tokens are defined in `src/app/globals.css` as CSS variables and mapped in `tailwind.config.js`.

---

## 4. Database Migrations

### Creating a Migration

```bash
cd backend

# Auto-detect model changes (requires all models imported in __init__.py)
alembic revision --autogenerate -m "description of change"

# Review the generated file
cat alembic/versions/<timestamp>_description_of_change.py

# Apply
alembic upgrade head
```

### Rolling Back

```bash
# Roll back one migration
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Show migration history
alembic history --verbose

# Show current applied revision
alembic current
```

### Running in Docker

```bash
# Run inside running backend container
docker compose exec backend alembic upgrade head

# Or restart backend (it runs migrations on startup)
docker compose restart backend
```

### Critical Rule

**Every new SQLAlchemy model MUST be imported in `backend/app/models/__init__.py`.**  
If you skip this step, `alembic revision --autogenerate` will not detect your new table and **the migration will be empty**.

---

## 5. Event System — How to Add a New Event

### Step 1: Define the event type constant

```python
# backend/app/services/event_dispatcher/event_types.py

class MyEvents:
    MY_THING_HAPPENED = "my_module.my_thing_happened"
```

### Step 2: Publish the event from your service

```python
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.services.event_dispatcher.event_types import MyEvents

DBEventDispatcher(db).publish(
    event_type=MyEvents.MY_THING_HAPPENED,
    entity_type="MyEntity",
    entity_id=my_entity.id,
    payload={"key": "value"},
)
db.commit()
```

### Step 3: Register a handler

```python
# backend/app/services/event_dispatcher/handlers.py

def handle_my_thing_happened(db, event):
    payload = event.payload or {}
    # do something
    pass

_HANDLER_MAP = {
    ...
    MyEvents.MY_THING_HAPPENED: handle_my_thing_happened,
}
```

Done. The background loop will pick up and process the event within ~2 seconds of publication.

---

## 6. Adding a New API Endpoint

### Step 1: Create or find the router file

```python
# backend/app/api/v1/my_resource.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.security.guards import require_role

router = APIRouter(prefix="/my-resource", tags=["My Resource"])

@router.get("/")
async def list_things(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("farmer"))
):
    return {"items": []}
```

### Step 2: Register in the central router

```python
# backend/app/api/v1/router.py
from app.api.v1 import my_resource

api_router.include_router(my_resource.router)
```

### Step 3: Add a Pydantic schema

```python
# backend/app/schemas/my_resource.py
from pydantic import BaseModel
import uuid

class MyResourceCreate(BaseModel):
    name: str

class MyResourceResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True
```

---

## 7. Adding a New Frontend Page

### Step 1: Create the page directory

```
frontend/src/app/my-page/page.tsx
```

### Step 2: Implement the page

```tsx
"use client";

import { useFetch } from "@/hooks/useFetch";
import { useTranslation } from "@/lib/i18n";

export default function MyPage() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useFetch("/api/v1/my-resource/");

  if (isLoading) return <div className="animate-pulse">Loading...</div>;
  if (error) return <div className="text-cultivax-danger">Error loading data</div>;

  return (
    <div className="p-6">
      <h1 className="text-cultivax-text-primary text-2xl font-bold">
        {t("my_page.title")}
      </h1>
    </div>
  );
}
```

### Step 3: Add to Sidebar

Edit `frontend/src/components/Sidebar.tsx` and add a nav item inside the appropriate role section.

### Step 4: Add translation keys

Edit `frontend/src/lib/i18n.ts` and add `"my_page.title"` under all 5 language objects.

---

## 8. Testing Guide

### Running Tests

```bash
cd backend

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html
# Open htmlcov/index.html

# Specific file
pytest tests/test_official_schemes.py -v

# By keyword
pytest -k "trust" -v

# Fail fast
pytest -x

# In Docker (no local Python needed)
docker compose exec backend pytest
```

### Writing a Test

```python
# backend/tests/test_my_feature.py
import pytest
from fastapi.testclient import TestClient

def test_my_endpoint_returns_200(client, db, farmer_headers):
    response = client.get("/api/v1/my-resource/", headers=farmer_headers)
    assert response.status_code == 200
    assert "items" in response.json()
```

### Key Fixtures (from `conftest.py`)

| Fixture | Type | Description |
|---------|------|-------------|
| `db` | `Session` | Test database session (rolled back after each test) |
| `client` | `TestClient` | FastAPI test client |
| `farmer_headers` | `dict` | Auth headers for `Demo Farmer` (`+919999999992`) |
| `admin_headers` | `dict` | Auth headers for `Demo Admin` (`+919999999991`) |
| `provider_headers` | `dict` | Auth headers for `Demo Provider` (`+919999999993`) |
| `seeded_crop` | `CropInstance` | A crop in `Active` state |

### Test Categories

```bash
# Only run performance benchmarks
pytest -m perf

# Skip performance tests (default)
pytest -m "not perf"

# Only run integration tests
pytest -m integration
```

---

## 9. Performance Testing

### Replay Performance Benchmark

```bash
cd backend
pytest tests/perf/test_replay_performance.py -v -m perf
```

Validates O(n) replay scaling across 100, 500, 1000 actions.

### Load Testing with k6

```bash
# Install k6: https://k6.io/docs/getting-started/installation/

# Run against local Docker
k6 run backend/perf/k6_600_users.js -e BASE_URL=http://localhost:8000

# Run against production
k6 run backend/perf/k6_600_users.js -e BASE_URL=https://your-cloud-run-url
```

**SLOs:**
- `http_req_failed < 1%`
- `http_req_duration p(95) < 500ms`
- Target: 600 concurrent virtual users

---

## 10. Common Debugging Scenarios

### 10.1 "Direct CTIS mutation blocked" Error

**Cause:** Code is trying to write to `CropInstance.state` (or other protected fields) outside the event handler context.

**Fix:** Use `DBEventDispatcher.publish(CTISEvents.CROP_STATE_CHANGE_REQUESTED, ...)` instead.

### 10.2 Alembic Generates Empty Migration

**Cause:** New model is not imported in `backend/app/models/__init__.py`.

**Fix:** Add `from app.models.my_model import MyModel  # noqa: F401` to `__init__.py`.

### 10.3 Frontend Shows Stale Data

**Cause:** SWR cache not invalidated after a mutation.

**Fix:** Call `mutate()` from the SWR hook after a successful POST/PUT:

```tsx
const { data, mutate } = useFetch("/api/v1/crops/");

const handleCreate = async () => {
  await api.post("/api/v1/crops/", newCrop);
  mutate(); // re-fetch
};
```

### 10.4 Events Stuck in "Processing" State

**Cause:** Backend crashed mid-processing. Events are left in `Processing` status.

**Fix:** The background loop automatically resets `Processing → Created` on startup. Restart the backend:
```bash
docker compose restart backend
```

Or manually reset via SQL:
```sql
UPDATE event_log SET status = 'Created', updated_at = NOW()
WHERE status = 'Processing';
```

### 10.5 "RecoveryRequired" Crop State

**Cause:** The replay engine encountered an unrecoverable error (e.g., inconsistent action log).

**Fix (Admin):**
1. Go to `/admin/health` → check dead letters
2. Identify the failed event in `/admin/dead-letters`
3. Fix the underlying data issue
4. Retry the event via `POST /api/v1/admin/dead-letters/{id}/retry`
5. The crop will return to `Active` state after successful replay

### 10.6 Backend Won't Start — Migration Error

**Cause:** A model has a new column that hasn't been migrated.

**Fix:**
```bash
docker compose exec backend alembic upgrade head
```

If the migration itself has errors:
```bash
docker compose exec backend alembic history
docker compose exec backend alembic downgrade -1
# Fix the migration file
docker compose exec backend alembic upgrade head
```

### 10.7 JWT "Not enough segments" Error

**Cause:** The frontend is sending a malformed or expired token.

**Fix:** Clear localStorage and log in again:
```javascript
// Browser console
localStorage.removeItem("access_token");
window.location.href = "/login";
```

---

## 11. Git Conventions

### Branch Naming

```
main ← develop ← feature/<what>
                  fix/<what>
                  docs/<what>
                  test/<what>
```

### Commit Format

```
type(scope): description

feat(ctis): add behavioral adaptation pattern detection
fix(soe): correct trust score temporal decay calculation
docs(api): update schemes endpoint request format
test(ml): add inference audit filter tests
chore(deps): update requirements.txt
deploy(gcp): add autoscaling config for 600 users
```

**Types:** `feat` | `fix` | `docs` | `test` | `chore` | `deploy` | `refactor` | `perf`

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] New models imported in `models/__init__.py`
- [ ] Migrations generated and tested
- [ ] Translation keys added (all 5 languages)
- [ ] UI components use `cultivax-*` theme tokens
- [ ] Accessibility attributes on interactive elements (`title`, `aria-label`)

---

## 12. Code Style

### Python

- Type hints required everywhere
- Pyright-clean (no red underlines for type errors)
- `snake_case` for variables, `PascalCase` for classes
- Docstrings on all service methods
- Services must not import directly from API layer

```python
# ✅ Service method signature
def compute_trust_score(self, provider_id: uuid.UUID) -> dict[str, float]:
    """
    Compute the weighted trust score for a provider.
    
    Returns: dict with keys: trust_score, component_breakdown
    """
```

### TypeScript / React

- Strict mode enabled (controlled by `tsconfig.json`)
- `PascalCase` for components, `camelCase` for variables
- All interactive elements must have `title` and `aria-label`
- Use `className` with `cultivax-*` tokens, not inline styles

```tsx
// ✅ Correct
<button
  onClick={handleAction}
  title="Refresh data"
  aria-label="Refresh data"
  className="btn-icon text-cultivax-text-muted hover:text-cultivax-text-primary"
>
  <RefreshCw className="w-4 h-4" />
</button>
```
