"""
Feature Flags API

GET /api/v1/features — list all feature flags
PUT /api/v1/features/{flag_name} — toggle a feature flag

ML Kill Switch (ML Enhancement 10):
Admin may disable risk prediction, behavioral adaptation,
and regional clustering. CTIS falls back to deterministic rule engine.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.admin_audit import AdminAuditLog
from app.models.feature_flag import FeatureFlag
from app.models.user import User
from app.services.admin_audit import create_audit_entry
from app.services.feature_flags import invalidate_cache

router = APIRouter(prefix="/features", tags=["Feature Flags"])


class FeatureFlagResponse(BaseModel):
    id: str
    flag_name: str
    is_enabled: bool
    description: Optional[str]
    scope: str
    scope_value: Optional[str]

    class Config:
        from_attributes = True


class FeatureToggleRequest(BaseModel):
    is_enabled: bool
    scope: str = "global"
    scope_value: Optional[str] = None
    reason: str


@router.get(
    "/",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_features(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all feature flags. Admin only."""
    query = db.query(FeatureFlag).filter(FeatureFlag.is_deleted == False)

    if search:
        query = query.filter(FeatureFlag.flag_name.ilike(f"%{search}%"))

    total = query.count()
    flags = (
        query.order_by(FeatureFlag.flag_name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [FeatureFlagResponse.model_validate(f) for f in flags],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.put(
    "/{flag_name}",
    response_model=FeatureFlagResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def toggle_feature(
    flag_name: str,
    data: FeatureToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle a feature flag securely invalidating bound internal cache memory."""
    flag = db.query(FeatureFlag).filter(
        FeatureFlag.flag_name == flag_name,
        FeatureFlag.scope == data.scope,
        FeatureFlag.is_deleted == False,
    )
    if data.scope_value:
        flag = flag.filter(FeatureFlag.scope_value == data.scope_value)
    else:
        flag = flag.filter(FeatureFlag.scope_value == None)

    flag = flag.first()

    if not flag:
        # If it doesn't exist under this explicit scope yet, insert it dynamically.
        flag = FeatureFlag(
            flag_name=flag_name,
            is_enabled=data.is_enabled,
            scope=data.scope,
            scope_value=data.scope_value,
            description=f"Auto-generated scope instantiation for namespace logic.",
        )
        db.add(flag)
        old_val = False
    else:
        old_val = flag.is_enabled
        flag.is_enabled = data.is_enabled

    # Write explicit Audit trace wrapping the boundary execution via helper
    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="feature_toggled",
        entity_type="feature_flag",
        entity_id=flag.id if flag.id else "new_flag",
        reason=data.reason,
        before_value={"old_value": old_val},
        after_value={
            "flag_name": flag_name,
            "new_value": data.is_enabled,
            "scope": data.scope,
            "scope_value": data.scope_value,
        },
    )
    db.refresh(flag)

    # Secure cache sweeping dropping stale paths instantly across any nodes leveraging that namespace.
    invalidate_cache(flag_name)

    return FeatureFlagResponse.model_validate(flag)
