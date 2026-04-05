"""
User Consent Model — NFR-13

Tracks explicit consent grants/revocations per processing purpose.
One row per user×purpose combination; updated (not appended) on change.
Immutable audit trail preserved via admin_audit_log entries on every change.
"""

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

CONSENT_PURPOSES = (
    "analytics",  # aggregate platform analytics
    "ml_training",  # use crop data for ML model training
    "sms_alerts",  # receive SMS notifications
    "third_party",  # share anonymised data with partners
    "research",  # academic / government research use
)


class UserConsent(BaseModel):
    """Records a user's explicit consent decision per processing purpose."""

    __tablename__ = "user_consents"

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    purpose = Column(String(50), nullable=False)  # one of CONSENT_PURPOSES
    granted = Column(Boolean, nullable=False, default=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # for audit trail
    user_agent = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)  # admin note or legal basis ref

    def __repr__(self):
        state = "granted" if self.granted else "revoked"
        return f"<UserConsent {self.purpose} [{state}] user={self.user_id}>"
