"""
CultivaX Database Configuration

SQLAlchemy engine, session factory, and dependency injection.
Uses PostgreSQL with connection pooling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from typing import Generator

from app.config import settings


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
