"""
Crops API

Crop Instance CRUD with seasonal window assignment.
POST /api/v1/crops
GET  /api/v1/crops
GET  /api/v1/crops/{crop_id}
PUT  /api/v1/crops/{crop_id}
PUT  /api/v1/crops/{crop_id}/sowing-date
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID
import hashlib
import json

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.deviation import DeviationProfile
from app.models.snapshot import CropInstanceSnapshot
from app.models.action_log import ActionLog
from app.models.event_log import EventLog
from app.schemas.crop_instance import (
    CropInstanceCreate, CropInstanceResponse, CropInstanceUpdate,
    SowingDateUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.ctis.crop_service import CropService
from app.services.ctis.seasonal_window import assign_seasonal_window
from app.services.ctis.replay_engine import ReplayEngine, ReplayError

router = APIRouter(prefix="/crops", tags=["Crops"])


def _get_crop_for_user(db: Session, crop_id: UUID, current_user: User) -> Optional[CropInstance]:
    query = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    )
    if current_user.role != "admin":
        query = query.filter(CropInstance.farmer_id == current_user.id)
    return query.first()


@router.post("/", response_model=CropInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_crop(
    data: CropInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new crop instance with automatic seasonal window assignment."""
    service = CropService(db)
    try:
        crop = service.create_crop(current_user, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return CropInstanceResponse.model_validate(crop)


@router.get("/", response_model=PaginatedResponse[CropInstanceResponse])
async def list_crops(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    crop_type: Optional[str] = None,
    region: Optional[str] = None,
    include_archived: bool = False,
    search: Optional[str] = None,
    seasonal_window_category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List crop instances with pagination and filtering."""
    service = CropService(db)
    result = service.list_crops(
        farmer_id=current_user.id,
        page=page,
        per_page=per_page,
        state=state,
        crop_type=crop_type,
        region=region,
        include_archived=include_archived,
        search=search,
        seasonal_window_category=seasonal_window_category,
    )
    return result


@router.get("/{crop_id}", response_model=CropInstanceResponse)
async def get_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single crop instance by ID."""
    service = CropService(db)
    crop = service.get_crop(crop_id, current_user.id)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}", response_model=CropInstanceResponse)
async def update_crop(
    crop_id: UUID,
    data: CropInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a crop instance (non-state fields only)."""
    service = CropService(db)
    try:
        crop = service.update_crop(crop_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/sowing-date", response_model=CropInstanceResponse)
async def modify_sowing_date(
    crop_id: UUID,
    data: SowingDateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modify sowing date — triggers full replay from scratch.
    Note: seasonal_window_category is NOT recalculated (immutable at creation).
    """
    service = CropService(db)
    crop = service.modify_sowing_date(crop_id, current_user.id, data.new_sowing_date)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/activate", response_model=CropInstanceResponse)
async def activate_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition crop state to Active."""
    service = CropService(db)
    crop = service.change_state(crop_id, current_user.id, "Active")
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/harvest", response_model=CropInstanceResponse)
async def harvest_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition crop state to Harvested."""
    service = CropService(db)
    crop = service.change_state(crop_id, current_user.id, "Harvested")
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/close", response_model=CropInstanceResponse)
async def close_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition crop state to Closed."""
    service = CropService(db)
    crop = service.change_state(crop_id, current_user.id, "Closed")
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/archive", response_model=CropInstanceResponse)
async def archive_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark crop as archived."""
    service = CropService(db)
    crop = service.set_archived(crop_id, current_user.id, True)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.put("/{crop_id}/unarchive", response_model=CropInstanceResponse)
async def unarchive_crop(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unarchive crop."""
    service = CropService(db)
    crop = service.set_archived(crop_id, current_user.id, False)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    return CropInstanceResponse.model_validate(crop)


@router.get("/{crop_id}/replay/status")
async def get_replay_status(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get replay status metadata for a crop instance."""
    crop = _get_crop_for_user(db, crop_id, current_user)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    latest_snapshot = (
        db.query(CropInstanceSnapshot)
        .filter(
            CropInstanceSnapshot.crop_instance_id == crop_id,
            CropInstanceSnapshot.is_deleted == False,
        )
        .order_by(desc(CropInstanceSnapshot.created_at))
        .first()
    )
    snapshot_count = (
        db.query(CropInstanceSnapshot)
        .filter(
            CropInstanceSnapshot.crop_instance_id == crop_id,
            CropInstanceSnapshot.is_deleted == False,
        )
        .count()
    )
    total_actions = (
        db.query(ActionLog)
        .filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.is_deleted == False,
        )
        .count()
    )
    action_offset = latest_snapshot.action_count_at_snapshot if latest_snapshot else 0
    actions_since_last_snapshot = max(total_actions - action_offset, 0)

    candidate_failures = (
        db.query(EventLog)
        .filter(EventLog.event_type == "ReplayFailed")
        .order_by(desc(EventLog.created_at))
        .limit(100)
        .all()
    )
    latest_failure_event = next(
        (
            event
            for event in candidate_failures
            if (event.payload or {}).get("crop_instance_id") == str(crop_id)
        ),
        None,
    )
    recovery_reason = None
    if latest_failure_event and latest_failure_event.payload:
        recovery_reason = latest_failure_event.payload.get("error")

    status_value = "idle"
    if crop.state == "RecoveryRequired":
        status_value = "blocked"

    return {
        "crop_id": str(crop.id),
        "status": status_value,
        "last_replay_at": latest_snapshot.created_at if latest_snapshot else None,
        "last_replay_duration_seconds": None,
        "actions_replayed_since_last_snapshot": actions_since_last_snapshot,
        "recovery_required": crop.state == "RecoveryRequired",
        "recovery_reason": recovery_reason,
        "snapshot_count": snapshot_count,
        "latest_snapshot_id": str(latest_snapshot.id) if latest_snapshot else None,
    }


@router.get("/{crop_id}/replay/history")
async def get_replay_history(
    crop_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get replay-related event history for a crop instance."""
    crop = _get_crop_for_user(db, crop_id, current_user)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    replay_event_types = [
        "ReplayTriggered",
        "ReplayFailed",
        "RecoveryCleared",
    ]
    events = (
        db.query(EventLog)
        .filter(
            EventLog.entity_id == crop_id,
            EventLog.event_type.in_(replay_event_types),
        )
        .order_by(desc(EventLog.created_at))
        .limit(limit)
        .all()
    )

    history = []
    for event in events:
        payload = event.payload or {}
        history.append(
            {
                "event_id": str(event.id),
                "event_type": event.event_type,
                "status": event.status,
                "retry_count": event.retry_count,
                "failure_reason": event.failure_reason,
                "created_at": event.created_at,
                "processed_at": event.processed_at,
                "payload": payload,
            }
        )

    return {
        "crop_id": str(crop_id),
        "total": len(history),
        "history": history,
    }


@router.get("/{crop_id}/snapshots")
async def list_crop_snapshots(
    crop_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List snapshots for a crop instance."""
    crop = _get_crop_for_user(db, crop_id, current_user)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    query = db.query(CropInstanceSnapshot).filter(
        CropInstanceSnapshot.crop_instance_id == crop_id,
        CropInstanceSnapshot.is_deleted == False,
    )
    total = query.count()
    offset = (page - 1) * page_size
    snapshots = (
        query.order_by(desc(CropInstanceSnapshot.action_count_at_snapshot))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for snap in snapshots:
        snap_data = snap.snapshot_data or {}
        items.append(
            {
                "id": str(snap.id),
                "action_index": snap.action_count_at_snapshot,
                "snapshot_at": snap.created_at,
                "stress_score": snap_data.get("stress_score"),
                "risk_index": snap_data.get("risk_index"),
                "stage": snap_data.get("stage"),
                "state": crop.state,
                "chain_hash": snap_data.get("chain_hash"),
                "metadata": snap_data,
            }
        )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (offset + page_size) < total,
        "snapshots": items,
    }


@router.get("/{crop_id}/snapshots/{snapshot_id}")
async def get_crop_snapshot_detail(
    crop_id: UUID,
    snapshot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one snapshot for a crop instance."""
    crop = _get_crop_for_user(db, crop_id, current_user)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    snapshot = (
        db.query(CropInstanceSnapshot)
        .filter(
            CropInstanceSnapshot.id == snapshot_id,
            CropInstanceSnapshot.crop_instance_id == crop_id,
            CropInstanceSnapshot.is_deleted == False,
        )
        .first()
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "id": str(snapshot.id),
        "crop_id": str(crop_id),
        "action_index": snapshot.action_count_at_snapshot,
        "snapshot_at": snapshot.created_at,
        "snapshot_version": snapshot.snapshot_version,
        "snapshot_data": snapshot.snapshot_data or {},
    }


@router.patch("/{crop_id}/_admin/recovery/clear")
async def clear_recovery_required(
    crop_id: UUID,
    reason: str = Query(..., min_length=3, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin operation: clear RecoveryRequired lock for a crop."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")
    if crop.state != "RecoveryRequired":
        raise HTTPException(status_code=409, detail="Crop is not in RecoveryRequired state")

    crop.state = "Active"
    payload = {
        "crop_instance_id": str(crop_id),
        "cleared_by": str(current_user.id),
        "reason": reason,
    }
    hash_raw = f"RecoveryCleared:{crop_id}:{current_user.id}:{reason}"
    db.add(
        EventLog(
            event_type="RecoveryCleared",
            entity_type="crop_instance",
            entity_id=crop_id,
            partition_key=crop_id,
            payload=payload,
            module_target="ctis",
            event_hash=hashlib.sha256(hash_raw.encode()).hexdigest(),
        )
    )
    db.commit()
    return {"crop_id": str(crop_id), "status": "recovery_cleared"}


@router.patch("/{crop_id}/_admin/recovery/retry")
async def retry_replay_for_recovery(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin operation: clear recovery lock and re-run replay immediately."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    crop.state = "Active"
    payload = {
        "crop_instance_id": str(crop_id),
        "triggered_by": str(current_user.id),
        "source": "admin_retry",
    }
    hash_raw = f"ReplayTriggered:{crop_id}:{current_user.id}:{json.dumps(payload, sort_keys=True)}"
    db.add(
        EventLog(
            event_type="ReplayTriggered",
            entity_type="crop_instance",
            entity_id=crop_id,
            partition_key=crop_id,
            payload=payload,
            module_target="ctis",
            event_hash=hashlib.sha256(hash_raw.encode()).hexdigest(),
        )
    )
    db.commit()

    engine = ReplayEngine(db)
    try:
        await engine.replay_crop_instance(crop_id)
    except ReplayError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {"crop_id": str(crop_id), "status": "retry_completed"}
