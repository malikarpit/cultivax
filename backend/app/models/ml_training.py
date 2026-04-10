"""
ML Training Audit Model

Records ML model training history for auditing.
TDD Section 2.6.2.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class MLTrainingAudit(BaseModel):
    __tablename__ = "ml_training_audit"

    model_id = Column(
        UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=False, index=True
    )

    # Training details
    dataset_size = Column(Integer, nullable=False)
    training_duration_seconds = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)

    # Dataset info
    dataset_metadata = Column(JSONB, default=dict)
    # { regions_included: [], crop_types: [], date_range: {} }

    # Who triggered it
    triggered_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<MLTrainingAudit dataset_size={self.dataset_size} acc={self.accuracy}>"
