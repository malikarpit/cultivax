"""
Land Parcels API

CRUD endpoints for farmer land parcel management with GPS boundaries.
POST   /api/v1/land-parcels
GET    /api/v1/land-parcels
GET    /api/v1/land-parcels/{parcel_id}
PUT    /api/v1/land-parcels/{parcel_id}
DELETE /api/v1/land-parcels/{parcel_id}
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.land_parcel import (
    LandParcelCreate,
    LandParcelUpdate,
    LandParcelResponse,
)
from app.services.land_parcel_service import LandParcelService

router = APIRouter(prefix="/land-parcels", tags=["Land Parcels"])


@router.post(
    "/",
    response_model=LandParcelResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def create_parcel(
    data: LandParcelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new land parcel with GPS boundary polygon.

    The boundary polygon is used to:
    - Auto-compute area in acres (if not provided manually)
    - Calculate centroid for weather data lookups
    - Display on the interactive map
    """
    service = LandParcelService(db)
    parcel = service.create_parcel(current_user, data)
    return _enrich_response(parcel)


@router.get(
    "/",
    response_model=List[LandParcelResponse],
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def list_parcels(
    include_deleted: bool = Query(False, description="Include soft-deleted parcels"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all land parcels for the authenticated farmer."""
    service = LandParcelService(db)
    parcels = service.list_parcels(current_user.id, include_deleted=include_deleted)
    return [_enrich_response(p) for p in parcels]


@router.get(
    "/{parcel_id}",
    response_model=LandParcelResponse,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def get_parcel(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific land parcel with full boundary data."""
    service = LandParcelService(db)
    parcel = service.get_parcel(parcel_id, current_user.id)
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land parcel not found",
        )
    return _enrich_response(parcel)


@router.put(
    "/{parcel_id}",
    response_model=LandParcelResponse,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def update_parcel(
    parcel_id: UUID,
    data: LandParcelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update land parcel boundaries, soil info, or metadata."""
    service = LandParcelService(db)
    parcel = service.update_parcel(parcel_id, current_user.id, data)
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land parcel not found",
        )
    return _enrich_response(parcel)


@router.delete(
    "/{parcel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def delete_parcel(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a land parcel."""
    service = LandParcelService(db)
    deleted = service.delete_parcel(parcel_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land parcel not found",
        )
    return None


@router.post(
    "/{parcel_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def restore_parcel(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restore a soft-deleted land parcel."""
    service = LandParcelService(db)
    restored = service.restore_parcel(parcel_id, current_user.id)
    if not restored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Land parcel not found",
        )
    return None


def _enrich_response(parcel) -> dict:
    """Add computed fields to parcel response."""
    data = {
        "id": parcel.id,
        "farmer_id": parcel.farmer_id,
        "parcel_name": parcel.parcel_name,
        "region": parcel.region,
        "sub_region": parcel.sub_region,
        "land_area": parcel.land_area,
        "land_area_unit": parcel.land_area_unit,
        "soil_type": parcel.soil_type,
        "gps_coordinates": parcel.gps_coordinates,
        "irrigation_source": parcel.irrigation_source,
        "is_deleted": parcel.is_deleted,
        "created_at": parcel.created_at,
        "updated_at": parcel.updated_at,
        "area_from_polygon": None,
        "centroid": None,
    }

    # Extract computed fields from gps_coordinates if available
    gps = parcel.gps_coordinates or {}
    if "computed_area_acres" in gps:
        data["area_from_polygon"] = gps["computed_area_acres"]
    if "centroid" in gps:
        data["centroid"] = gps["centroid"]

    return data
