"""
Scheme Redirect Audit Log — FR-31

Records every time a user clicks "Open Official Portal" so we can
track which schemes are most accessed and provide an audit trail.
"""

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class SchemeRedirectLog(BaseModel):
    """Audit trail for portal redirect clicks."""

    __tablename__ = "scheme_redirect_logs"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("official_schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    redirect_url = Column(String(2000), nullable=False)

    def __repr__(self):
        return f"<SchemeRedirectLog user={self.user_id} scheme={self.scheme_id}>"
