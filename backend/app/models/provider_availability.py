"""
Provider Availability Model

Tracks provider availability by date.
TDD Section 5.3.
"""

from sqlalchemy import Column, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class ProviderAvailability(BaseModel):
    __tablename__ = "provider_availability"

    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_providers.id"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ProviderAvailability {self.date} available={self.is_available}>"
