"""
Admin Audit Log Model

Immutable, append-only log of all admin actions.
TDD Section 2.8.1. No hard deletion allowed (MSDD Enhancement 10).
"""

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class AdminAuditLog(BaseModel):
    __tablename__ = "admin_audit_log"

    # Who did it
    admin_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # What was done
    action = Column(String(100), nullable=False, index=True)
    # user_role_change | user_deactivate | rule_create | rule_modify
    # provider_verify | provider_suspend | feature_flag_toggle | dead_letter_retry

    # Target entity
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Before and after values for auditability
    before_value = Column(JSONB, nullable=True)
    after_value = Column(JSONB, nullable=True)

    # Reason (required for destructive actions)
    reason = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<AdminAudit {self.action} on {self.entity_type}>"
