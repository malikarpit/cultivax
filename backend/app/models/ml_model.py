"""
ML Model Registry

Stores ML model metadata and versions.
TDD Section 2.6.1.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class MLModel(BaseModel):
    __tablename__ = "ml_models"

    model_name = Column(String(255), nullable=False, index=True)
    model_type = Column(String(100), nullable=False)
    # risk_predictor | stress_classifier | yield_verifier | edge_ai

    version = Column(Integer, nullable=False, default=1)
    file_path = Column(String(500), nullable=True)

    # Status
    status = Column(String(20), default="draft", nullable=False)
    # draft | active | deprecated | archived

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    training_metadata = Column(JSONB, default=dict)

    # Compatibility (Patch Module 8)
    min_compatible_backend_version = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<MLModel {self.model_name} v{self.version} [{self.status}]>"
