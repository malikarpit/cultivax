"""
Deviation Profile Model — Arpit

Tracks consecutive deviations from expected crop timeline.
MSDD Section 1.9.1 + TDD 2.3.4.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DeviationProfile(BaseModel):
    __tablename__ = "deviation_profiles"

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Deviation tracking
    consecutive_deviation_count = Column(Integer, default=0, nullable=False)
    deviation_trend_slope = Column(Float, default=0.0, nullable=False)
    recurring_pattern_flag = Column(Boolean, default=False, nullable=False)

    # Last deviation details
    last_deviation_type = Column(String(50), nullable=True)  # early | late
    last_deviation_days = Column(Integer, default=0)
    cumulative_deviation_days = Column(Integer, default=0)

    # Relationships
    crop_instance = relationship("CropInstance", back_populates="deviation_profile")

    def __repr__(self):
        return f"<DeviationProfile consecutive={self.consecutive_deviation_count}>"
