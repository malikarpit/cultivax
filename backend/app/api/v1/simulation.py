"""
Simulation API

What-If Simulation endpoint for testing hypothetical actions.
POST /api/v1/crops/{crop_id}/simulate
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ctis.whatif_engine import WhatIfEngine

router = APIRouter(prefix="/crops", tags=["Simulation"])


class HypotheticalAction(BaseModel):
    """Schema for a hypothetical action in what-if simulation."""
    action_type: str
    action_date: Optional[str] = None
    metadata: Optional[dict] = None


class SimulationRequest(BaseModel):
    """Request body for what-if simulation."""
    hypothetical_actions: List[HypotheticalAction]


class SimulationResponse(BaseModel):
    """Response from what-if simulation."""
    projected_state: str
    projected_stress: float
    projected_risk: float
    projected_day_number: int
    projected_stage: Optional[str]
    actions_applied: int
    state_transitions: List[dict]
    warnings: List[str]


@router.post("/{crop_id}/simulate", response_model=SimulationResponse)
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
    """
    engine = WhatIfEngine(db)

    try:
        actions = [a.model_dump() for a in request.hypothetical_actions]
        result = await engine.simulate(crop_id, actions)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SimulationResponse.model_validate({
        "projected_state": result.projected_state,
        "projected_stress": result.projected_stress,
        "projected_risk": result.projected_risk,
        "projected_day_number": result.projected_day_number,
        "projected_stage": result.projected_stage,
        "actions_applied": result.actions_applied,
        "state_transitions": result.state_transitions,
        "warnings": result.warnings,
    })
