"""
SystemHealth — subsystem health monitoring.
Tracks operational status of ML, weather, media, events subsystems.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class SystemHealth(BaseModel):
    __tablename__ = "system_health"

    subsystem = Column(String(50), nullable=False, unique=True)
    # ml | weather | media | events | database | storage

    status = Column(String(20), nullable=False, default="Operational")
    # Operational | Degraded | Down

    last_checked_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    details = Column(JSONB, default=dict)
    error_message = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<SystemHealth({self.subsystem}={self.status})>"
