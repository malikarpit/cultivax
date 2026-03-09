"""
Seasonal Window Assignment

Assigns Early/Optimal/Late category based on sowing_date vs regional calendar.
MSDD 1.9 + Patch Module 5.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.models.sowing_calendar import RegionalSowingCalendar


def assign_seasonal_window(
    db: Session,
    sowing_date: date,
    crop_type: str,
    region: str,
) -> str:
    """
    Determine the seasonal window category for a crop instance.
    
    Logic:
        - If sowing_date < optimal_start → 'Early'
        - If optimal_start <= sowing_date <= optimal_end → 'Optimal'
        - If sowing_date > optimal_end → 'Late'
        - If no calendar found, falls back to national default, then 'Unknown'
    
    This value is set ONCE at creation and NEVER changes,
    even if sowing_date is later modified (MSDD 1.9).
    """
    # Try region-specific calendar first
    calendar = db.query(RegionalSowingCalendar).filter(
        RegionalSowingCalendar.crop_type == crop_type,
        RegionalSowingCalendar.region == region,
        RegionalSowingCalendar.is_deleted == False,
    ).order_by(RegionalSowingCalendar.version_id.desc()).first()

    # Fallback to national default
    if not calendar:
        calendar = db.query(RegionalSowingCalendar).filter(
            RegionalSowingCalendar.crop_type == crop_type,
            RegionalSowingCalendar.region == "national",
            RegionalSowingCalendar.is_deleted == False,
        ).order_by(RegionalSowingCalendar.version_id.desc()).first()

    if not calendar:
        return "Unknown"

    if sowing_date < calendar.optimal_start:
        return "Early"
    elif sowing_date <= calendar.optimal_end:
        return "Optimal"
    else:
        return "Late"
