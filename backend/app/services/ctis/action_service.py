"""
Action Service

Business logic for action logging with chronological validation.
Publishes ActionLogged event after successful insert (Day 13 integration).
"""

from sqlalchemy.orm import Session  # type: ignore
from uuid import UUID
from datetime import date
import logging

from app.models.action_log import ActionLog  # type: ignore
from app.models.crop_instance import CropInstance  # type: ignore
from app.models.event_log import EventLog  # type: ignore
from app.schemas.crop_instance import ActionLogCreate  # type: ignore
from app.services.ctis.state_machine import CropStateMachine, BLOCKED_STATES  # type: ignore

logger = logging.getLogger(__name__)


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
        
        After insert, publishes an ActionLogged event for the
        Event Dispatcher → Replay Engine pipeline (Day 13).
        """

        # Get crop and verify ownership
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            raise PermissionError("Crop not found or not owned by you")

        # Check crop is in an actionable state (uses State Machine)
        if crop.state in BLOCKED_STATES:
            raise ValueError(
                f"Cannot log actions on crop in '{crop.state}' state. "
                f"{'Admin must resolve RecoveryRequired state.' if crop.state == 'RecoveryRequired' else ''}"
            )

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

        # Provisional update for Day 7 (until ReplayEngine is implemented)
        action_day = (data.effective_date - crop.sowing_date).days
        if crop.current_day_number is None or action_day > crop.current_day_number:
            crop.current_day_number = action_day

        # Publish ActionLogged event for Replay Engine pipeline (Day 13)
        import hashlib
        import json
        
        payload_dict = {
            "crop_instance_id": str(crop_id),
            "action_type": data.action_type,
            "effective_date": str(data.effective_date),
            "category": data.category,
        }
        
        # Simple hash based on idempotency_key or payload
        hash_source = data.idempotency_key or json.dumps(payload_dict)
        e_hash = hashlib.sha256(hash_source.encode()).hexdigest()

        event = EventLog(
            event_type="ActionLogged",
            entity_type="CropInstance",
            entity_id=crop_id,
            partition_key=crop_id,
            event_hash=e_hash,
            payload=payload_dict,
        )
        self.db.add(event)

        logger.info(
            f"Action logged: {data.action_type} on crop {crop_id}, "
            f"ActionLogged event published"
        )

        self.db.commit()
        self.db.refresh(action)
        return action

    def list_actions(self, crop_id: UUID, farmer_id: UUID) -> list[ActionLog]:
        """List chronological actions for a specific crop."""
        # Verify ownership
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
        ).first()

        if not crop:
            raise PermissionError("Crop not found or not owned by you")

        return self.db.query(ActionLog).filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.is_deleted == False
        ).order_by(ActionLog.effective_date.desc()).all()

    def list_actions_paginated(
        self,
        crop_id: UUID,
        farmer_id: UUID,
        page: int = 1,
        page_size: int = 20,
        sort: str = "-effective_date",
    ) -> dict:
        """List crop actions with pagination and deterministic sorting."""
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            raise PermissionError("Crop not found or not owned by you")

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        query = self.db.query(ActionLog).filter(
            ActionLog.crop_instance_id == crop_id,
            ActionLog.is_deleted == False,
        )

        total = query.count()

        if sort == "effective_date":
            query = query.order_by(ActionLog.effective_date.asc(), ActionLog.created_at.asc())
        else:
            query = query.order_by(ActionLog.effective_date.desc(), ActionLog.created_at.desc())

        actions = query.offset(offset).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (offset + page_size) < total,
            "actions": actions,
        }
