"""
User Report Model — OR-14, OR-15

Allows farmers/users to report fraudulent, abusive, or non-compliant behaviour
by service providers or other platform actors.

Resolution states: open → reviewed → actioned | dismissed
"""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

REPORT_CATEGORIES = (
    "fraud",  # false claims, fake listings
    "abuse",  # harassment, threats
    "non_compliance",  # violating platform terms
    "quality",  # material misrepresentation of service quality
    "safety",  # health or safety concern
    "other",
)


class UserReport(BaseModel):
    """A report filed by a user against another platform actor."""

    __tablename__ = "user_reports"

    reporter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    reported_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    evidence_url = Column(String(512), nullable=True)  # optional screenshot/link

    status = Column(String(30), nullable=False, default="open", index=True)
    # open | reviewed | actioned | dismissed

    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<UserReport {self.category} [{self.status}]>"
