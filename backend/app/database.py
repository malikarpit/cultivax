"""
CultivaX Database Configuration

SQLAlchemy engine, session factory, and dependency injection.
Uses PostgreSQL with connection pooling.
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.services.event_dispatcher.mutation_guard import \
    is_ctis_mutation_allowed

# Create SQLAlchemy engine
# Uses effective_database_url which auto-resolves Cloud SQL (unix socket)
# vs local development (standard connection string).
engine = create_engine(
    settings.effective_database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


PROTECTED_CTIS_FIELDS = {
    "state",
    "stage",
    "stress_score",
    "risk_index",
    "current_day_number",
    "stage_offset_days",
}


@event.listens_for(Session, "before_flush")
def prevent_direct_ctis_mutation(session, flush_context, instances):
    """Block direct mutations of protected CTIS fields outside sanctioned contexts."""
    if not settings.CTIS_MUTATION_GUARD_ENABLED:
        return
    if is_ctis_mutation_allowed():
        return

    from app.models.crop_instance import CropInstance

    for obj in session.dirty:
        if not isinstance(obj, CropInstance):
            continue

        state = getattr(obj, "_sa_instance_state", None)
        if not state:
            continue

        changed = {
            attr.key
            for attr in state.attrs
            if attr.history.has_changes() and attr.key in PROTECTED_CTIS_FIELDS
        }
        if changed:
            raise RuntimeError(
                f"Direct CTIS mutation blocked for CropInstance {obj.id}; changed={sorted(changed)}"
            )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes session after request.

    Usage in FastAPI:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
