"""
Dashboard API — Aggregated stats for frontend dashboards

GET /api/v1/dashboard/stats       — Farmer/Provider dashboard stats
GET /api/v1/dashboard/admin-stats — Admin platform-wide stats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.alert import Alert
from app.models.service_request import ServiceRequest
from app.models.service_provider import ServiceProvider

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get personalized dashboard stats for the current user.

    Returns role-specific metrics:
    - Farmer: active crops, crops needing action, alerts, services booked
    - Provider: pending requests, active jobs, completed jobs, trust score
    """
    if current_user.role == "farmer":
        return _farmer_stats(db, current_user)
    elif current_user.role == "provider":
        return _provider_stats(db, current_user)
    else:
        return _admin_quick_stats(db)


@router.get("/admin-stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Get platform-wide admin dashboard stats."""
    total_users = (
        db.query(func.count(User.id))
        .filter(User.is_deleted == False, User.is_active == True)
        .scalar()
    ) or 0

    total_crops = (
        db.query(func.count(CropInstance.id))
        .filter(CropInstance.is_deleted == False)
        .scalar()
    ) or 0

    active_crops = (
        db.query(func.count(CropInstance.id))
        .filter(
            CropInstance.is_deleted == False,
            CropInstance.state.in_(["Active", "Created", "Delayed", "AtRisk"]),
        )
        .scalar()
    ) or 0

    total_providers = (
        db.query(func.count(ServiceProvider.id))
        .filter(ServiceProvider.is_deleted == False)
        .scalar()
    ) or 0

    verified_providers = (
        db.query(func.count(ServiceProvider.id))
        .filter(
            ServiceProvider.is_deleted == False,
            ServiceProvider.is_verified == True,
        )
        .scalar()
    ) or 0

    pending_issues = (
        db.query(func.count(Alert.id))
        .filter(
            Alert.is_deleted == False,
            Alert.is_acknowledged == False,
        )
        .scalar()
    ) or 0

    # Farmers by region (top 5)
    region_breakdown = (
        db.query(User.region, func.count(User.id))
        .filter(
            User.role == "farmer",
            User.is_deleted == False,
            User.region.isnot(None),
        )
        .group_by(User.region)
        .order_by(func.count(User.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_users": total_users,
        "total_crops": total_crops,
        "active_crops": active_crops,
        "total_providers": total_providers,
        "verified_providers": verified_providers,
        "pending_issues": pending_issues,
        "region_breakdown": [
            {"region": r, "count": c} for r, c in region_breakdown
        ],
    }


def _farmer_stats(db: Session, user: User) -> dict:
    """Farmer-specific dashboard statistics."""
    # Active crops
    active_crops = (
        db.query(func.count(CropInstance.id))
        .filter(
            CropInstance.farmer_id == user.id,
            CropInstance.is_deleted == False,
            CropInstance.state.in_(["Active", "Created", "Delayed", "AtRisk"]),
        )
        .scalar()
    ) or 0

    # Crops needing action (high stress or at risk)
    crops_needing_action = (
        db.query(func.count(CropInstance.id))
        .filter(
            CropInstance.farmer_id == user.id,
            CropInstance.is_deleted == False,
            CropInstance.state.in_(["AtRisk", "Delayed"]),
        )
        .scalar()
    ) or 0

    # Pending alerts
    alerts_due = (
        db.query(func.count(Alert.id))
        .filter(
            Alert.user_id == user.id,
            Alert.is_deleted == False,
            Alert.is_acknowledged == False,
        )
        .scalar()
    ) or 0

    # Services booked
    services_booked = (
        db.query(func.count(ServiceRequest.id))
        .filter(
            ServiceRequest.farmer_id == user.id,
            ServiceRequest.is_deleted == False,
            ServiceRequest.status.in_(
                ["pending", "accepted", "in_progress"]
            ),
        )
        .scalar()
    ) or 0

    return {
        "role": "farmer",
        "active_crops": active_crops,
        "crops_needing_action": crops_needing_action,
        "alerts_due_today": alerts_due,
        "services_booked": services_booked,
        "is_onboarded": user.is_onboarded,
        "region": user.region,
    }


def _provider_stats(db: Session, user: User) -> dict:
    """Provider-specific dashboard statistics."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.user_id == user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )

    if not provider:
        return {
            "role": "provider",
            "pending_requests": 0,
            "active_jobs": 0,
            "completed_jobs": 0,
            "trust_score": 0.0,
            "is_verified": False,
        }

    pending = (
        db.query(func.count(ServiceRequest.id))
        .filter(
            ServiceRequest.provider_id == provider.id,
            ServiceRequest.status == "pending",
        )
        .scalar()
    ) or 0

    active = (
        db.query(func.count(ServiceRequest.id))
        .filter(
            ServiceRequest.provider_id == provider.id,
            ServiceRequest.status.in_(["accepted", "in_progress"]),
        )
        .scalar()
    ) or 0

    completed = (
        db.query(func.count(ServiceRequest.id))
        .filter(
            ServiceRequest.provider_id == provider.id,
            ServiceRequest.status == "completed",
        )
        .scalar()
    ) or 0

    return {
        "role": "provider",
        "pending_requests": pending,
        "active_jobs": active,
        "completed_jobs": completed,
        "trust_score": float(provider.trust_score or 0.0),
        "is_verified": provider.is_verified,
    }


def _admin_quick_stats(db: Session) -> dict:
    """Quick stats for admin shown on the regular stats endpoint."""
    return {
        "role": "admin",
        "active_crops": (
            db.query(func.count(CropInstance.id))
            .filter(
                CropInstance.is_deleted == False,
                CropInstance.state.in_(["Active", "Created"]),
            )
            .scalar()
        )
        or 0,
        "alerts_due_today": (
            db.query(func.count(Alert.id))
            .filter(
                Alert.is_deleted == False,
                Alert.is_acknowledged == False,
            )
            .scalar()
        )
        or 0,
        "is_onboarded": True,
    }
