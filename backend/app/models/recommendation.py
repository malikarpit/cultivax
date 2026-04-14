"""
Recommendation Model

Stores prioritized recommendations for crop management actions.

Patch Module 2, Sec 15
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class Recommendation(BaseModel):
    __tablename__ = "recommendations"

    crop_instance_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recommendation_type = Column(
        String(50), nullable=False
    )  # irrigation/fertilizer/harvest_prep/general
    priority_rank = Column(Integer, nullable=False, default=0)
    message_key = Column(String(100), nullable=False)
    message_parameters = Column(JSONB, nullable=True)
    basis = Column(Text, nullable=True)  # Explanation of why this was recommended
    rationale = Column(JSONB, nullable=True)  # FR-9: structured rationale object
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # active/dismissed/acted/expired/overridden

    def __repr__(self):
        return f"<Recommendation(type={self.recommendation_type}, priority={self.priority_rank})>"
