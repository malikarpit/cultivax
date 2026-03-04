"""
Service Request Model

Service requests from farmers to providers.
TDD Section 2.5.2 + provider_acknowledged_at (Patch Sec 2).
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ServiceRequest(BaseModel):
    __tablename__ = "service_requests"

    # Parties
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.id"), nullable=False, index=True)

    # Request details
    service_type = Column(String(100), nullable=False)
    crop_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Scheduling
    requested_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="Pending",
        index=True,
    )  # Pending | Accepted | InProgress | Completed | Cancelled | Disputed

    # Response tracking (Patch Sec 2 Enhancement)
    provider_acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Pricing
    agreed_price = Column(Float, nullable=True)
    final_price = Column(Float, nullable=True)

    # Metadata
    metadata_json = Column(JSONB, default=dict)

    # Relationships
    provider = relationship("ServiceProvider", back_populates="service_requests")
    review = relationship("ServiceReview", back_populates="service_request", uselist=False)
    events = relationship("ServiceRequestEvent", back_populates="service_request", lazy="dynamic")

    def __repr__(self):
        return f"<ServiceRequest {self.service_type} [{self.status}]>"
