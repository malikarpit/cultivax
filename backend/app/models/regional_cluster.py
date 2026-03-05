"""
Regional Cluster Model

Stores aggregated regional learning data.
TDD Section 5.6.2 + confidence interval (Patch Sec 4 Enhancement).
"""

from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class RegionalCluster(BaseModel):
    __tablename__ = "regional_clusters"

    # Cluster key
    crop_type = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    season = Column(String(20), nullable=True)  # kharif | rabi | zaid

    # Aggregate data
    avg_delay = Column(Float, default=0.0, nullable=False)
    avg_yield = Column(Float, default=0.0, nullable=False)
    sample_size = Column(Integer, default=0, nullable=False)

    # Statistical confidence (Patch Sec 4 Enhancement)
    std_dev_delay = Column(Float, nullable=True)
    std_dev_yield = Column(Float, nullable=True)
    confidence_interval_95 = Column(JSONB, default=dict)
    # { lower: 0.0, upper: 0.0 }

    # Data quality
    last_updated_from_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<RegionalCluster {self.crop_type}/{self.region} n={self.sample_size}>"
