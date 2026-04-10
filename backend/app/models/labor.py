"""
Labor Model

Labor resources offered by service providers.
MSDD Section 2.6.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Labor(BaseModel):
    __tablename__ = "labor"

    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_providers.id"),
        nullable=False,
        index=True,
    )

    # Labor details
    labor_type = Column(String(100), nullable=False)
    # harvesting_crew | irrigation_worker | spraying_team | general_farm_labor

    description = Column(String(1000), nullable=True)

    # Availability & pricing
    available_units = Column(Integer, default=1, nullable=False)
    daily_rate = Column(Float, nullable=True)
    hourly_rate = Column(Float, nullable=True)

    # Location
    region = Column(String(200), nullable=False, index=True)
    sub_region = Column(String(200), nullable=True)

    # Status
    is_available = Column(Boolean, default=True, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)

    # Relationships
    provider = relationship("ServiceProvider", back_populates="labor")

    def __repr__(self):
        return f"<Labor {self.labor_type} (units={self.available_units})>"
