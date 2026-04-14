"""
Recommendation Override — FR-7, FR-8

Tracks farmer overrides of system-generated recommendations.
Records what was overridden, when, why, and what the farmer did instead.
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class RecommendationOverride(BaseModel):
    __tablename__ = "recommendation_overrides"

    recommendation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id"),
        nullable=False,
        index=True,
    )
    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )
    farmer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # What the farmer chose to do
    override_action = Column(
        String(50), nullable=False
    )  # dismissed | ignored | acted_differently

    farmer_reason = Column(Text, nullable=True)

    # Snapshot of original recommendation context
    original_recommendation_type = Column(String(50), nullable=False)
    original_priority_rank = Column(Integer, nullable=False, default=0)
    original_rationale = Column(JSONB, nullable=True)

    def __repr__(self):
        return (
            f"<RecommendationOverride(rec={self.recommendation_id}, "
            f"action={self.override_action})>"
        )
