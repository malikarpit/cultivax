"""
Base Model

Provides reusable mixins for all SQLAlchemy models:
- UUID primary key
- Timestamp columns (created_at, updated_at)
- Soft delete fields (is_deleted, deleted_at, deleted_by)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SoftDeleteMixin:
    """Mixin for soft delete support. No hard deletes allowed (MSDD 5.10)."""

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)


class TimestampMixin:
    """Mixin for automatic timestamp tracking."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base model with UUID PK, timestamps, and soft delete.
    All CultivaX models should inherit from this.
    """

    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
