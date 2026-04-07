"""
Analytics Service — FR-35, NFR-15, NFR-33, OR-12/13

Aggregates platform-wide metrics for admin monitoring dashboards.
All queries use DB-level aggregations — no in-memory loops on large tables.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, text
from sqlalchemy.orm import Session


class AnalyticsService:
    """Compute platform analytics using efficient SQL aggregations."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Overview (FR-35, OR-12)
    # -------------------------------------------------------------------------

    def get_overview(self) -> dict[str, Any]:
        """Top-level platform KPIs: user counts, crop counts, alert totals."""
        from app.models.alert import Alert
        from app.models.crop_instance import CropInstance
        from app.models.user import User

        total_users = (
            self.db.query(func.count(User.id)).filter(User.is_deleted == False).scalar()
            or 0
        )
        active_users = (
            self.db.query(func.count(User.id))
            .filter(User.is_active == True, User.is_deleted == False)
            .scalar()
            or 0
        )
        farmer_count = (
            self.db.query(func.count(User.id))
            .filter(User.role == "farmer", User.is_deleted == False)
            .scalar()
            or 0
        )
        provider_count = (
            self.db.query(func.count(User.id))
            .filter(User.role == "service_provider", User.is_deleted == False)
            .scalar()
            or 0
        )
        admin_count = (
            self.db.query(func.count(User.id))
            .filter(User.role == "admin", User.is_deleted == False)
            .scalar()
            or 0
        )

        total_crops = (
            self.db.query(func.count(CropInstance.id))
            .filter(CropInstance.is_deleted == False)
            .scalar()
            or 0
        )
        active_crops = (
            self.db.query(func.count(CropInstance.id))
            .filter(
                CropInstance.state.in_(["Active", "AtRisk"]),
                CropInstance.is_deleted == False,
            )
            .scalar()
            or 0
        )
        at_risk_crops = (
            self.db.query(func.count(CropInstance.id))
            .filter(CropInstance.state == "AtRisk", CropInstance.is_deleted == False)
            .scalar()
            or 0
        )

        total_alerts = (
            self.db.query(func.count(Alert.id))
            .filter(Alert.is_deleted == False)
            .scalar()
            or 0
        )
        unacked_alerts = (
            self.db.query(func.count(Alert.id))
            .filter(Alert.is_acknowledged == False, Alert.is_deleted == False)
            .scalar()
            or 0
        )

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "farmers": farmer_count,
                "providers": provider_count,
                "admins": admin_count,
            },
            "crops": {
                "total": total_crops,
                "active": active_crops,
                "at_risk": at_risk_crops,
                "health_rate": round(
                    (active_crops - at_risk_crops) / max(active_crops, 1) * 100, 1
                ),
            },
            "alerts": {
                "total": total_alerts,
                "unacknowledged": unacked_alerts,
            },
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------------------
    # Activity timeline (OR-12, NFR-33)
    # -------------------------------------------------------------------------

    def get_activity_timeline(self, days: int = 30) -> list[dict[str, Any]]:
        """Daily new user and crop registrations for the last N days."""
        from app.models.crop_instance import CropInstance
        from app.models.user import User

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        user_by_day = dict(
            self.db.query(
                func.date_trunc("day", User.created_at).label("day"),
                func.count(User.id),
            )
            .filter(User.created_at >= cutoff, User.is_deleted == False)
            .group_by(text("day"))
            .all()
        )

        crop_by_day = dict(
            self.db.query(
                func.date_trunc("day", CropInstance.created_at).label("day"),
                func.count(CropInstance.id),
            )
            .filter(CropInstance.created_at >= cutoff, CropInstance.is_deleted == False)
            .group_by(text("day"))
            .all()
        )

        all_dates = sorted(set(list(user_by_day.keys()) + list(crop_by_day.keys())))
        return [
            {
                "date": (
                    d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
                ),
                "new_users": user_by_day.get(d, 0),
                "new_crops": crop_by_day.get(d, 0),
            }
            for d in all_dates
        ]

    # -------------------------------------------------------------------------
    # Crop distribution (OR-13)
    # -------------------------------------------------------------------------

    def get_crop_distribution(self) -> dict[str, Any]:
        """Breakdown of crops by type, season, and state."""
        from app.models.crop_instance import CropInstance

        by_type = (
            self.db.query(CropInstance.crop_type, func.count(CropInstance.id))
            .filter(CropInstance.is_deleted == False)
            .group_by(CropInstance.crop_type)
            .all()
        )

        by_state = (
            self.db.query(CropInstance.state, func.count(CropInstance.id))
            .filter(CropInstance.is_deleted == False)
            .group_by(CropInstance.state)
            .all()
        )

        by_season = (
            self.db.query(
                CropInstance.seasonal_window_category, func.count(CropInstance.id)
            )
            .filter(CropInstance.is_deleted == False)
            .group_by(CropInstance.seasonal_window_category)
            .all()
        )

        return {
            "by_type": [{"label": k or "Unknown", "count": v} for k, v in by_type],
            "by_state": [{"label": k or "Unknown", "count": v} for k, v in by_state],
            "by_season": [{"label": k or "Unknown", "count": v} for k, v in by_season],
        }

    # -------------------------------------------------------------------------
    # Demand heatmap (OR-13, NFR-15)
    # -------------------------------------------------------------------------

    def get_region_demand(self) -> list[dict[str, Any]]:
        """Per-region crop count and at-risk ratio for demand heatmap."""
        from app.models.crop_instance import CropInstance

        rows = (
            self.db.query(
                CropInstance.region,
                func.count(CropInstance.id).label("total"),
                func.sum(case((CropInstance.state == "AtRisk", 1), else_=0)).label(
                    "at_risk"
                ),
            )
            .filter(
                CropInstance.is_deleted == False,
                CropInstance.region.isnot(None),
            )
            .group_by(CropInstance.region)
            .all()
        )

        return [
            {
                "region": r.region,
                "total_crops": r.total,
                "at_risk": int(r.at_risk or 0),
                "risk_rate": round(int(r.at_risk or 0) / max(r.total, 1) * 100, 1),
            }
            for r in rows
        ]
