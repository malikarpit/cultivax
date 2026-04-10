"""
Abuse Flag Model

Tracks abuse detection flags for offensive sync, timeline manipulation, etc.
MSDD Patch Section 4.1.
"""

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class AbuseFlag(BaseModel):
    __tablename__ = "abuse_flags"

    # Who
    farmer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # What
    flag_type = Column(String(100), nullable=False, index=True)
    # offline_batch_abuse | timestamp_manipulation | excessive_media |
    # yield_inflation | review_spam | action_logging_spam

    # Severity
    severity = Column(
        String(20), nullable=False, default="low"
    )  # low | medium | high | critical

    # Score
    anomaly_score = Column(Float, nullable=True)

    # Details
    details = Column(JSONB, default=dict)

    # Resolution
    status = Column(
        String(20), default="open", nullable=False
    )  # open | reviewed | dismissed | actioned
    resolved_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<AbuseFlag {self.flag_type} [{self.severity}]>"
