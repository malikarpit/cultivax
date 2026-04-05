"""
Official Government Scheme / Portal Model — FR-31

Stores links to government agricultural schemes, subsidies, and portals.
Admins manage these; farmers browse and get redirected to official URLs.
"""

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class OfficialScheme(BaseModel):
    """A government agricultural scheme or official portal entry."""

    __tablename__ = "official_schemes"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    portal_url = Column(String(2000), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    # e.g.: "subsidy", "insurance", "advisory", "equipment", "credit"

    region = Column(String(100), nullable=True, index=True)
    # NULL = pan-India; specific value = region-scoped

    crop_type = Column(String(100), nullable=True, index=True)
    # NULL = all crops

    tags = Column(JSONB, default=list)
    # Additional keywords for search

    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<OfficialScheme {self.name} [{self.category}]>"
