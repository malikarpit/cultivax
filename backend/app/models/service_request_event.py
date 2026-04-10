"""
Service Request Event Model

Audit trail for service request state transitions.
SOE Enhancement 7.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ServiceRequestEvent(BaseModel):
    __tablename__ = "service_request_events"

    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    # State transition
    event_type = Column(String(100), nullable=False)
    # Created | Accepted | InProgress | Completed | Cancelled | Disputed | Escalated

    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=False)

    # Who triggered the transition
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(50), nullable=True)  # farmer | provider | admin | system

    # When
    transitioned_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Optional notes
    notes = Column(String(1000), nullable=True)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="events")

    def __repr__(self):
        return f"<ServiceRequestEvent {self.previous_state} → {self.new_state}>"
