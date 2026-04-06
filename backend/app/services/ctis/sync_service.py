"""
Sync Service

Handles offline sync with temporal anomaly detection, schema-aligned
ActionLog insertion, idempotency, and replay event emission.

MSDD 1.7.1 — Temporal Anomaly Detection
Audit 15 — Full rewrite for schema alignment & ActionService integration.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.abuse_flag import AbuseFlag
from app.models.action_log import ActionLog
from app.models.crop_instance import CropInstance

logger = logging.getLogger(__name__)

# Anomaly thresholds
MAX_BACKDATE_DAYS = 7
MAX_FUTURE_HOURS = 2
MAX_BATCH_SIZE = 500
ANOMALY_SCORE_THRESHOLD = 3

# Allowed action types for offline submission
ALLOWED_ACTION_TYPES = {
    "irrigation",
    "fertilizer",
    "pesticide",
    "fungicide",
    "herbicide",
    "pruning",
    "thinning",
    "transplanting",
    "harvesting",
    "monitoring",
    "soil_amendment",
    "disease_management",
    "pest_management",
    "weeding",
    "mulching",
    "staking",
    "defoliation",
    "seed_treatment",
    "observation",
}

# Category mapping for action types
CATEGORY_MAP = {
    "irrigation": "irrigation",
    "fertilizer": "soil_management",
    "pesticide": "pest_disease_management",
    "fungicide": "pest_disease_management",
    "herbicide": "pest_disease_management",
    "pruning": "crop_management",
    "thinning": "crop_management",
    "transplanting": "crop_management",
    "harvesting": "harvesting",
    "monitoring": "monitoring",
    "observation": "monitoring",
    "soil_amendment": "soil_management",
    "disease_management": "pest_disease_management",
    "pest_management": "pest_disease_management",
    "weeding": "pest_disease_management",
    "mulching": "soil_management",
    "staking": "crop_management",
    "defoliation": "crop_management",
    "seed_treatment": "crop_management",
}


class SyncService:
    """
    Processes offline sync submissions with temporal anomaly detection.

    Detects:
    - Excessive back-dated actions (beyond MAX_BACKDATE_DAYS)
    - Excessive future-dated actions (beyond server_time + tolerance)
    - Large batch submission anomalies (>MAX_BATCH_SIZE)
    - Monotonic counter resets (local_seq_no not strictly increasing)
    - Invalid action types not in whitelist
    - Crop ownership violations
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
            Dict with synced, failed, warnings, duplicates and per-action details.
        """
        now = datetime.now(timezone.utc)

        synced_actions: List[Dict[str, Any]] = []
        failed_actions: List[Dict[str, Any]] = []
        duplicate_actions: List[Dict[str, Any]] = []
        anomalies: List[Dict[str, Any]] = []

        # ── 1. Validate batch size ──
        if len(actions) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch too large: {len(actions)} (max {MAX_BATCH_SIZE})")

        if len(actions) == 0:
            raise ValueError("Empty batch")

        # ── 2. Prefetch farmer's crops for ownership check ──
        farmer_crops: Dict[str, CropInstance] = {}
        for crop in (
            self.db.query(CropInstance)
            .filter(
                CropInstance.farmer_id == farmer_id,
                CropInstance.is_deleted == False,
            )
            .all()
        ):
            farmer_crops[str(crop.id)] = crop

        # ── 3. Validate sequence monotonicity (batch-level) ──
        seq_numbers = [a.get("local_seq_no", 0) for a in actions]
        if seq_numbers != sorted(seq_numbers):
            anomalies.append(
                {
                    "action_index": -1,
                    "local_seq_no": -1,
                    "reason": "non-monotonic sequence (batch level)",
                    "severity": "warning",
                }
            )

        # ── 4. Process each action ──
        last_seq: Optional[int] = None

        for idx, action in enumerate(actions):
            local_seq = action.get("local_seq_no")
            crop_id = str(action.get("crop_instance_id", ""))
            action_type_raw = action.get("action_type", "")

            try:
                # 4a. Validate action_type
                action_type = action_type_raw.lower().strip()
                if action_type not in ALLOWED_ACTION_TYPES:
                    raise ValueError(
                        f"Invalid action_type '{action_type_raw}'. "
                        f"Allowed: {', '.join(sorted(ALLOWED_ACTION_TYPES))}"
                    )

                # 4b. Validate local_seq_no
                if local_seq is None:
                    raise ValueError("local_seq_no is required")

                # 4c. Per-action monotonicity check
                if last_seq is not None and local_seq <= last_seq:
                    anomalies.append(
                        {
                            "action_index": idx,
                            "local_seq_no": local_seq,
                            "reason": "non-monotonic sequence",
                            "severity": "high",
                        }
                    )
                last_seq = local_seq

                # 4d. Validate crop ownership
                if crop_id not in farmer_crops:
                    raise ValueError(f"Crop {crop_id[:8]}… not owned by farmer")

                crop = farmer_crops[crop_id]
                if crop.state in ("CLOSED", "ARCHIVED"):
                    raise ValueError(
                        f"Crop {crop_id[:8]}… is {crop.state} — cannot log actions"
                    )

                # 4e. Parse and validate effective date
                action_date_str = action.get("action_effective_date", "")
                if not action_date_str:
                    raise ValueError("action_effective_date is required")

                action_date = self._parse_date(action_date_str)

                # 4f. Backdate check (≤7 days)
                backdate_days = (now.date() - action_date.date()).days
                if backdate_days > MAX_BACKDATE_DAYS:
                    anomalies.append(
                        {
                            "action_index": idx,
                            "local_seq_no": local_seq,
                            "reason": f"backdate: {backdate_days} days",
                            "severity": "medium",
                        }
                    )

                # 4g. Future-date check (≤2 hours)
                future_seconds = (action_date - now).total_seconds()
                if future_seconds > MAX_FUTURE_HOURS * 3600:
                    future_h = future_seconds / 3600
                    anomalies.append(
                        {
                            "action_index": idx,
                            "local_seq_no": local_seq,
                            "reason": f"future date: {future_h:.1f} hours",
                            "severity": "medium",
                        }
                    )

                # 4h. Insert action via corrected method
                action_log, is_duplicate = self._insert_action(
                    crop_id=crop_id,
                    farmer_id=farmer_id,
                    action_type=action_type,
                    action_date=action_date,
                    metadata=action.get("metadata") or {},
                    local_seq_no=local_seq,
                    device_id=device_id,
                    session_id=session_id,
                    notes=action.get("notes"),
                )

                if is_duplicate:
                    duplicate_actions.append(
                        {
                            "action_index": idx,
                            "action_id": str(action_log.id),
                            "reason": "duplicate_detected",
                            "original_sync_time": (
                                action_log.created_at.isoformat()
                                if action_log.created_at
                                else now.isoformat()
                            ),
                        }
                    )
                else:
                    synced_actions.append(
                        {
                            "action_id": str(action_log.id),
                            "crop_id": crop_id,
                            "action_type": action_type,
                            "action_effective_date": action_date.isoformat(),
                            "local_seq_no": local_seq,
                            "status": "synced",
                        }
                    )

                logger.info(
                    f"  Action {idx + 1}/{len(actions)} "
                    f"{'dup' if is_duplicate else 'synced'}: "
                    f"{action_type} on {action_date.date()}"
                )

            except ValueError as e:
                logger.warning(f"  Action {idx + 1} validation error: {e}")
                failed_actions.append(
                    {
                        "action_index": idx,
                        "local_seq_no": local_seq or 0,
                        "crop_id": crop_id or None,
                        "action_type": action_type_raw or None,
                        "error": str(e),
                        "status": "failed",
                    }
                )

            except Exception as e:
                logger.error(f"  Action {idx + 1} system error: {e}", exc_info=True)
                failed_actions.append(
                    {
                        "action_index": idx,
                        "local_seq_no": local_seq or 0,
                        "crop_id": crop_id or None,
                        "action_type": action_type_raw or None,
                        "error": f"System error: {str(e)[:100]}",
                        "status": "error",
                    }
                )

        # ── 5. Create AbuseFlag if anomaly score ≥ threshold ──
        anomaly_score = len(anomalies)
        if anomaly_score >= ANOMALY_SCORE_THRESHOLD:
            self._flag_abuse(
                farmer_id=farmer_id,
                score=anomaly_score,
                anomalies=anomalies,
                device_id=device_id,
                session_id=session_id,
                failed_count=len(failed_actions),
            )

        logger.info(
            f"Sync complete for farmer {farmer_id}: "
            f"{len(synced_actions)} synced, {len(failed_actions)} failed, "
            f"{len(duplicate_actions)} dups, {anomaly_score} anomalies"
        )

        return {
            "synced": len(synced_actions),
            "failed": len(failed_actions),
            "warnings": anomaly_score,
            "duplicates": len(duplicate_actions),
            "synced_actions": synced_actions,
            "failed_actions": failed_actions,
            "duplicate_actions": duplicate_actions,
            "anomalies": anomalies,
            "device_id": device_id,
            "session_id": session_id,
            "sync_timestamp": now.isoformat(),
        }

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse ISO date string, converting to UTC."""
        try:
            dt = datetime.fromisoformat(date_str)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid date format: {exc}") from exc

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    def _insert_action(
        self,
        crop_id: str,
        farmer_id: UUID,
        action_type: str,
        action_date: datetime,
        metadata: dict,
        local_seq_no: int,
        device_id: str,
        session_id: str,
        notes: Optional[str] = None,
    ) -> tuple:
        """
        Insert offline action into ActionLog with correct schema.

        Returns (ActionLog, is_duplicate).
        """
        # 1. Build idempotency key
        idempotency_key = f"offline_{device_id}_{session_id}_{local_seq_no}"

        # 2. Check for duplicates
        existing = (
            self.db.query(ActionLog)
            .filter(
                ActionLog.idempotency_key == idempotency_key,
                ActionLog.is_deleted == False,
            )
            .first()
        )

        if existing:
            logger.info(f"Duplicate action detected: {idempotency_key}")
            return existing, True

        # 3. Derive category from action_type
        category = CATEGORY_MAP.get(action_type, "Operational")

        # 4. Create ActionLog with **correct** column names
        action_log = ActionLog(
            id=uuid4(),
            crop_instance_id=UUID(crop_id),
            action_type=action_type,
            category=category,
            effective_date=(
                action_date.date() if isinstance(action_date, datetime) else action_date
            ),
            metadata_json=metadata,
            notes=notes,
            source="offline",
            idempotency_key=idempotency_key,
            local_seq_no=local_seq_no,
            device_timestamp=action_date,
            server_timestamp=datetime.now(timezone.utc),
        )

        self.db.add(action_log)
        self.db.flush()

        logger.info(f"Action created: {action_log.id} (offline, seq={local_seq_no})")
        return action_log, False

    def _flag_abuse(
        self,
        farmer_id: UUID,
        score: int,
        anomalies: List[Dict[str, Any]],
        device_id: str,
        session_id: str,
        failed_count: int,
    ) -> None:
        """Create an abuse flag for anomalous sync behaviour."""
        flag = AbuseFlag(
            farmer_id=farmer_id,
            flag_type="offline_sync_anomalies",
            severity="high" if score >= 5 else "medium",
            anomaly_score=float(score),
            details={
                "anomaly_count": score,
                "anomalies": anomalies[:10],
                "device_id": device_id,
                "session_id": session_id,
                "failed_count": failed_count,
                "sync_timestamp": datetime.now(timezone.utc).isoformat(),
            },
            status="open",
        )
        self.db.add(flag)
        logger.warning(
            f"AbuseFlag created for farmer {farmer_id}: " f"sync anomaly score={score}"
        )
