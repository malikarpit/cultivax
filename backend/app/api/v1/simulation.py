"""
Simulation API

What-If Simulation endpoint for testing hypothetical actions.
POST /api/v1/crops/{crop_id}/simulate
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.ctis.whatif_engine import WhatIfEngine

router = APIRouter(prefix="/crops", tags=["Simulation"])


@router.post(
    "/{crop_id}/simulate",
    response_model=SimulationResponse,
    dependencies=[Depends(require_role(["farmer"]))],
)
async def simulate_crop(
    crop_id: UUID,
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a what-if simulation on a crop instance.

    Applies hypothetical actions in an isolated context to project future
    state without modifying any live data (MSDD 1.14).
    Only the crop owner may simulate.
    """
    # Ownership check — farmer can only simulate their own crops
    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this crop",
        )
    if crop.state in {"Closed", "Archived"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot simulate a closed crop",
        )

    engine = WhatIfEngine(db)

    try:
        actions = [a.model_dump() for a in request.hypothetical_actions]
        result = await engine.simulate(crop_id, actions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SimulationResponse.model_validate(result.to_response())


@router.post(
    "/{crop_id}/what-if",
    response_model=SimulationResponse,
    dependencies=[Depends(require_role(["farmer"]))],
    summary="What-if simulation (API-0104, alias for /{crop_id}/simulate)",
)
async def what_if_crop(
    crop_id: UUID,
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Alias for POST /crops/{crop_id}/simulate.

    The MSDD names this endpoint 'what-if' (MSDD-8-C0024 / API-0104).
    Delegates directly to simulate_crop.
    """
    return await simulate_crop(crop_id=crop_id, request=request, db=db, current_user=current_user)

