# CultivaX 🌱

**Intelligent Crop Lifecycle Management & Service Orchestration Platform**

CultivaX is a deterministic, event-driven agricultural management system that provides farmers with chronologically accurate crop timeline tracking, intelligent recommendations, and a service marketplace — all built with replay-safe architecture.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 15 (Cloud SQL) |
| Frontend | Next.js 14, React 18, TailwindCSS |
| Auth | JWT (python-jose) |
| Deployment | Google Cloud Run, Cloud Storage |
| Containerization | Docker, docker-compose |

## Project Structure

```
cultivax/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/           # REST endpoints
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── middleware/     # Error handling, idempotency
│   │   └── security/      # JWT, password hashing
│   ├── alembic/           # Database migrations
│   └── data/              # Seed data
├── frontend/              # Next.js frontend
│   └── src/
│       ├── app/           # Pages (App Router)
│       ├── components/    # Reusable UI components
│       ├── context/       # React contexts
│       └── lib/           # Utilities
└── docker-compose.yml
```

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

# Start all services
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

## Core Systems

- **CTIS** — Crop Timeline Intelligence System (deterministic replay engine)
- **SOE** — Service Orchestration Ecosystem (marketplace + trust scoring)
- **Event Dispatcher** — DB-backed, partitioned FIFO event processing

## Team

| Member | Role |
|--------|------|
| Arpit | Lead — Backend Architecture, CTIS, Event System, Deployment |
| Ayush Kumar Meena | Auth, Middleware, Admin APIs |
| Ravi Patel | SOE Module, Trust Engine, Provider Management |
| Prince | Frontend — All UI pages, Components |
| Shivam Yadav | ML Module, Media, Seed Data, Base Models |

## License

This project is developed as part of the Software Engineering course.
