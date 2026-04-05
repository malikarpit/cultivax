"""
SMS Delivery Log Model — NFR-11

Tracks every SMS notification attempt, its status, and provider response
for audit and retry purposes.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class SmsDeliveryLog(BaseModel):
    """Per-SMS delivery audit record."""

    __tablename__ = "sms_delivery_logs"

    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    phone = Column(String(20), nullable=False)
    message_template = Column(String(100), nullable=True)
    message_body = Column(Text, nullable=True)

    attempt_count = Column(Integer, default=1, nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    # pending | sent | failed | dead_lettered

    provider = Column(String(50), nullable=True)
    # twilio | aws_sns | stub

    provider_response = Column(Text, nullable=True)
    # Raw API response or error string

    def __repr__(self):
        return f"<SmsDeliveryLog phone={self.phone} status={self.status}>"
