"""
Equipment Model

Provider equipment listing.
TDD Section 5.5.2.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Equipment(BaseModel):
    __tablename__ = "equipment"

    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_providers.id"),
        nullable=False,
        index=True,
    )

    # Equipment details
    equipment_type = Column(String(100), nullable=False)
    # tractor | harvester | sprayer | thresher | irrigation_pump | transport_vehicle

    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Availability & pricing
    is_available = Column(Boolean, default=True, nullable=False)
    hourly_rate = Column(Float, nullable=True)
    daily_rate = Column(Float, nullable=True)

    # Condition
    condition = Column(String(50), default="good", nullable=False)
    # new | good | fair | needs_maintenance

    # Flagged for review
    is_flagged = Column(Boolean, default=False, nullable=False)

    # Relationships
    provider = relationship("ServiceProvider", back_populates="equipment")

    def __repr__(self):
        return f"<Equipment {self.name} ({self.equipment_type})>"
