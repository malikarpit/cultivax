"""
Operations API

Compatibility endpoint for long-running operation tracking:
GET /api/v1/operations/{operation_id}
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.event_log import EventLog
from app.models.user import User

router = APIRouter(prefix="/operations", tags=["Operations"])

_STATUS_MAP = {
    "Created": ("queued", 10),
    "Processing": ("processing", 60),
    "Completed": ("completed", 100),
    "Failed": ("failed", 100),
    "DeadLetter": ("failed", 100),
}


@router.get("/{operation_id}")
async def get_operation_status(
    operation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return operation status/progress for long-running backend jobs.

    Current implementation treats operation IDs as EventLog IDs.
    """
    event = db.query(EventLog).filter(
        EventLog.id == operation_id,
        EventLog.is_deleted == False,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Operation not found")

    status, progress = _STATUS_MAP.get(event.status, ("unknown", 0))
    response = {
        "operation_id": str(event.id),
        "status": status,
        "progress": progress,
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "entity_id": str(event.entity_id),
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "processed_at": event.processed_at.isoformat() if event.processed_at else None,
    }
    if event.failure_reason:
        response["failure_reason"] = event.failure_reason
    return response
