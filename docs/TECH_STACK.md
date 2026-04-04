# CultivaX Tech Stack Components

CultivaX utilizes a modern, rigorously typed, full-stack architecture optimized for high I/O throughput and visual aesthetics.

## Frontend Layer
*   **Next.js 14** (App Router): Provides the foundational React framework, enabling Server Components for fast time-to-interactive layout generation and optimal SEO structuring.
*   **React 18**: High-performance UI rendering utilizing concurrent features like transitions and suspense for loading state management.
*   **TailwindCSS**: Granular utility-first styling utilizing a highly customized `M3` (Material Design 3) Design Language system specifically curated via `globals.css` variable extensions.
*   **Lucide React**: Vectorized icon framework mapped to the premium M3 design language.
*   **Recharts**: Composable charting library handling live-data analytics such as weather tracking and yield visualization.

## Backend Service Layer
*   **FastAPI**: Asynchronous Python web framework generating high-throughput REST APIs and automatic OpenAPI 3 / Swagger documentation.
*   **Python 3.11**: Strict type hinting (`typing`) verified across the codebase using `Pyright` and `Pyre2` for runtime safety.
*   **Pydantic V2**: Rigorous schema validation protecting controllers against malformed payloads or data injections from the client tier.

## Database & Persistence
*   **PostgreSQL 15**: ACID-compliant relational SQL storage. Serves as the backbone for the CTIS Event Logger and transactional service ecosystem.
*   **SQLAlchemy 2.0**: The primary ORM bridging Python domain logic to the relational mapping in a synchronous engine interface.
*   **Alembic**: Database version control handling automated schema upgrading, downgrade rollbacks, and baseline migrations during deployments.

## Authentication & Security
*   **JWT (JSON Web Tokens)**: Cryptographically verified bearer tokens managing user sessions (`python-jose`).
*   **Bcrypt**: Memory-hard key derivation protecting password-at-rest via `passlib`, preventing brute force decryption in data breach scenarios.
*   **GCP Secret Manager**: Secure injection vector preventing configuration drift and keeping hard secrets out of the orchestration layer.

## Infrastructure
*   **Docker & Docker Compose**: Immutable containerization guaranteeing "it works on my machine works in production" environments for local development and build pipelines.
*   **Google Cloud Run**: Serverless container orchestration abstracting away base-layer server maintenance while autoscaling to handle unpredictable agricultural load burst traffic.
*   **Google Cloud Storage (GCS)**: Managing the heavy lifting of raw multimedia (Crop snapshots, problem analysis images) with secure Signed Time-To-Live URLs minimizing bandwidth routing through the REST proxy.
