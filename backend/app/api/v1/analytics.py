"""
Analytics API — FR-35, NFR-15, OR-12/13

Admin-only endpoints for platform monitoring dashboards.

Routes:
  GET /analytics/overview            — KPI snapshot (users, crops, alerts)
  GET /analytics/activity?days=30    — daily new registrations timeline
  GET /analytics/crops/distribution  — crop type/state/season breakdown
  GET /analytics/regions/demand      — per-region demand and risk heatmap
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    from fastapi import HTTPException

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/overview")
async def get_overview(
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Platform KPI snapshot — user counts, crop health, unacknowledged alerts."""
    return AnalyticsService(db).get_overview()


@router.get("/activity")
async def get_activity_timeline(
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to look back"
    ),
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Daily new user and crop registrations for admin timeline chart."""
    return {
        "timeline": AnalyticsService(db).get_activity_timeline(days=days),
        "days": days,
    }


@router.get("/crops/distribution")
async def get_crop_distribution(
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Crop breakdown by type, lifecycle state, and season."""
    return AnalyticsService(db).get_crop_distribution()


@router.get("/regions/demand")
async def get_region_demand(
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Per-region crop count and at-risk ratio for demand heatmap."""
    return {"regions": AnalyticsService(db).get_region_demand()}
