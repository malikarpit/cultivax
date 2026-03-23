"""
Offline Sync API

POST /api/v1/offline-sync — bulk action submission with temporal anomaly detection

MSDD 1.7.1 — Temporal Anomaly Detection
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ctis.sync_service import SyncService

router = APIRouter(prefix="/offline-sync", tags=["Offline Sync"])


class OfflineAction(BaseModel):
    crop_instance_id: str
    action_type: str
    action_effective_date: str
    local_seq_no: int
    metadata: dict = {}


class OfflineSyncRequest(BaseModel):
    actions: List[OfflineAction]
    device_id: str = ""
    session_id: str = ""


class SyncResponse(BaseModel):
    processed: int
    rejected: int
    anomalies_detected: int
    details: List[dict]


@router.post("/", response_model=SyncResponse)
async def submit_offline_sync(
    data: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit bulk actions from offline queue.

    Validates temporal anomalies:
    - Excessive back-dated actions
    - Excessive future-dated actions
    - Large batch anomalies
    - Monotonic counter resets
    """
    service = SyncService(db)
    try:
        result = service.process_sync(
            farmer_id=current_user.id,
            actions=[a.model_dump() for a in data.actions],
            device_id=data.device_id,
            session_id=data.session_id,
        )
        return SyncResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
