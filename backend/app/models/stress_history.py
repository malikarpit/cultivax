"""
Stress History Model

Records stress score snapshots per crop per stage.
TDD Section 5.6.1.
"""

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class StressHistory(BaseModel):
    __tablename__ = "stress_history"

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Stress snapshot
    stress_score = Column(Float, nullable=False)
    stage = Column(String(100), nullable=True)
    day_number = Column(Float, nullable=True)

    # Source signals
    source = Column(String(50), nullable=True)
    # manual | media_analysis | weather | replay | multi_signal

    # Signal breakdown
    signal_breakdown = Column(JSONB, default=dict)
    # { backend_ml: 0.3, weather_risk: 0.2, deviation_penalty: 0.1, edge_signal: 0.0 }

    def __repr__(self):
        return f"<StressHistory score={self.stress_score} stage={self.stage}>"
