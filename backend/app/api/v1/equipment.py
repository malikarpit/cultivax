"""
Equipment API

Provider equipment management endpoints.
POST /api/v1/providers/{provider_id}/equipment
GET  /api/v1/providers/{provider_id}/equipment
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.service_provider import ServiceProvider
from app.models.equipment import Equipment
from app.schemas.service_provider import EquipmentCreate, EquipmentResponse

router = APIRouter(prefix="/providers/{provider_id}/equipment", tags=["Equipment"])


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def add_equipment(
    provider_id: UUID,
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add equipment to a provider's listing."""
    # Verify provider exists and belongs to current user
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == provider_id,
        ServiceProvider.user_id == current_user.id,
        ServiceProvider.is_deleted == False,
    ).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found or not owned by you")

    equipment = Equipment(
        provider_id=provider_id,
        equipment_type=data.equipment_type,
        name=data.name,
        description=data.description,
        hourly_rate=data.hourly_rate,
        daily_rate=data.daily_rate,
        condition=data.condition,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return EquipmentResponse.model_validate(equipment)


@router.get("/", response_model=list[EquipmentResponse])
async def list_equipment(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all equipment for a provider."""
    equipment_list = db.query(Equipment).filter(
        Equipment.provider_id == provider_id,
        Equipment.is_deleted == False,
    ).all()
    return [EquipmentResponse.model_validate(e) for e in equipment_list]
