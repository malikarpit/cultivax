"""
Crop Instance Model

Core CTIS table. Represents one farmer's one crop lifecycle.
Fields from TDD Section 2.3.1.
"""

from sqlalchemy import Column, String, Float, Date, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CropInstance(BaseModel):
    __tablename__ = "crop_instances"

    # Foreign keys
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Crop identity
    crop_type = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    sowing_date = Column(Date, nullable=False)

    # State machine (MSDD 1.5)
    state = Column(
        String(50),
        nullable=False,
        default="Created",
        index=True,
    )  # Created | Active | Delayed | AtRisk | ReadyToHarvest | Harvested | Closed | Archived

    # Current stage
    stage = Column(String(100), nullable=True)
    current_day_number = Column(Integer, default=0)

    # Baseline tracking (MSDD 1.3.1) — tracks expected progress independently
    baseline_day_number = Column(Integer, default=0)
    baseline_growth_stage = Column(String(100), nullable=True)

    # Risk & stress
    stress_score = Column(Float, default=0.0, nullable=False)
    risk_index = Column(Float, default=0.0, nullable=False)

    # Seasonal window (MSDD 1.9 + Patch Module 5)
    seasonal_window_category = Column(
        String(20),
        nullable=True,
    )  # Early | Optimal | Late

    # Land info
    land_area = Column(Float, nullable=True)  # in acres
    region = Column(String(100), nullable=False, index=True)
    sub_region = Column(String(100), nullable=True)

    # Rule template reference
    rule_template_id = Column(UUID(as_uuid=True), nullable=True)
    rule_template_version = Column(Integer, nullable=True)

    # Drift tracking
    stage_offset_days = Column(Integer, default=0)
    max_allowed_drift = Column(Integer, default=7)

    # ML cache (Patch Sec 4 Enhancement)
    last_risk_probability = Column(Float, nullable=True)
    last_inference_at = Column(String(50), nullable=True)

    # Archive flag (MSDD 1.16, 5.10) — separate from soft delete
    is_archived = Column(Boolean, default=False, nullable=False)

    # Tamper detection (TDD 2.3.1)
    event_chain_hash = Column(String(255), nullable=True)

    # Projected harvest (MSDD 1.10) — computed and cached
    projected_harvest_date = Column(Date, nullable=True)

    # Metadata
    metadata_extra = Column(JSONB, default=dict)

    # Relationships
    farmer = relationship("User", back_populates="crop_instances")
    action_logs = relationship("ActionLog", back_populates="crop_instance", lazy="dynamic")
    snapshots = relationship("CropInstanceSnapshot", back_populates="crop_instance", lazy="dynamic")
    yield_records = relationship("YieldRecord", back_populates="crop_instance", lazy="dynamic")
    deviation_profile = relationship("DeviationProfile", back_populates="crop_instance", uselist=False)

    def __repr__(self):
        return f"<CropInstance {self.crop_type} [{self.state}]>"
