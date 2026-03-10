"""
Action Service

Business logic for action logging with chronological validation.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

from app.models.action_log import ActionLog
from app.models.crop_instance import CropInstance
from app.schemas.crop_instance import ActionLogCreate


class ActionService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self, crop_id: UUID, farmer_id: UUID, data: ActionLogCreate
    ) -> ActionLog:
        """
        Log an action with chronological invariant enforcement.
        
        Rules (TDD 4.5):
        1. effective_date >= crop.sowing_date
        2. effective_date >= last_action.effective_date (same crop)
        3. Idempotency key must be unique if provided
        """

        # Get crop and verify ownership
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            raise PermissionError("Crop not found or not owned by you")

        # Check crop is in an actionable state
        if crop.state in ("Closed", "Archived"):
            raise ValueError(f"Cannot log actions on crop in '{crop.state}' state")

        # Rule 1: effective_date >= sowing_date
        if data.effective_date < crop.sowing_date:
            raise ValueError(
                f"Action date ({data.effective_date}) cannot be before "
                f"sowing date ({crop.sowing_date})"
            )

        # Rule 2: effective_date >= last action's effective_date
        last_action = self.db.query(ActionLog).filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.is_deleted == False,
        ).order_by(ActionLog.effective_date.desc()).first()

        if last_action and data.effective_date < last_action.effective_date:
            raise ValueError(
                f"Action date ({data.effective_date}) cannot be before "
                f"last action date ({last_action.effective_date}). "
                "Actions must be chronologically ordered."
            )

        # Rule 3: idempotency check
        if data.idempotency_key:
            existing = self.db.query(ActionLog).filter(
                ActionLog.idempotency_key == data.idempotency_key,
            ).first()
            if existing:
                raise ValueError(
                    f"Action with idempotency key '{data.idempotency_key}' already exists"
                )

        # Create action log
        action = ActionLog(
            crop_instance_id=crop_id,
            action_type=data.action_type,
            effective_date=data.effective_date,
            category=data.category,
            metadata_json=data.metadata_json or {},
            notes=data.notes,
            local_seq_no=data.local_seq_no,
            device_timestamp=data.device_timestamp,
            idempotency_key=data.idempotency_key,
        )
        self.db.add(action)

        # Activate crop if still in Created state
        if crop.state == "Created":
            crop.state = "Active"

        self.db.commit()
        self.db.refresh(action)
        return action
