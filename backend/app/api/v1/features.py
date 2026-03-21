"""
Feature Flags API

GET /api/v1/features — list all feature flags
PUT /api/v1/features/{flag_name} — toggle a feature flag

ML Kill Switch (ML Enhancement 10):
Admin may disable risk prediction, behavioral adaptation,
and regional clustering. CTIS falls back to deterministic rule engine.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.feature_flag import FeatureFlag

router = APIRouter(prefix="/features", tags=["Feature Flags"])


class FeatureFlagResponse(BaseModel):
    id: str
    flag_name: str
    is_enabled: bool
    description: Optional[str]

    class Config:
        from_attributes = True


class FeatureToggleRequest(BaseModel):
    is_enabled: bool


@router.get("/", response_model=list[FeatureFlagResponse])
async def list_features(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all feature flags."""
    flags = db.query(FeatureFlag).filter(FeatureFlag.is_deleted == False).all()
    return [FeatureFlagResponse.model_validate(f) for f in flags]


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
    """Toggle a feature flag (admin only). Implements ML Kill Switch."""
    flag = db.query(FeatureFlag).filter(
        FeatureFlag.flag_name == flag_name,
        FeatureFlag.is_deleted == False,
    ).first()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

    flag.is_enabled = data.is_enabled
    db.commit()
    db.refresh(flag)
    return FeatureFlagResponse.model_validate(flag)
