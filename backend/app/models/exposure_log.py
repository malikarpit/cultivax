"""
Exposure Log Model

Tracks provider search result impressions for ranking fairness
and exposure cap enforcement. Uses BaseModel for soft-delete
and timestamp consistency.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class ExposureLog(BaseModel):
    __tablename__ = "exposure_logs"

    provider_id = Column(UUID(as_uuid=True), ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False)
    region = Column(String(100), nullable=False)
    search_signature_hash = Column(String(64), nullable=True)
    rank_position = Column(Integer, nullable=False)
    page = Column(Integer, nullable=False, default=1)
    request_id = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_exposure_logs_provider_shown", "provider_id", "created_at"),
        Index("ix_exposure_logs_region_shown", "region", "created_at"),
    )
