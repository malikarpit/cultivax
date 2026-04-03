"""
Labor CRUD API

POST   /api/v1/labor       — create labor listing
GET    /api/v1/labor        — list labor (with filters)
GET    /api/v1/labor/{id}   — get specific labor listing
PUT    /api/v1/labor/{id}   — update labor listing
DELETE /api/v1/labor/{id}   — soft-delete labor listing

MSDD Section 2.6 — Labor Marketplace
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.labor import Labor
from app.models.service_provider import ServiceProvider
from app.schemas.labor import LaborCreate, LaborResponse, LaborUpdate, LaborAvailabilityUpdate
from app.schemas.common import PaginatedResponse

from datetime import datetime, timezone

router = APIRouter(prefix="/labor", tags=["Labor"])


@router.post("/", response_model=LaborResponse, status_code=status.HTTP_201_CREATED)
async def create_labor(
    data: LaborCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new labor listing. User must be a registered provider."""
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.user_id == current_user.id,
        ServiceProvider.is_deleted == False,
    ).first()

    if not provider:
        raise HTTPException(status_code=403, detail="Only registered providers can list labor")

    if provider.is_suspended:
        raise HTTPException(status_code=403, detail="Suspended providers cannot create listings")

    labor = Labor(
        provider_id=provider.id,
        labor_type=data.labor_type,
        description=data.description,
        available_units=data.available_units,
        daily_rate=data.daily_rate,
        hourly_rate=data.hourly_rate,
        region=data.region,
        sub_region=data.sub_region,
    )
    db.add(labor)
    db.commit()
    db.refresh(labor)
    return LaborResponse.model_validate(labor)


@router.get("/", response_model=PaginatedResponse[LaborResponse])
async def list_labor(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    labor_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List available labor with optional region and type filters."""
    query = db.query(Labor).options(joinedload(Labor.provider)).filter(
        Labor.is_deleted == False,
    )

    if region:
        query = query.filter(Labor.region == region)
    if labor_type:
        query = query.filter(Labor.labor_type == labor_type)

    total = query.count()
    items = (
        query.order_by(Labor.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    enriched_items = []
    for l in items:
        base = LaborResponse.model_validate(l).dict()
        base["provider_name"] = l.provider.business_name if l.provider else None
        base["provider_is_verified"] = l.provider.is_verified if l.provider else False
        base["provider_trust_score"] = l.provider.trust_score if l.provider else None
        enriched_items.append(LaborResponse(**base))

    return PaginatedResponse(
        items=enriched_items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/{labor_id}", response_model=LaborResponse)
async def get_labor(
    labor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific labor listing by ID."""
    labor = db.query(Labor).filter(
        Labor.id == labor_id,
        Labor.is_deleted == False,
    ).first()
    if not labor:
        raise HTTPException(status_code=404, detail="Labor listing not found")
    return LaborResponse.model_validate(labor)


@router.put("/{labor_id}", response_model=LaborResponse)
async def update_labor(
    labor_id: UUID,
    data: LaborUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a labor listing. Only the owning provider can update."""
    labor = db.query(Labor).filter(
        Labor.id == labor_id,
        Labor.is_deleted == False,
    ).first()
    if not labor:
        raise HTTPException(status_code=404, detail="Labor listing not found")

    # Verify ownership
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == labor.provider_id,
        ServiceProvider.user_id == current_user.id,
    ).first()
    if not provider:
        raise HTTPException(status_code=403, detail="You do not own this labor listing")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(labor, key, value)
        
    labor.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(labor)
    return LaborResponse.model_validate(labor)


@router.patch("/{labor_id}/availability", response_model=LaborResponse)
async def toggle_availability(
    labor_id: UUID,
    data: LaborAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle labor listing availability explicitly."""
    labor = db.query(Labor).filter(
        Labor.id == labor_id,
        Labor.is_deleted == False,
    ).first()
    if not labor:
        raise HTTPException(status_code=404, detail="Labor listing not found")

    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == labor.provider_id,
        ServiceProvider.user_id == current_user.id,
    ).first()
    if not provider:
        raise HTTPException(status_code=403, detail="You do not own this labor listing")

    labor.is_available = data.is_available
    labor.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(labor)
    return LaborResponse.model_validate(labor)


@router.delete("/{labor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_labor(
    labor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a labor listing. Only the owning provider can delete."""
    labor = db.query(Labor).filter(
        Labor.id == labor_id,
        Labor.is_deleted == False,
    ).first()
    if not labor:
        raise HTTPException(status_code=404, detail="Labor listing not found")

    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == labor.provider_id,
        ServiceProvider.user_id == current_user.id,
    ).first()
    if not provider:
        raise HTTPException(status_code=403, detail="You do not own this labor listing")

    labor.is_deleted = True
    labor.deleted_at = datetime.now(timezone.utc)
    labor.deleted_by = current_user.id
    db.commit()
