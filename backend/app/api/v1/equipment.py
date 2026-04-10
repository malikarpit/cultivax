"""
Equipment API

Provider equipment management endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.equipment import Equipment
from app.models.service_provider import ServiceProvider
from app.models.user import User
from app.schemas.equipment import (EquipmentAvailabilityUpdate,
                                   EquipmentCreate, EquipmentResponse,
                                   EquipmentType, EquipmentUpdate,
                                   PaginatedEquipmentResponse)

router = APIRouter(prefix="/providers/{provider_id}/equipment", tags=["Equipment"])


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def add_equipment(
    provider_id: UUID,
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add equipment to a provider's listing."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.user_id == current_user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=403, detail="Provider not found or not owned by you"
        )

    equipment = Equipment(
        provider_id=provider_id,
        equipment_type=data.equipment_type.value,
        name=data.name,
        description=data.description,
        hourly_rate=data.hourly_rate,
        daily_rate=data.daily_rate,
        condition=data.condition.value,
        is_available=data.is_available,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return EquipmentResponse.model_validate(equipment)


@router.get("/", response_model=PaginatedEquipmentResponse)
async def list_equipment(
    provider_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_available: Optional[bool] = None,
    equipment_type: Optional[EquipmentType] = None,
    db: Session = Depends(get_db),
    # Intentionally removed `current_user` dependency from the parameter
    # to allow the Farmer side discovery surfaces to passively list equipment.
):
    """List all active equipment for a provider natively handling paginations."""
    query = db.query(Equipment).filter(
        Equipment.provider_id == provider_id,
        Equipment.is_deleted == False,
    )

    if is_available is not None:
        query = query.filter(Equipment.is_available == is_available)

    if equipment_type is not None:
        query = query.filter(Equipment.equipment_type == equipment_type.value)

    total = query.count()
    items = (
        query.order_by(Equipment.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    response_items = []
    for e in items:
        resp = EquipmentResponse.model_validate(e)
        response_items.append(resp)

    return PaginatedEquipmentResponse(
        items=response_items, total=total, page=page, per_page=per_page
    )


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    provider_id: UUID,
    equipment_id: UUID,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely updates native provider equipment mappings matching ownership chains."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.user_id == current_user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=403, detail="Provider not found or not owned by you"
        )

    equipment = (
        db.query(Equipment)
        .filter(
            Equipment.id == equipment_id,
            Equipment.provider_id == provider_id,
            Equipment.is_deleted == False,
        )
        .first()
    )

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    update_data = data.model_dump(exclude_unset=True)
    if "equipment_type" in update_data:
        update_data["equipment_type"] = update_data["equipment_type"].value
    if "condition" in update_data:
        update_data["condition"] = update_data["condition"].value

    for key, value in update_data.items():
        setattr(equipment, key, value)

    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return EquipmentResponse.model_validate(equipment)


@router.patch("/{equipment_id}/availability", response_model=EquipmentResponse)
async def toggle_availability(
    provider_id: UUID,
    equipment_id: UUID,
    data: EquipmentAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provides rapid status overrides."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.user_id == current_user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )

    if not provider:
        raise HTTPException(status_code=403, detail="Provider access forbidden")

    equipment = (
        db.query(Equipment)
        .filter(
            Equipment.id == equipment_id,
            Equipment.provider_id == provider_id,
            Equipment.is_deleted == False,
        )
        .first()
    )

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    equipment.is_available = data.is_available
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return EquipmentResponse.model_validate(equipment)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_equipment(
    provider_id: UUID,
    equipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handles secure soft removals keeping historical relationships intact."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.user_id == current_user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )

    if not provider:
        raise HTTPException(status_code=403, detail="Provider access forbidden")

    equipment = (
        db.query(Equipment)
        .filter(
            Equipment.id == equipment_id,
            Equipment.provider_id == provider_id,
            Equipment.is_deleted == False,
        )
        .first()
    )

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    equipment.is_deleted = True
    db.add(equipment)
    db.commit()
    return None
