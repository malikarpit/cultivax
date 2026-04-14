"""
Actions API

POST /api/v1/crops/{crop_id}/actions — Log an action with chronological validation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.crop_instance import (ActionLogCreate, ActionLogListResponse,
                                       ActionLogResponse)
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
        return ActionLogResponse.from_action(action)
    except ValueError as e:
        msg = str(e)
        if "idempotency" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=msg
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/", response_model=ActionLogListResponse)
async def list_actions(
    crop_id: UUID,
    page: int = 1,
    page_size: int = 20,
    sort: str = "-effective_date",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List actions for a specific crop instance with pagination."""
    service = ActionService(db)
    try:
        result = service.list_actions_paginated(
            crop_id,
            current_user.id,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        return {
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "has_more": result["has_more"],
            "actions": [ActionLogResponse.from_action(a) for a in result["actions"]],
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
