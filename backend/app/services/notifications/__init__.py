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
        details: Optional[dict] = None,
    ) -> Optional[Alert]:
        """Generate an alert with throttle check."""
        if not self._can_send_alert(crop_instance_id, alert_type):
            logger.info(
                f"Alert throttled for crop {crop_instance_id}: {alert_type}"
            )
            return None

        alert = Alert(
            crop_instance_id=crop_instance_id,
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
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
        self, user_id: UUID, unacknowledged_only: bool = True
    ) -> List[Alert]:
        """Get alerts for a user."""
        query = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_deleted == False,
        )
        if unacknowledged_only:
            query = query.filter(Alert.is_acknowledged == False)
        return query.order_by(Alert.created_at.desc()).limit(50).all()

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
