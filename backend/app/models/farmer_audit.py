"""
FarmerAudit — audit trail for all farmer-facing actions.
Separate from admin_audit — tracks farmer actions specifically.
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class FarmerAudit(BaseModel):
    __tablename__ = "farmer_action_audit_log"

    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    # login | action_create | crop_create | service_request | media_upload | data_export

    entity_type = Column(String(50), nullable=True)  # crop_instance | action_log | service_request
    entity_id = Column(UUID(as_uuid=True), nullable=True)

    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    channel = Column(String(20), nullable=True)  # web | whatsapp | offline

    details = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<FarmerAudit(farmer={self.farmer_id}, action={self.action_type})>"
