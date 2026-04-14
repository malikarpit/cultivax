"""
Conversation Model — FR-23

Represents a messaging thread between two users,
optionally tied to a service request context.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

    participant_a_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    participant_b_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    service_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_requests.id"),
        nullable=True,
        index=True,
    )

    last_message_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), server_default="active", nullable=False)
    # active | archived

    # Relationships
    messages = relationship("Message", back_populates="conversation", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint(
            "participant_a_id",
            "participant_b_id",
            "service_request_id",
            name="uq_conversation_participants_context",
        ),
    )

    def __repr__(self):
        return (
            f"<Conversation(a={self.participant_a_id}, b={self.participant_b_id}, "
            f"status={self.status})>"
        )
