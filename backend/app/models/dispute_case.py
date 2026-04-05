"""
Dispute Case Model — FR-33

Structured end-to-end dispute workflow between farmers and providers.
States: open → investigating → resolved | dismissed
"""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class DisputeCase(BaseModel):
    """A formal dispute between a farmer (reporter) and a provider (respondent)."""

    __tablename__ = "dispute_cases"

    # Parties — FK to users with SET NULL so records survive user deletion
    reporter_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    respondent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    # Optional reference to the triggering service request (no FK — table may not be present)
    service_request_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Classification
    category = Column(String(50), nullable=False)
    # quality | fraud | non_delivery | payment | other
    description = Column(Text, nullable=True)

    # Lifecycle
    status = Column(String(30), nullable=False, default="open", index=True)
    # open | investigating | resolved | dismissed

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Resolution
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<DisputeCase {self.category} [{self.status}]>"
