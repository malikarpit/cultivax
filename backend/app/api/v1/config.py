"""
Configuration API — Platform Extensibility

Allows admins to dynamically manage region configurations and other
platform-wide settings without code changes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.region_config import RegionConfig
from app.models.user import User

router = APIRouter(prefix="/config", tags=["Configuration"])


def _require_admin(cu: User = Depends(get_current_user)) -> User:
    if cu.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return cu


class RegionConfigPayload(BaseModel):
    region_name: str
    is_active: bool = True
    parameters: dict


@router.post("/regions", status_code=201)
async def create_region_config(
    req: RegionConfigPayload,
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Add a new region configuration."""
    existing = (
        db.query(RegionConfig)
        .filter(
            RegionConfig.region_name == req.region_name,
            RegionConfig.is_deleted == False,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Region already exists")

    new_region = RegionConfig(
        region_name=req.region_name,
        is_active=req.is_active,
        parameters=req.parameters,
    )
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    return new_region


@router.get("/regions")
async def list_regions(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List all region configurations. Publicly accessible for frontend dropdowns."""
    q = db.query(RegionConfig).filter(RegionConfig.is_deleted == False)
    if active_only:
        q = q.filter(RegionConfig.is_active == True)

    # Return limited fields for non-admins if needed, but here we return all
    regions = q.all()
    return {
        "items": [
            {
                "id": str(r.id),
                "region_name": r.region_name,
                "is_active": r.is_active,
                "parameters": r.parameters,
            }
            for r in regions
        ]
    }


@router.put("/regions/{region_id}")
async def update_region_config(
    region_id: UUID,
    req: RegionConfigPayload,
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Update an existing region configuration."""
    region = (
        db.query(RegionConfig)
        .filter(RegionConfig.id == region_id, RegionConfig.is_deleted == False)
        .first()
    )
    if not region:
        raise HTTPException(status_code=404, detail="Region config not found")

    region.region_name = req.region_name
    region.is_active = req.is_active
    region.parameters = req.parameters

    db.commit()
    db.refresh(region)
    return region


@router.delete("/regions/{region_id}")
async def delete_region_config(
    region_id: UUID,
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Soft-delete a region configuration."""
    region = (
        db.query(RegionConfig)
        .filter(RegionConfig.id == region_id, RegionConfig.is_deleted == False)
        .first()
    )
    if not region:
        raise HTTPException(status_code=404, detail="Region config not found")

    region.is_deleted = True
    db.commit()
    return {"status": "deleted"}
