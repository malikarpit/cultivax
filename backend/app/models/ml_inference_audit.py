"""
ML Inference Audit Model — FR-29

Records every production inference call for auditability.
One row per prediction: crop, model, features used, and output produced.
"""

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class MLInferenceAudit(BaseModel):
    """Per-prediction audit trail for ML inference calls."""

    __tablename__ = "ml_inference_audit"

    # Subject of prediction
    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Model that produced this prediction
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_version = Column(String(100), nullable=False, index=True)

    # Inference source: "registry" | "heuristic_fallback" | "rule_based"
    inference_source = Column(String(50), nullable=False, default="rule_based")

    # Features fed into the model (for reproducibility)
    features = Column(JSONB, nullable=False, default=dict)

    # Output produced
    prediction_value = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    risk_label = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_ml_inference_audit_crop_model", "crop_instance_id", "model_id"),
        Index("ix_ml_inference_audit_version", "model_version"),
    )

    def __repr__(self):
        return (
            f"<MLInferenceAudit crop={self.crop_instance_id} "
            f"model_v={self.model_version} risk={self.prediction_value:.3f}>"
        )
