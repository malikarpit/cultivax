"""
Offline Sync API

POST  /api/v1/offline-sync/        — bulk action submission with anomaly detection
GET   /api/v1/offline-sync/preview/{crop_id}  — preview pending sync for a crop
GET   /api/v1/offline-sync/history/{crop_id}  — synced offline actions for a crop
GET   /api/v1/offline-sync/anomalies          — farmer's own abuse flags

Audit 15 — Full rewrite with proper schemas, GET endpoints, error handling.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.abuse_flag import AbuseFlag
from app.models.action_log import ActionLog
from app.models.crop_instance import CropInstance
from app.models.user import User
from app.schemas.sync import OfflineSyncRequest, OfflineSyncResponse
from app.services.ctis.sync_service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offline-sync", tags=["Offline Sync"])


# ── POST — Sync offline actions ──


@router.post(
    "/",
    response_model=OfflineSyncResponse,
    dependencies=[Depends(require_role(["farmer"]))],
)
async def submit_offline_sync(
    data: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit bulk actions from offline queue. Farmer only.

    Validates:
    - Batch size (≤500 actions)
    - Sequence monotonicity
    - Backdate (≤7 days) / Future (≤2 hours)
    - Crop ownership & state
    - action_type whitelist
    - Idempotency (duplicate detection via idempotency_key)

    Returns full per-action breakdown: synced, failed, duplicates, anomalies.
    """
    logger.info(
        f"Offline sync request from farmer {current_user.id}: "
        f"{len(data.actions)} actions, device {data.device_id}"
    )

    service = SyncService(db)

    try:
        result = service.process_sync(
            farmer_id=current_user.id,
            actions=[a.model_dump() for a in data.actions],
            device_id=data.device_id,
            session_id=data.session_id,
        )
        db.commit()
        return OfflineSyncResponse(**result)

    except ValueError as e:
        logger.warning(f"Sync validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed",
        )


# ── GET — Preview sync for a crop ──


@router.get("/preview/{crop_id}")
async def preview_offline_actions(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preview: show what has previously synced offline for a crop.
    (Useful for mobile client to display pending before submitting)
    """
    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == current_user.id,
            CropInstance.is_deleted == False,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    offline_count = (
        db.query(ActionLog)
        .filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.source == "offline",
            ActionLog.is_deleted == False,
        )
        .count()
    )

    return {
        "crop_id": str(crop_id),
        "offline_actions_synced": offline_count,
        "crop_state": crop.state,
        "ready_to_sync": crop.state not in ("CLOSED", "ARCHIVED"),
    }


# ── GET — Sync history for a crop ──


@router.get("/history/{crop_id}")
async def get_sync_history(
    crop_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get offline-synced actions for a crop, newest first.
    """
    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == current_user.id,
            CropInstance.is_deleted == False,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    actions = (
        db.query(ActionLog)
        .filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.source == "offline",
            ActionLog.is_deleted == False,
        )
        .order_by(ActionLog.server_timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "action_id": str(a.id),
            "action_type": a.action_type,
            "category": a.category,
            "effective_date": (
                a.effective_date.isoformat() if a.effective_date else None
            ),
            "local_seq_no": a.local_seq_no,
            "synced_at": a.server_timestamp.isoformat() if a.server_timestamp else None,
            "idempotency_key": a.idempotency_key,
        }
        for a in actions
    ]


# ── GET — Farmer's own anomaly flags ──


@router.get("/anomalies")
async def get_sync_anomalies(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get anomaly/abuse flags for the current farmer's syncs.
    Lets the farmer see if their data was flagged.
    """
    flags = (
        db.query(AbuseFlag)
        .filter(
            AbuseFlag.farmer_id == current_user.id,
            AbuseFlag.flag_type == "offline_sync_anomalies",
            AbuseFlag.is_deleted == False,
        )
        .order_by(AbuseFlag.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(f.id),
            "severity": f.severity,
            "anomaly_score": f.anomaly_score,
            "anomalies": (f.details or {}).get("anomalies", []),
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "status": f.status,
        }
        for f in flags
    ]


# ──────────────────────────────────────────────────────────────────────────────
# /crops/{crop_id}/sync-batch — MSDD API parity alias (API-0103 / TDD-8-C0018)
# ──────────────────────────────────────────────────────────────────────────────

crops_sync_router = APIRouter(prefix="/crops", tags=["Offline Sync"])


@crops_sync_router.post(
    "/{crop_id}/sync-batch",
    response_model=OfflineSyncResponse,
    dependencies=[Depends(require_role(["farmer"]))],
    summary="Crop-scoped batch offline sync (API-0103 / TDD-8-C0018)",
)
async def sync_batch_for_crop(
    crop_id: UUID,
    data: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convenience endpoint: POST /crops/{crop_id}/sync-batch

    Accepts a batch of offline actions scoped to a single crop instance.
    Validates crop ownership then delegates to the offline sync service.

    MSDD API-0103 / TDD-8-C0018
    """
    # Validate crop ownership before processing
    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == crop_id,
            CropInstance.is_deleted == False,
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    if crop.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this crop")

    service = SyncService(db)
    try:
        result = service.process_sync(
            farmer_id=current_user.id,
            actions=[a.model_dump() for a in data.actions],
            device_id=data.device_id,
            session_id=data.session_id,
        )
        db.commit()
        return OfflineSyncResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"sync-batch failed for crop {crop_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sync operation failed")
