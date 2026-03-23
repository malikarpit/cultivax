"""
MLFeedback — farmer feedback on ML predictions.
Tracks rejection/confirmation of risk predictions.
"""

from sqlalchemy import Column, String, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class MLFeedback(BaseModel):
    __tablename__ = "ml_feedback"

    crop_instance_id = Column(UUID(as_uuid=True), ForeignKey("crop_instances.id"), nullable=False, index=True)
    prediction_id = Column(String(255), nullable=False)  # Reference to the prediction
    model_version = Column(String(50), nullable=True)

    feedback_type = Column(String(50), nullable=False)  # rejected | confirmed | partially_correct
    reason = Column(Text, nullable=True)
    farmer_notes = Column(String(1000), nullable=True)

    # Original prediction context
    original_prediction = Column(JSONB, nullable=True)
    original_confidence = Column(Float, nullable=True)

    def __repr__(self):
        return f"<MLFeedback(crop={self.crop_instance_id}, type={self.feedback_type})>"
