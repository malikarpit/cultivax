"""
Alerts API

GET /api/v1/alerts
PUT /api/v1/alerts/{alert_id}/acknowledge
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertAcknowledge

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    unacknowledged_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alerts for the current user."""
    query = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_deleted == False,
    )
    if unacknowledged_only:
        query = query.filter(Alert.is_acknowledged == False)

    alerts = query.order_by(Alert.created_at.desc()).limit(50).all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    from datetime import datetime, timezone

    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
        Alert.is_deleted == False,
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)
