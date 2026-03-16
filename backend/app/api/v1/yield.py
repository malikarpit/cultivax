"""
Yield API

Yield submission endpoint for crop harvest recording.
POST /api/v1/crops/{crop_id}/yield
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.yield_record import YieldSubmission, YieldResponse
from app.services.ctis.yield_service import YieldService

router = APIRouter(prefix="/crops", tags=["Yield"])


@router.post(
    "/{crop_id}/yield",
    response_model=YieldResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_yield(
    crop_id: UUID,
    data: YieldSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit yield data for a crop instance.

    - Computes YieldVerificationScore from stress history and weather
    - Enforces biological limit cap on ml_yield_value
    - reported_yield is NEVER modified (Farmer Truth — MSDD 1.12)
    - ml_yield_value computed separately (ML Truth)
    - Transitions crop to 'Harvested' state
    """
    service = YieldService(db)
    try:
        result = service.submit_yield(crop_id, current_user.id, data)
        return YieldResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
