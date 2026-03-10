"""
Actions API

POST /api/v1/crops/{crop_id}/actions — Log an action with chronological validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.crop_instance import ActionLogCreate, ActionLogResponse
from app.services.ctis.action_service import ActionService

router = APIRouter(prefix="/crops/{crop_id}/actions", tags=["Actions"])


@router.post("/", response_model=ActionLogResponse, status_code=status.HTTP_201_CREATED)
async def log_action(
    crop_id: UUID,
    data: ActionLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a farmer action on a crop instance.
    
    Enforces chronological invariant:
    - action.effective_date >= sowing_date
    - action.effective_date >= last_action.effective_date (within same crop)
    
    Rejects if idempotency_key already exists.
    """
    service = ActionService(db)
    try:
        action = service.log_action(crop_id, current_user.id, data)
        return ActionLogResponse.model_validate(action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
