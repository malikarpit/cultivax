"""
Crop Rule Template Model

Stores crop-specific rules including stage definitions, risk parameters,
irrigation/fertilizer/harvest windows, and version tracking.

MSDD 1.4 — Crop rules are versioned and effective from a specific date.
march 26 : Phase 7A — Governance lifecycle: draft → validated → active (dual-approval).
"""

from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class CropRuleTemplate(BaseModel):
    """
    Crop rule templates define the expected lifecycle parameters for each
    crop type. These are versioned and immutable once applied.

    Governance lifecycle (Phase 7A):
      - draft: initial creation, editable
      - validated: passes structural validation, awaiting admin approval
      - active: approved by a second admin, live for use
      - deprecated: superseded by newer version

    Fields per MSDD 1.4:
    - stage_definitions: ordered list of growth stages with expected durations
    - risk_parameters: thresholds for stress, drift, and risk alerts
    - irrigation_windows: optimal irrigation timing per stage
    - fertilizer_windows: optimal fertilizer timing per stage
    - harvest_windows: expected harvest readiness indicators
    - drift_limits: max allowed deviation per stage (MSDD 1.9)
    """
    __tablename__ = "crop_rule_templates"

    crop_type = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)

    # Versioning (MSDD 1.4)
    version_id = Column(String(50), nullable=False, default="1.0")
    effective_from_date = Column(Date, nullable=False)

    # Governance lifecycle (Phase 7A)
    status = Column(
        String(20), nullable=False, default="draft",
        comment="draft → validated → active → deprecated"
    )
    approved_by = Column(UUID(as_uuid=True), nullable=True, comment="Second admin who approved")
    approved_at = Column(DateTime, nullable=True, comment="Approval timestamp")
    validation_errors = Column(JSONB, nullable=True, default=list, comment="Validation result details")

    # Rule definitions (JSONB for flexibility)
    stage_definitions = Column(JSONB, nullable=False, default=list)
    risk_parameters = Column(JSONB, nullable=False, default=dict)
    irrigation_windows = Column(JSONB, nullable=True, default=dict)
    fertilizer_windows = Column(JSONB, nullable=True, default=dict)
    harvest_windows = Column(JSONB, nullable=True, default=dict)
    drift_limits = Column(JSONB, nullable=True, default=dict)

    # Metadata
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return (
            f"<CropRuleTemplate(crop_type={self.crop_type}, "
            f"version={self.version_id}, status={self.status}, region={self.region})>"
        )
