"""
MarketPrice — regional crop market pricing data.
Tracks mandi/market prices with staleness detection.
"""

from sqlalchemy import Column, String, Float, Date, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class MarketPrice(BaseModel):
    __tablename__ = "market_prices"

    crop_type = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    region = Column(String(200), nullable=False, index=True)

    price_per_unit = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False, default="kg")  # kg | quintal | ton
    currency = Column(String(10), nullable=False, default="INR")

    price_date = Column(Date, nullable=False)
    source_provider = Column(String(200), nullable=True)  # API source or manual entry

    # Staleness detection (merges market_cache concept)
    is_stale = Column(Boolean, default=False, nullable=False)
    staleness_threshold_hours = Column(Float, default=24.0)

    metadata_extra = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<MarketPrice({self.crop_type}@{self.region}={self.price_per_unit}/{self.unit})>"
