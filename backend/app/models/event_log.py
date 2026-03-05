"""
Event Log Model

DB-backed event persistence for the event dispatcher.
TDD Section 2.4.1. Idempotency via UNIQUE event_hash.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone

from app.models.base import BaseModel


class EventLog(BaseModel):
    __tablename__ = "event_log"

    # Event identity
    event_type = Column(String(100), nullable=False, index=True)
    # ActionLogged | ReplayTriggered | MediaAnalyzed | StressUpdated |
    # YieldSubmitted | WeatherUpdated | RuleModified | AlertCreated

    # Entity reference
    entity_type = Column(String(50), nullable=False)  # crop_instance | service_request | user
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Payload
    payload = Column(JSONB, nullable=False, default=dict)

    # Partition key for FIFO ordering per crop
    partition_key = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Idempotency — UNIQUE hash prevents duplicate event processing
    event_hash = Column(String(255), unique=True, nullable=False)

    # Processing status
    status = Column(
        String(20),
        nullable=False,
        default="Created",
        index=True,
    )  # Created | Processing | Completed | Failed | DeadLetter

    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    failure_reason = Column(String(1000), nullable=True)

    # Timestamps
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<EventLog {self.event_type} [{self.status}]>"
