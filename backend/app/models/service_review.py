"""
Service Review Model

Immutable reviews for completed service requests.
TDD Section 2.5.3. No hard deletion — reviews are immutable.
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ServiceReview(BaseModel):
    __tablename__ = "service_reviews"

    # Link to completed request (one review per request)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_requests.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Reviewer (farmer)
    reviewer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Provider
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_providers.id"),
        nullable=False,
        index=True,
    )

    # Rating
    rating = Column(Float, nullable=False)  # 1.0 - 5.0
    comment = Column(Text, nullable=True)

    # Complaint (optional)
    complaint_category = Column(String(100), nullable=True)
    # late_arrival | poor_quality | overcharging | damage | no_show | other

    # Admin moderation
    is_flagged = Column(String(20), default="none")  # none | flagged | reviewed
    flagged_reason = Column(String(500), nullable=True)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="review")

    def __repr__(self):
        return f"<ServiceReview rating={self.rating}>"
