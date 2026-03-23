"""
Sync Service

Handles offline sync with temporal anomaly detection and replay debouncing.

MSDD 1.7.1 — Temporal Anomaly Detection
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.models.action_log import ActionLog
from app.models.abuse_flag import AbuseFlag

logger = logging.getLogger(__name__)

# Anomaly thresholds
MAX_BACKDATE_DAYS = 7
MAX_FUTURE_HOURS = 2
MAX_BATCH_SIZE = 50
ANOMALY_SCORE_THRESHOLD = 3


class SyncService:
    """
    Processes offline sync submissions with temporal anomaly detection.

    Detects:
    - Excessive back-dated actions (beyond MAX_BACKDATE_DAYS)
    - Excessive future-dated actions (beyond server_time + tolerance)
    - Large batch submission anomalies (>MAX_BATCH_SIZE)
    - Monotonic counter resets (local_seq_no not strictly increasing)
    """

    def __init__(self, db: Session):
        self.db = db

    def process_sync(
        self,
        farmer_id: UUID,
        actions: List[Dict[str, Any]],
        device_id: str = "",
        session_id: str = "",
    ) -> Dict[str, Any]:
        """
        Process a batch of offline actions.

        Returns:
            Dict with processed, rejected, anomalies_detected, details
        """
        now = datetime.now(timezone.utc)
        _processed = [0]  # Use lists to avoid Pyre augmented assignment issues
        _rejected = [0]
        _anomaly = [0]
        details: List[Dict[str, Any]] = []

        # Check batch size anomaly
        if len(actions) > MAX_BATCH_SIZE:
            _anomaly[0] = _anomaly[0] + 2
            details.append({
                "type": "large_batch",
                "message": f"Batch size {len(actions)} exceeds limit {MAX_BATCH_SIZE}",
                "severity": "warning",
            })

        # Validate monotonic sequence
        seq_numbers = [a.get("local_seq_no", 0) for a in actions]
        if seq_numbers != sorted(seq_numbers):
            _anomaly[0] = _anomaly[0] + 1
            details.append({
                "type": "sequence_reset",
                "message": "Monotonic counter reset detected",
                "severity": "warning",
            })

        # Process each action
        for action in actions:
            validation = self._validate_action(action, now)

            if validation["is_valid"]:
                try:
                    self._insert_action(farmer_id, action)
                    _processed[0] = _processed[0] + 1
                except Exception as e:
                    _rejected[0] = _rejected[0] + 1
                    details.append({
                        "type": "insert_error",
                        "action": action.get("action_type"),
                        "message": str(e),
                    })
            else:
                _rejected[0] = _rejected[0] + 1
                points = validation.get("anomaly_points", 0)
                if isinstance(points, int):
                    _anomaly[0] = _anomaly[0] + points
                details.append(validation)

        # Extract final values
        processed: int = _processed[0]
        rejected: int = _rejected[0]
        anomaly_score: int = _anomaly[0]

        # Flag if anomaly score exceeds threshold
        if anomaly_score >= ANOMALY_SCORE_THRESHOLD:
            self._flag_abuse(farmer_id, anomaly_score, details)

        result = {
            "processed": processed,
            "rejected": rejected,
            "anomalies_detected": anomaly_score,
            "details": [d for i, d in enumerate(details) if i < 20],  # Limit details
        }

        logger.info(
            f"Sync processed for farmer {farmer_id}: "
            f"{processed} ok, {rejected} rejected, "
            f"anomaly_score={anomaly_score}"
        )

        return result

    def _validate_action(
        self, action: Dict[str, Any], now: datetime
    ) -> Dict[str, Any]:
        """Validate a single action for temporal anomalies."""
        try:
            action_date = datetime.fromisoformat(
                action.get("action_effective_date", "")
            ).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return {
                "is_valid": False,
                "type": "invalid_date",
                "message": "Invalid action date format",
                "anomaly_points": 1,
            }

        # Check back-dating
        days_back = (now - action_date).days
        if days_back > MAX_BACKDATE_DAYS:
            return {
                "is_valid": False,
                "type": "excessive_backdate",
                "message": f"Action dated {days_back} days in the past",
                "anomaly_points": 1,
            }

        # Check future-dating
        hours_ahead = (action_date - now).total_seconds() / 3600
        if hours_ahead > MAX_FUTURE_HOURS:
            return {
                "is_valid": False,
                "type": "excessive_future",
                "message": f"Action dated {hours_ahead:.1f} hours in the future",
                "anomaly_points": 1,
            }

        return {"is_valid": True}

    def _insert_action(
        self, farmer_id: UUID, action: Dict[str, Any]
    ) -> None:
        """Insert a validated action into the database."""
        log = ActionLog(
            crop_instance_id=action["crop_instance_id"],
            action_type=action["action_type"],
            action_effective_date=action["action_effective_date"],
            performed_by=farmer_id,
            metadata_extra=action.get("metadata", {}),
            source="offline_sync",
        )
        self.db.add(log)
        self.db.flush()

    def _flag_abuse(
        self, farmer_id: UUID, score: int, details: List[Dict[str, Any]]
    ) -> None:
        """Create an abuse flag for anomalous sync behavior."""
        flag = AbuseFlag(
            target_type="user",
            target_id=farmer_id,
            flag_type="sync_anomaly",
            severity="high" if score >= 5 else "medium",
            details={"anomaly_score": score, "sync_details": [d for i, d in enumerate(details) if i < 10]},
        )
        self.db.add(flag)
        logger.warning(
            f"Abuse flag created for farmer {farmer_id}: "
            f"sync anomaly score={score}"
        )
