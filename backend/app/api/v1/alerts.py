"""
Alerts API

GET /api/v1/alerts
PUT /api/v1/alerts/{alert_id}/acknowledge
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import (AlertResponse, BulkAcknowledgeRequest,
                               BulkAcknowledgeResponse)
from app.services.notifications import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(default=None),
    urgency_level: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    crop_instance_id: Optional[UUID] = Query(default=None),
    unacknowledged_only: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alerts for the current user."""
    service = AlertService(db)
    alerts = service.get_alerts(
        user_id=current_user.id,
        unacknowledged_only=unacknowledged_only,
        severity=severity,
        urgency_level=urgency_level,
        alert_type=alert_type,
        crop_instance_id=crop_instance_id,
        skip=skip,
        limit=limit,
    )
    return [AlertResponse.model_validate(a) for a in alerts]


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
            Alert.is_deleted == False,
        )
        .first()
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    service = AlertService(db)
    service.acknowledge_alert(alert_id)
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.post("/acknowledge-bulk", response_model=BulkAcknowledgeResponse)
async def acknowledge_alerts_bulk(
    payload: BulkAcknowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge a list of alerts owned by the current user."""
    service = AlertService(db)
    acknowledged_count = service.bulk_acknowledge(current_user.id, payload.alert_ids)
    db.commit()
    return BulkAcknowledgeResponse(acknowledged_count=acknowledged_count)
