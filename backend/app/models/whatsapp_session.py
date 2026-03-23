"""
WhatsAppSession — WhatsApp chatbot session management.
Tracks conversation context for stateful farmer interactions.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

from app.models.base import BaseModel


class WhatsAppSession(BaseModel):
    __tablename__ = "whatsapp_sessions"

    farmer_phone = Column(String(20), nullable=False, index=True)
    session_type = Column(String(50), nullable=False, default="general")
    # general | action_log | query | alert_ack | service_request

    status = Column(String(20), nullable=False, default="active")
    # active | completed | expired | abandoned

    context_data = Column(JSONB, default=dict)
    # Stores conversation state: current step, collected data, etc.

    language = Column(String(10), default="hi")  # hi | en | mr | te | ...

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self):
        return f"<WhatsAppSession(phone={self.farmer_phone}, type={self.session_type})>"
