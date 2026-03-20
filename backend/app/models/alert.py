"""
Alert Model

Stores system-generated alerts for farmers.

MSDD Enhancement Sec 14
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone

from app.models.base import BaseModel


class Alert(BaseModel):
    __tablename__ = "alerts"

    crop_instance_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="info")  # info/warning/critical
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Alert(type={self.alert_type}, severity={self.severity})>"
