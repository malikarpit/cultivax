"""
Region Config Model — Platform Extensibility

Provides dynamic configuration for new agricultural regions without hardcoding.
Allows admins to define region-specific thresholds, alerts, and supported crops.
"""

from sqlalchemy import JSON, Boolean, Column, String

from app.models.base import BaseModel


class RegionConfig(BaseModel):
    """Configuration for a specific geographical region."""

    __tablename__ = "region_configs"

    region_name = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # JSON structure containing regional parameters:
    # {
    #   "supported_crops": ["wheat", "rice", "cotton"],
    #   "ph_thresholds": {"wheat": {"min": 6.0, "max": 7.5}},
    #   "weather_alert_thresholds": {"temp_max": 40, "rainfall_min": 10}
    # }
    parameters = Column(JSON, default=dict, nullable=False)

    def __repr__(self):
        return f"<RegionConfig {self.region_name} (Active: {self.is_active})>"
