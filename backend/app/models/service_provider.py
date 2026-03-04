"""
Service Provider Model

Service providers in the SOE marketplace.
TDD Section 2.5.1 + crop_specializations (Patch Sec 2 Enhancement).
"""

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ServiceProvider(BaseModel):
    __tablename__ = "service_providers"

    # Link to user account
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Provider details
    business_name = Column(String(255), nullable=True)
    service_type = Column(String(100), nullable=False, index=True)
    # equipment_rental | labor | transport | storage | advisory

    # Location
    region = Column(String(100), nullable=False, index=True)
    sub_region = Column(String(100), nullable=True)
    service_radius_km = Column(Float, nullable=True)

    # Crop specialization (Patch Sec 2 Enhancement)
    crop_specializations = Column(JSONB, default=list)
    # e.g. ["wheat", "rice", "cotton"]

    # Trust & verification
    trust_score = Column(Float, default=0.5, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)

    # Status
    is_suspended = Column(Boolean, default=False, nullable=False)
    suspension_reason = Column(String(500), nullable=True)

    # Description
    description = Column(Text, nullable=True)

    # Relationships
    equipment = relationship("Equipment", back_populates="provider", lazy="dynamic")
    labor = relationship("Labor", back_populates="provider", lazy="dynamic")
    service_requests = relationship("ServiceRequest", back_populates="provider", lazy="dynamic")

    def __repr__(self):
        return f"<ServiceProvider {self.business_name} ({self.service_type})>"
