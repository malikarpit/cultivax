"""
Yield Record Model

Stores yield submissions with dual truth: farmer-reported and ML-verified.
TDD Section 2.3.5 + TDD 4.9 (Farmer Truth vs ML Truth).
"""

from sqlalchemy import Column, Float, Boolean, String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class YieldRecord(BaseModel):
    __tablename__ = "yield_records"

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Farmer-reported yield (never modified by ML)
    reported_yield = Column(Float, nullable=False)
    yield_unit = Column(String(20), default="kg/acre", nullable=False)
    harvest_date = Column(Date, nullable=True)
    quality_grade = Column(String(10), nullable=True)
    moisture_pct = Column(Float, nullable=True)
    notes = Column(String(1000), nullable=True)

    # ML-verified yield (capped by biological limit)
    ml_yield_value = Column(Float, nullable=True)
    biological_cap = Column(Float, nullable=True)
    bio_cap_applied = Column(Boolean, default=False, nullable=False)

    # Verification
    yield_verification_score = Column(Float, nullable=True)  # 0-1 confidence
    verification_metadata = Column(JSONB, default=dict)

    # Relationships
    crop_instance = relationship("CropInstance", back_populates="yield_records")

    def __repr__(self):
        return f"<YieldRecord reported={self.reported_yield} {self.yield_unit}>"
