"""
Action Log Model

Records every farmer action on a crop instance.
Fields from TDD Section 2.3.2.
Chronological integrity enforced at service layer.
"""

from sqlalchemy import Column, String, Date, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import BaseModel


class ActionLog(BaseModel):
    __tablename__ = "action_logs"

    # Foreign key
    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Action details
    action_type = Column(String(100), nullable=False, index=True)
    # irrigation | fertilizer | pesticide | weeding | harvest | observation | media_upload

    effective_date = Column(Date, nullable=False)

    # Category (MSDD 1.6.3)
    category = Column(
        String(50),
        nullable=False,
        default="Operational",
    )  # Timeline-Critical | Operational | Informational

    # Metadata
    metadata_json = Column(JSONB, default=dict)
    notes = Column(String(1000), nullable=True)

    # Offline sync support
    local_seq_no = Column(Integer, nullable=True)
    device_timestamp = Column(DateTime(timezone=True), nullable=True)
    server_timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Idempotency
    idempotency_key = Column(String(255), unique=True, nullable=True)

    # Replay status
    applied_in_replay = Column(String(20), default="pending")  # pending | applied | skipped

    # Relationships
    crop_instance = relationship("CropInstance", back_populates="action_logs")

    def __repr__(self):
        return f"<ActionLog {self.action_type} on {self.effective_date}>"
