"""
Snapshot Manager — Create and Load Crop Instance Snapshots

Manages deterministic checkpoint creation for the Replay Engine.
Snapshots are taken every N actions to speed up replay recovery.

MSDD 1.8.2 | TDD 2.3.3
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json
import logging

from app.models.snapshot import CropInstanceSnapshot
from app.models.crop_instance import CropInstance
from app.models.action_log import ActionLog

logger = logging.getLogger(__name__)

# Snapshot threshold — create a snapshot every N actions
SNAPSHOT_INTERVAL = 10


class SnapshotManager:
    """
    Manages crop instance snapshots for efficient replay.

    Snapshots capture the full computed state at a point in time,
    allowing the Replay Engine to skip replaying all actions from
    the beginning. Instead, it resumes from the latest snapshot.
    """

    def __init__(self, db: Session):
        self.db = db

    def should_create_snapshot(self, crop_instance_id: UUID) -> bool:
        """
        Determine if a snapshot should be created based on action count
        since the last snapshot.
        """
        last_snapshot = self._get_latest_snapshot(crop_instance_id)

        if last_snapshot:
            last_action_seq = last_snapshot.action_sequence_number or 0
        else:
            last_action_seq = 0

        # Count actions since last snapshot
        action_count = self.db.query(ActionLog).filter(
            ActionLog.crop_instance_id == crop_instance_id,
            ActionLog.sequence_number > last_action_seq,
            ActionLog.is_deleted == False,
        ).count()

        return action_count >= SNAPSHOT_INTERVAL

    def create_snapshot(
        self,
        crop_instance_id: UUID,
        state_data: Dict[str, Any],
        action_sequence_number: int,
        replay_hash: Optional[str] = None,
    ) -> CropInstanceSnapshot:
        """
        Create a new snapshot of the crop instance state.

        Args:
            crop_instance_id: The crop instance to snapshot
            state_data: Full computed state dict (stress, risk, stage, etc.)
            action_sequence_number: The sequence number of the last processed action
            replay_hash: Optional deterministic hash of the replay output
        """
        snapshot = CropInstanceSnapshot(
            crop_instance_id=crop_instance_id,
            state_data=state_data,
            action_sequence_number=action_sequence_number,
            replay_hash=replay_hash,
            snapshot_version="1.0",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(snapshot)
        self.db.flush()

        logger.info(
            f"Created snapshot for crop {crop_instance_id} "
            f"at action_seq={action_sequence_number}"
        )
        return snapshot

    def load_latest_snapshot(
        self, crop_instance_id: UUID
    ) -> Optional[CropInstanceSnapshot]:
        """
        Load the most recent valid snapshot for a crop instance.
        Returns None if no snapshots exist.
        """
        return self._get_latest_snapshot(crop_instance_id)

    def invalidate_snapshots_after(
        self, crop_instance_id: UUID, after_sequence: int
    ) -> int:
        """
        Invalidate (soft-delete) all snapshots after a given action sequence.
        Used when actions are retroactively modified.

        Returns the number of invalidated snapshots.
        """
        snapshots = self.db.query(CropInstanceSnapshot).filter(
            CropInstanceSnapshot.crop_instance_id == crop_instance_id,
            CropInstanceSnapshot.action_sequence_number > after_sequence,
            CropInstanceSnapshot.is_deleted == False,
        ).all()

        count = 0
        for snap in snapshots:
            snap.is_deleted = True
            snap.deleted_at = datetime.now(timezone.utc)
            count += 1

        if count > 0:
            logger.info(
                f"Invalidated {count} snapshots for crop {crop_instance_id} "
                f"after sequence {after_sequence}"
            )

        return count

    def _get_latest_snapshot(
        self, crop_instance_id: UUID
    ) -> Optional[CropInstanceSnapshot]:
        """Get the most recent non-deleted snapshot."""
        return (
            self.db.query(CropInstanceSnapshot)
            .filter(
                CropInstanceSnapshot.crop_instance_id == crop_instance_id,
                CropInstanceSnapshot.is_deleted == False,
            )
            .order_by(CropInstanceSnapshot.action_sequence_number.desc())
            .first()
        )

    def get_snapshot_count(self, crop_instance_id: UUID) -> int:
        """Get total number of active snapshots for a crop instance."""
        return self.db.query(CropInstanceSnapshot).filter(
            CropInstanceSnapshot.crop_instance_id == crop_instance_id,
            CropInstanceSnapshot.is_deleted == False,
        ).count()
