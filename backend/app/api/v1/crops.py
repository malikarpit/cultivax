"""
Crops API

Crop Instance CRUD with seasonal window assignment.
POST /api/v1/crops
GET  /api/v1/crops
GET  /api/v1/crops/{crop_id}
PUT  /api/v1/crops/{crop_id}
PUT  /api/v1/crops/{crop_id}/sowing-date
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.deviation import DeviationProfile
from app.schemas.crop_instance import (
    CropInstanceCreate, CropInstanceResponse, CropInstanceUpdate,
    SowingDateUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.ctis.crop_service import CropService
from app.services.ctis.seasonal_window import assign_seasonal_window

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("/", response_model=CropInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_crop(
    data: CropInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new crop instance with automatic seasonal window assignment."""
    service = CropService(db)
    crop = service.create_crop(current_user, data)
    return CropInstanceResponse.model_validate(crop)


@router.get("/", response_model=PaginatedResponse[CropInstanceResponse])
async def list_crops(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    crop_type: Optional[str] = None,
    region: Optional[str] = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List crop instances with pagination and filtering."""
    service = CropService(db)
    result = service.list_crops(
        farmer_id=current_user.id,
        page=page,
        per_page=per_page,
        state=state,
        crop_type=crop_type,
        region=region,
        include_archived=include_archived,
    )
    return result


@router.get("/{crop_id}", response_model=CropInstanceResponse)
async def get_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single crop instance by ID."""
    service = CropService(db)
    crop = service.get_crop(crop_id, current_user.id)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}", response_model=CropInstanceResponse)
async def update_crop(
    crop_id: UUID,
    data: CropInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a crop instance (non-state fields only)."""
    service = CropService(db)
    crop = service.update_crop(crop_id, current_user.id, data)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/sowing-date", response_model=CropInstanceResponse)
async def modify_sowing_date(
    crop_id: UUID,
    data: SowingDateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modify sowing date — triggers full replay from scratch.
    Note: seasonal_window_category is NOT recalculated (immutable at creation).
    """
    service = CropService(db)
    crop = service.modify_sowing_date(crop_id, current_user.id, data.new_sowing_date)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)
