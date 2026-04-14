"""
Message Model — FR-23, FR-24

Individual messages within a conversation thread.
Supports text, system, and contact_share message types.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    recipient_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    content = Column(Text, nullable=False)
    message_type = Column(
        String(30), server_default="text", nullable=False
    )  # text | system | contact_share

    is_read = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Offline sync tracking (FR-24)
    client_message_id = Column(String(255), nullable=True, unique=True)
    # Client-generated UUID for deduplication during offline sync

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __init__(self, **kwargs):
        # Ensure is_read defaults to False at Python object level
        if "is_read" not in kwargs:
            kwargs["is_read"] = False
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Message(from={self.sender_id}, type={self.message_type})>"
