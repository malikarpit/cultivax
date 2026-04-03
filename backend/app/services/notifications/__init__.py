"""
Alert Service

Generates alerts from system events with throttling.
Max 3 alerts per crop per 24h (configurable per alert type).

MSDD Enhancement Sec 14
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

from app.models.alert import Alert

logger = logging.getLogger(__name__)

# Alert throttling: max alerts per crop per 24 hours
MAX_ALERTS_PER_CROP = 3
THROTTLE_WINDOW_HOURS = 24

# Alert type definitions
ALERT_TYPES = [
    "weather_alert",
    "stress_alert",
    "risk_alert",
    "pest_alert",
    "action_reminder",
    "market_alert",
    "harvest_approaching",
]


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def generate_alert(
        self,
        crop_instance_id: UUID,
        user_id: UUID,
        alert_type: str,
        severity: str,
        message: str,
        urgency_level: str = "Medium",
        details: Optional[dict] = None,
        source_event_id: Optional[UUID] = None,
        expires_in_hours: Optional[int] = 24,
    ) -> Optional[Alert]:
        """Generate an alert with throttle check."""
        if not self._can_send_alert(crop_instance_id, alert_type):
            logger.info(
                f"Alert throttled for crop {crop_instance_id}: {alert_type}"
            )
            return None

        expires_at = None
        if expires_in_hours is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        alert = Alert(
            crop_instance_id=crop_instance_id,
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            urgency_level=urgency_level,
            message=message,
            details=details or {},
            source_event_id=source_event_id,
            expires_at=expires_at,
        )
        self.db.add(alert)
        self.db.flush()

        logger.info(f"Alert generated: {alert_type} for crop {crop_instance_id}")
        return alert

    def acknowledge_alert(self, alert_id: UUID) -> Optional[Alert]:
        """Mark an alert as acknowledged."""
        alert = self.db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.is_deleted == False,
        ).first()
        if alert:
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.now(timezone.utc)
        return alert

    def get_alerts(
        self,
        user_id: UUID,
        unacknowledged_only: bool = True,
        severity: Optional[str] = None,
        urgency_level: Optional[str] = None,
        alert_type: Optional[str] = None,
        crop_instance_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Alert]:
        """Get alerts for a user."""
        query = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_deleted == False,
        )
        if unacknowledged_only:
            query = query.filter(Alert.is_acknowledged == False)

        if severity:
            query = query.filter(Alert.severity == severity)
        if urgency_level:
            query = query.filter(Alert.urgency_level == urgency_level)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if crop_instance_id:
            query = query.filter(Alert.crop_instance_id == crop_instance_id)

        skip = max(skip, 0)
        limit = min(max(limit, 1), 100)

        return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    def bulk_acknowledge(self, user_id: UUID, alert_ids: list[UUID]) -> int:
        """Bulk acknowledge alerts owned by the user."""
        if not alert_ids:
            return 0

        now = datetime.now(timezone.utc)
        alerts = self.db.query(Alert).filter(
            Alert.id.in_(alert_ids),
            Alert.user_id == user_id,
            Alert.is_deleted == False,
            Alert.is_acknowledged == False,
        ).all()

        for alert in alerts:
            alert.is_acknowledged = True
            alert.acknowledged_at = now

        return len(alerts)

    def cleanup_expired_alerts(self) -> int:
        """Soft-delete alerts that are expired or stale acknowledged."""
        now = datetime.now(timezone.utc)
        stale_ack_threshold = now - timedelta(days=30)

        expired = self.db.query(Alert).filter(
            Alert.is_deleted == False,
            Alert.expires_at.isnot(None),
            Alert.expires_at < now,
        ).all()

        stale_ack = self.db.query(Alert).filter(
            Alert.is_deleted == False,
            Alert.is_acknowledged == True,
            Alert.acknowledged_at.isnot(None),
            Alert.acknowledged_at < stale_ack_threshold,
        ).all()

        for alert in [*expired, *stale_ack]:
            alert.is_deleted = True
            alert.deleted_at = now

        return len(expired) + len(stale_ack)

    def _can_send_alert(
        self, crop_instance_id: UUID, alert_type: str
    ) -> bool:
        """Check throttle: max alerts per crop per window."""
        window_start = datetime.now(timezone.utc) - timedelta(
            hours=THROTTLE_WINDOW_HOURS
        )
        count = self.db.query(Alert).filter(
            Alert.crop_instance_id == crop_instance_id,
            Alert.created_at >= window_start,
            Alert.is_deleted == False,
        ).count()
        return count < MAX_ALERTS_PER_CROP
