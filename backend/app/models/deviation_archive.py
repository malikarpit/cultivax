"""
DeviationArchive — archived deviation profiles per farmer per season.
Preserves historical deviation data for behavioral analysis.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class DeviationArchive(BaseModel):
    __tablename__ = "deviation_profile_archive"

    farmer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    crop_type = Column(String(100), nullable=False)
    season = Column(String(50), nullable=False)  # e.g. "kharif_2025", "rabi_2024"

    archived_profile = Column(JSONB, nullable=False, default=dict)
    # Stores the full deviation profile snapshot at archive time

    archived_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<DeviationArchive(farmer={self.farmer_id}, season={self.season})>"
