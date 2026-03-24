"""
Replay Engine v2 — Deterministic Crop Instance Replay

The core CTIS algorithm. Recomputes a crop instance's entire state
from its ordered action logs, with incremental snapshot support.

Hardening:
  - Orphan action handling (Patch 1.7)
  - Baseline tracking (MSDD 1.3.1)
  - Event chain hash (TDD 2.3.1)
  - Replay timeout protection (CTIS Enh 8)

TDD Section 4.4 | MSDD 1.18 (Failure Recovery)
"""

import asyncio
import hashlib
import json
from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import asc  # type: ignore
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
import logging

from app.models.crop_instance import CropInstance  # type: ignore
from app.models.action_log import ActionLog  # type: ignore
from app.models.snapshot import CropInstanceSnapshot  # type: ignore
from app.models.deviation import DeviationProfile  # type: ignore
from app.models.event_log import EventLog  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SNAPSHOT_INTERVAL = 10  # Create a snapshot every N applied actions
STRESS_DECAY_FACTOR = 0.95  # Per-action stress decay (EMA smoothing)
MAX_STRESS = 100.0
REPLAY_TIMEOUT_SECONDS = 120  # Max time for a single replay (CTIS Enh 8)
MAX_RISK = 1.0

# Stage definitions mapped from rule templates (simplified for v1)
DEFAULT_STAGE_TIMELINE = {
    "germination": (0, 14),
    "vegetative": (15, 45),
    "flowering": (46, 75),
    "maturity": (76, 105),
    "harvest": (106, 120),
}

# Action type → base stress impact
STRESS_IMPACT = {
    "irrigation": -5.0,       # Reduces stress
    "fertilizer": -3.0,       # Reduces stress
    "pesticide": -4.0,        # Reduces stress
    "weeding": -2.0,          # Reduces stress
    "observation": 0.0,       # Neutral
    "media_upload": 0.0,      # Neutral
    "harvest": 0.0,           # Terminal action
}


class ReplayError(Exception):
    """Raised when the replay engine encounters an unrecoverable error."""
    pass


class ReplayEngine:
    """
    Deterministic Replay Engine v1.

    Given a crop_instance_id, replays all action logs in chronological order,
    recomputing stress, risk, stage, and deviation state from scratch
    (or from the last available snapshot).
    """

    def __init__(self, db: Session):
        self.db = db

    async def replay_crop_instance(
        self,
        crop_instance_id: UUID,
        timeout_seconds: float = REPLAY_TIMEOUT_SECONDS,
    ) -> CropInstance:
        """
        Full replay pipeline with timeout protection (CTIS Enh 8):

        1. Acquire row lock (SELECT FOR UPDATE) to prevent concurrent replay
        2. Load latest snapshot (if exists)
        3. Load ordered action_logs (after snapshot point)
        4. For each action: validate → skip orphans → apply → baseline → chain hash
        5. Update crop_instance row
        6. Create snapshot if threshold met
        7. Commit transaction

        On failure:
          - Revert to last stable snapshot (MSDD 1.18)
          - Lock crop_instance, set state = 'RecoveryRequired'
          - Log error, notify admin
          - Prevent further action logging until resolved
        """
        try:
            return await asyncio.wait_for(
                self._do_replay(crop_instance_id),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Replay TIMEOUT for crop {crop_instance_id} "
                f"(exceeded {timeout_seconds}s)"
            )
            raise ReplayError(
                f"Replay timed out after {timeout_seconds}s for crop {crop_instance_id}"
            )

    async def _do_replay(self, crop_instance_id: UUID) -> CropInstance:
        """Internal replay implementation (wrapped by timeout)."""

        logger.info(f"Starting replay for crop_instance_id={crop_instance_id}")

        # 1. Acquire row lock
        crop = (
            self.db.query(CropInstance)
            .filter(
                CropInstance.id == crop_instance_id,
                CropInstance.is_deleted == False,
            )
            .with_for_update()
            .first()
        )

        if not crop:
            raise ReplayError(f"CropInstance {crop_instance_id} not found")

        if crop.state == "RecoveryRequired":
            raise ReplayError(
                f"CropInstance {crop_instance_id} is in RecoveryRequired state. "
                "Admin must resolve before replay can proceed."
            )

        try:
            # 2. Load latest snapshot
            snapshot = self._load_latest_snapshot(crop_instance_id)

            # Initialize state from snapshot or defaults
            state = self._initialize_state(crop, snapshot)

            # 3. Load ordered action logs (after snapshot point)
            actions = self._load_actions(crop_instance_id, state["action_offset"])

            if not actions:
                logger.info("No new actions to replay.")
                self.db.commit()
                return crop

            # 4. Apply each action sequentially (with orphan detection)
            applied_count = 0
            orphaned_count = 0
            for action in actions:
                # Orphan detection (Patch 1.7): skip actions before sowing date
                if self._is_orphaned_action(crop, action):
                    action.is_orphaned = True
                    action.applied_in_replay = "skipped"
                    orphaned_count += 1
                    continue

                self._apply_action(crop, action, state)
                action.applied_in_replay = "applied"
                applied_count += 1

                # Baseline tracking (MSDD 1.3.1)
                self._update_baseline(crop, action, state)

                # Event chain hash (TDD 2.3.1)
                self._update_chain_hash(crop, action, state)

            if orphaned_count > 0:
                logger.info(f"Orphaned {orphaned_count} actions before sowing date")

            # 5. Write computed state back to crop_instance
            self._write_state_to_crop(crop, state)

            # 6. Create snapshot if threshold met
            total_actions = state["action_offset"] + applied_count
            if total_actions % SNAPSHOT_INTERVAL == 0 and applied_count > 0:
                self._create_snapshot(crop, state, total_actions)

            # Load deviation profile and update
            self._update_deviation_profile(crop, state)

            # 7. Commit
            self.db.commit()
            self.db.refresh(crop)

            logger.info(
                f"Replay complete for crop {crop_instance_id}: "
                f"applied={applied_count}, stress={crop.stress_score:.2f}, "
                f"risk={crop.risk_index:.2f}, state={crop.state}"
            )
            return crop

        except ReplayError:
            raise
        except Exception as e:
            logger.error(f"Replay failed for crop {crop_instance_id}: {e}")
            self._handle_failure(crop, snapshot, str(e))
            raise ReplayError(f"Replay failed: {e}") from e

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _load_latest_snapshot(
        self, crop_instance_id: UUID
    ) -> Optional[CropInstanceSnapshot]:
        """Load the most recent snapshot for incremental replay."""
        return (
            self.db.query(CropInstanceSnapshot)
            .filter(CropInstanceSnapshot.crop_instance_id == crop_instance_id)
            .order_by(CropInstanceSnapshot.created_at.desc())
            .first()
        )

    def _initialize_state(
        self, crop: CropInstance, snapshot: Optional[CropInstanceSnapshot]
    ) -> dict:
        """
        Initialize the replay state from a snapshot or crop defaults.
        Returns a mutable dict that accumulates state during replay.
        """
        if snapshot and snapshot.snapshot_data:
            data = snapshot.snapshot_data
            return {
                "stress_score": data.get("stress_score", 0.0),
                "risk_index": data.get("risk_index", 0.0),
                "current_day_number": data.get("current_day_number", 0),
                "stage": data.get("stage"),
                "stage_offset_days": data.get("stage_offset_days", 0),
                "action_offset": snapshot.action_count_at_snapshot,
                "consecutive_deviations": data.get("consecutive_deviations", 0),
                "deviation_trend_slope": data.get("deviation_trend_slope", 0.0),
                "cumulative_deviation_days": data.get("cumulative_deviation_days", 0),
            }

        # Fresh replay from scratch
        return {
            "stress_score": 0.0,
            "risk_index": 0.0,
            "current_day_number": 0,
            "stage": None,
            "stage_offset_days": 0,
            "action_offset": 0,
            "consecutive_deviations": 0,
            "deviation_trend_slope": 0.0,
            "cumulative_deviation_days": 0,
            # Baseline tracking (MSDD 1.3.1)
            "baseline_day_number": 0,
            "baseline_growth_stage": None,
            # Chain hash (TDD 2.3.1)
            "chain_hash": None,
        }

    def _load_actions(self, crop_instance_id: UUID, offset: int) -> list[ActionLog]:
        """Load action logs after the snapshot offset, ordered chronologically."""
        query = (
            self.db.query(ActionLog)
            .filter(
                ActionLog.crop_instance_id == crop_instance_id,
                ActionLog.is_deleted == False,
            )
            .order_by(
                asc(ActionLog.effective_date),
                asc(ActionLog.server_timestamp),
            )
        )

        if offset > 0:
            query = query.offset(offset)

        return query.all()

    def _apply_action(self, crop: CropInstance, action: ActionLog, state: dict):
        """
        Apply a single action to the running state.
        Updates stress, risk, day number, stage, and drift.
        """

        # Calculate day number from sowing date
        if crop.sowing_date and action.effective_date:
            day_number = (action.effective_date - crop.sowing_date).days
            state["current_day_number"] = max(state["current_day_number"], day_number)

        # Determine expected stage from day number
        expected_stage = self._compute_stage(state["current_day_number"])
        if expected_stage and expected_stage != state["stage"]:
            state["stage"] = expected_stage

        # Update stress score (EMA with action impact)
        impact = STRESS_IMPACT.get(action.action_type, 0.0)

        # Category multiplier: Timeline-Critical actions have stronger effect
        category_multiplier = 1.0
        if action.category == "Timeline-Critical":
            category_multiplier = 1.5
        elif action.category == "Informational":
            category_multiplier = 0.5

        # Apply stress: decay existing + add impact
        new_stress = (state["stress_score"] * STRESS_DECAY_FACTOR) + (
            impact * category_multiplier
        )
        state["stress_score"] = max(0.0, min(new_stress, MAX_STRESS))

        # Compute risk index from stress (normalized to 0-1)
        state["risk_index"] = min(state["stress_score"] / MAX_STRESS, MAX_RISK)

        # Drift enforcement: check if action is within expected timeline
        self._enforce_drift(crop, action, state)

    def _compute_stage(self, day_number: int) -> Optional[str]:
        """Determine the expected crop stage from the day number."""
        for stage_name, (start, end) in DEFAULT_STAGE_TIMELINE.items():
            if start <= day_number <= end:
                return stage_name
        if day_number > 120:
            return "harvest"
        return None

    def _enforce_drift(self, crop: CropInstance, action: ActionLog, state: dict):
        """
        Enforce drift limits (MSDD 1.9).
        Tracks deviation from expected timeline.
        """
        if not crop.sowing_date or not action.effective_date:
            return

        day_number = (action.effective_date - crop.sowing_date).days
        expected_stage = self._compute_stage(day_number)

        if expected_stage and state["stage"] and expected_stage != state["stage"]:
            # There's a deviation between where we should be and where we are
            state["consecutive_deviations"] += 1
            state["cumulative_deviation_days"] += 1

            # Update trend slope (simple moving estimate)
            state["deviation_trend_slope"] = (
                state["consecutive_deviations"] / max(day_number, 1)
            )

            # Compute stage offset
            expected_stages = list(DEFAULT_STAGE_TIMELINE.keys())
            if expected_stage in expected_stages and state["stage"] in expected_stages:
                expected_idx = expected_stages.index(expected_stage)
                current_idx = expected_stages.index(state["stage"])
                state["stage_offset_days"] = (current_idx - expected_idx) * 15

            # If drift exceeds max allowed, increase stress penalty
            if abs(state["stage_offset_days"]) > (crop.max_allowed_drift or 7):
                state["stress_score"] = min(
                    state["stress_score"] + 10.0, MAX_STRESS
                )
        else:
            # Action is on-track, reset consecutive deviation counter
            state["consecutive_deviations"] = 0

    def _is_orphaned_action(self, crop: CropInstance, action: ActionLog) -> bool:
        """
        Orphan action detection (Patch 1.7).
        An action is orphaned if its effective_date is before the sowing date.
        """
        if not crop.sowing_date or not action.effective_date:
            return False
        return action.effective_date < crop.sowing_date

    def _update_baseline(self, crop: CropInstance, action: ActionLog, state: dict):
        """
        Baseline tracking (MSDD 1.3.1).
        Maintains expected (baseline) day number and growth stage
        independently from actuals, for progress comparison.
        """
        if not crop.sowing_date or not action.effective_date:
            return

        # Baseline progresses linearly from sowing date
        baseline_day = (action.effective_date - crop.sowing_date).days
        state["baseline_day_number"] = max(state["baseline_day_number"], baseline_day)
        state["baseline_growth_stage"] = self._compute_stage(baseline_day)

    def _update_chain_hash(self, crop: CropInstance, action: ActionLog, state: dict):
        """
        Event chain hash computation (TDD 2.3.1).
        Creates a tamper-detection chain: hash(prev_hash + action_data).
        """
        prev_hash = state.get("chain_hash") or ""
        action_data = f"{action.id}:{action.action_type}:{action.effective_date}:{action.server_timestamp}"
        raw = f"{prev_hash}:{action_data}"
        new_hash = hashlib.sha256(raw.encode()).hexdigest()
        state["chain_hash"] = new_hash

    def _write_state_to_crop(self, crop: CropInstance, state: dict):
        """Write the computed replay state back to the crop instance."""
        crop.stress_score = round(state["stress_score"], 4)
        crop.risk_index = round(state["risk_index"], 4)
        crop.current_day_number = state["current_day_number"]
        crop.stage = state["stage"]
        crop.stage_offset_days = state["stage_offset_days"]

        # Baseline tracking (MSDD 1.3.1)
        crop.baseline_day_number = state.get("baseline_day_number", 0)
        crop.baseline_growth_stage = state.get("baseline_growth_stage")

        # Chain hash (TDD 2.3.1)
        crop.event_chain_hash = state.get("chain_hash")

        # Auto-transition state based on risk
        if crop.state == "Created":
            crop.state = "Active"

        if crop.state in ("Active", "Delayed"):
            if state["risk_index"] >= 0.7:
                crop.state = "AtRisk"
            elif state["stage_offset_days"] > (crop.max_allowed_drift or 7):
                crop.state = "Delayed"

        if crop.state == "AtRisk" and state["risk_index"] < 0.5:
            crop.state = "Active"

    def _create_snapshot(
        self, crop: CropInstance, state: dict, action_count: int
    ):
        """Create a replay checkpoint snapshot."""
        snapshot = CropInstanceSnapshot(
            crop_instance_id=crop.id,
            snapshot_data={
                "stress_score": state["stress_score"],
                "risk_index": state["risk_index"],
                "current_day_number": state["current_day_number"],
                "stage": state["stage"],
                "stage_offset_days": state["stage_offset_days"],
                "consecutive_deviations": state["consecutive_deviations"],
                "deviation_trend_slope": state["deviation_trend_slope"],
                "cumulative_deviation_days": state["cumulative_deviation_days"],
            },
            action_count_at_snapshot=action_count,
            snapshot_version=1,
        )
        self.db.add(snapshot)
        logger.info(f"Snapshot created at action_count={action_count}")

    def _update_deviation_profile(self, crop: CropInstance, state: dict):
        """Sync the deviation profile with computed replay state."""
        deviation = (
            self.db.query(DeviationProfile)
            .filter(DeviationProfile.crop_instance_id == crop.id)
            .first()
        )

        if deviation:
            deviation.consecutive_deviation_count = state["consecutive_deviations"]
            deviation.deviation_trend_slope = round(
                state["deviation_trend_slope"], 4
            )
            deviation.cumulative_deviation_days = state["cumulative_deviation_days"]
            deviation.recurring_pattern_flag = state["consecutive_deviations"] >= 3

    def _handle_failure(
        self,
        crop: CropInstance,
        snapshot: Optional[CropInstanceSnapshot],
        error_msg: str,
    ):
        """
        Failure recovery (MSDD 1.18):
        1. Revert to last stable snapshot
        2. Lock crop instance to 'RecoveryRequired'
        3. Log error for admin review
        """
        self.db.rollback()

        try:
            # Re-acquire the crop (transaction was rolled back)
            crop = (
                self.db.query(CropInstance)
                .filter(CropInstance.id == crop.id)
                .first()
            )
            if not crop:
                return

            # Revert to snapshot if available
            if snapshot and snapshot.snapshot_data:
                data = snapshot.snapshot_data
                crop.stress_score = data.get("stress_score", 0.0)
                crop.risk_index = data.get("risk_index", 0.0)
                crop.current_day_number = data.get("current_day_number", 0)
                crop.stage = data.get("stage")
                crop.stage_offset_days = data.get("stage_offset_days", 0)

            # Lock the crop instance
            crop.state = "RecoveryRequired"

            # Log the failure for admin review
            error_log = EventLog(
                event_type="ReplayFailed",
                source="ReplayEngine",
                payload={
                    "crop_instance_id": str(crop.id),
                    "error": error_msg,
                    "reverted_to_snapshot": snapshot.id if snapshot else None,
                },
            )
            self.db.add(error_log)
            self.db.commit()

            logger.error(
                f"Crop {crop.id} set to RecoveryRequired after replay failure"
            )

        except Exception as recovery_error:
            logger.critical(
                f"Recovery itself failed for crop {crop.id}: {recovery_error}"
            )
            self.db.rollback()
