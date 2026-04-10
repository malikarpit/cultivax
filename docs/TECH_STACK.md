# CultivaX — Tech Stack

> Full rationale for every technology choice in the CultivaX platform.

---

## Frontend

| Technology | Version | Rationale |
|-----------|---------|-----------|
| **Next.js** | 14 (App Router) | Server Components for fast time-to-interactive; file-based routing that maps 1:1 to our 30+ pages; built-in image optimization for media-heavy crop views |
| **React** | 18 | Concurrent features (transitions, Suspense) for loading state management on slow rural connections |
| **TypeScript** | 5.x | Strict typechecking prevents runtime shape mismatches between frontend and backend schemas |
| **TailwindCSS** | 3.x | Custom `cultivax-*` design tokens via CSS variables. Utility-first approach enables rapid component development with consistent spacing/color scales |
| **SWR** | 2.x | Stale-while-revalidate semantics give instant perceived performance; built-in cache invalidation after mutations; deduplication of concurrent requests |
| **Lucide React** | Latest | Consistent 24×24 stroke-based icon set; tree-shakeable; matches the clean dark-mode aesthetic |
| **Recharts** | 2.x | Composable React charting library; supports Line/Bar/Pie with the same data format; renders crisp on HiDPI displays |
| **MapLibre GL JS** | 3.x | Open-source MapLibre (forked from Mapbox); no API key required for the base map tile server; supports WebGL-accelerated rendering for dense farm marker clusters |
| **react-i18next** | — | Localization orchestration; inline dictionary (`i18n.ts`) serves 5 languages without CDN dependency, enabling full offline translation |

---

## Backend

| Technology | Version | Rationale |
|-----------|---------|-----------|
| **Python** | 3.11 | Pattern matching, improved exception groups, ~10-25% performance improvement over 3.10 | 
| **FastAPI** | 0.110+ | Async-first; automatic OpenAPI/Swagger generation; Pydantic v2 validation built-in; dependency injection for DB sessions and auth |
| **Pydantic** | v2 | 5-10× faster validation than v1 (Rust core); strict mode prevents silent coercions; clean schema-first API design |
| **SQLAlchemy** | 2.0 | Modern `Session` API; declarative ORM; works well with Alembic for migration management |
| **Alembic** | 1.13+ | Version-controlled DB schema migrations; autogenerate from SQLAlchemy models; supports downgrade rollbacks for safe deployments |
| **python-jose** | — | JWT creation and verification with HS256; lightweight, well-audited |
| **passlib (bcrypt)** | — | Memory-hard bcrypt password hashing; prevents brute force in data breach scenarios |
| **httpx** | — | Async HTTP client for external API calls (weather, Twilio). Replaces `requests` for async compatibility |
| **Pyright** | — | Static type checker; stricter than mypy on certain generics; integrated into VS Code |

---

## Database & Persistence

| Technology | Version | Rationale |
|-----------|---------|-----------|
| **PostgreSQL** | 15 | ACID compliance for CTIS event log and crop state integrity; JSONB for flexible schema fields (accessibility settings, crop stage definitions, ML features); `SELECT FOR UPDATE SKIP LOCKED` for safe multi-worker event processing |
| **psycopg2-binary** | — | Synchronous PostgreSQL adapter; works with SQLAlchemy sync sessions |

### Why Not NoSQL?

The CTIS replay engine requires **strict ordering and atomicity** of action logs. PostgreSQL provides:
- `SELECT FOR UPDATE` row locking during replay (prevents concurrent replays of the same crop)  
- ACID transactions so event publish + state update commit together or not at all  
- `UNIQUE (event_hash)` constraint for reliable idempotency  
- Native JSONB for flexible payload fields while keeping relational integrity for foreign keys

---

## Infrastructure

| Technology | Rationale |
|-----------|-----------|
| **Docker + Docker Compose** | Reproducible local dev environment. Backend, database, and frontend start with a single command. Eliminates "works on my machine" issues across team members. |
| **Google Cloud Run** | Serverless containers — no server management. Autoscales from 0 to 12 instances in ~2 seconds. Cost-efficient (pay per request, not per idle instance). Connects to Cloud SQL via Unix socket for low-latency DB access. |
| **Google Cloud SQL (PostgreSQL 15)** | Managed PostgreSQL with automatic backups, point-in-time recovery, and private IP (no public internet exposure). |
| **Google Cloud Storage (GCS)** | Object storage for media uploads (crop photos, analysis videos). Signed URLs (60-minute expiry) serve files directly to clients without routing huge binaries through the API server. |
| **Google Cloud Build** | CI/CD pipeline triggered on push. Builds Docker image, pushes to Artifact Registry, deploys to Cloud Run. |

---

## Communications & External Services

| Service | Purpose | Fallback |
|---------|---------|---------|
| **Twilio** | Real SMS OTPs and critical alerts | `stub` provider logs OTPs to console (safe for dev/testing) |
| **Open-Meteo** | Weather data (free, no API key) | Historical baseline if API is down |
| **OpenWeatherMap** | Secondary weather provider (7-day forecasts) | Falls back to Open-Meteo |

---

## Design System

| Design Decision | Choice | Reason |
|----------------|--------|--------|
| **Primary color** | `#34D399` (Emerald 400) | Associated with growth, farming, health |
| **Accent color** | `#F59E0B` (Amber 500) | Warmth, harvest, the "X" in CultivaX |
| **Dark background** | `#0B1120` | Easier to read on low-brightness screens in outdoor sunlight |
| **Typography** | Inter + JetBrains Mono | Inter is readable at small sizes; Mono for numeric data (stress scores, risk indices) |
| **Glassmorphism** | `backdrop-filter: blur(16px)` | Premium feel without heavy GPU cost; degrades gracefully on older Android devices |
| **CSS Variables** | All design tokens as `--cultivax-*` | Enables runtime theme switching (dark/light) without page reload |

---

## Security Choices

| Choice | Rationale |
|--------|-----------|
| **JWT only (no OAuth)** | Simpler implementation. Social OAuth (Google/Facebook) is inappropriate for shared-phone rural environments. |
| **Phone number as primary identifier** | Email is less common in rural India. Phone is universally available. |
| **bcrypt work factor** | Tuned to ~250ms hash time — slow enough to deter brute force, fast enough for login UX |
| **Rate limiting** | 10 req/min on auth endpoints; 200 req/min on reads — protects against credential stuffing and API abuse |
| **Soft deletes everywhere** | Legal/audit requirement — records of farmers' crop data must be retained even after "deletion" |
| **Idempotency keys** | Offline sync safety — retried actions from reconnecting devices must not double-commit |
