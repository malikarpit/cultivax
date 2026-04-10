"""
Regional Sowing Calendar Model

Defines optimal sowing windows per crop_type per region.
Used to determine seasonal_window_category (Early/Optimal/Late).
MSDD 1.9 + Patch Module 5.
"""

from sqlalchemy import Column, Date, Integer, String

from app.models.base import BaseModel


class RegionalSowingCalendar(BaseModel):
    __tablename__ = "regional_sowing_calendars"

    crop_type = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)

    # Optimal sowing window
    optimal_start = Column(Date, nullable=False)
    optimal_end = Column(Date, nullable=False)

    # Versioning (same philosophy as CropRuleTemplates)
    version_id = Column(Integer, default=1, nullable=False)
    effective_from_date = Column(Date, nullable=True)

    # Notes
    notes = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<SowingCalendar {self.crop_type}/{self.region} [{self.optimal_start} - {self.optimal_end}]>"
