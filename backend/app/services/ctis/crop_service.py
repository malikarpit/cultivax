"""
Crop Service

Business logic for crop instance CRUD operations.
"""

import math
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.crop_instance import CropInstance
from app.models.deviation import DeviationProfile
from app.models.land_parcel import LandParcel
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.crop_instance import CropInstanceCreate, CropInstanceUpdate
from app.services.ctis.seasonal_window import assign_seasonal_window
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.services.event_dispatcher.event_types import CTISEvents
from app.services.event_dispatcher.mutation_guard import allow_ctis_mutation


class CropService:
    def __init__(self, db: Session):
        self.db = db

    def create_crop(self, farmer: User, data: CropInstanceCreate) -> CropInstance:
        """Create a new crop instance with seasonal window assignment."""

        if data.land_parcel_id:
            parcel = (
                self.db.query(LandParcel)
                .filter(
                    LandParcel.id == data.land_parcel_id,
                    LandParcel.farmer_id == farmer.id,
                    LandParcel.is_deleted == False,
                )
                .first()
            )
            if not parcel:
                raise ValueError("Invalid land_parcel_id for this farmer")

        # Resolve Active Rule Template dynamically by precedence policy
        from app.models.crop_rule_template import CropRuleTemplate

        base_query = self.db.query(CropRuleTemplate).filter(
            CropRuleTemplate.status == "active",
            CropRuleTemplate.crop_type == data.crop_type,
            CropRuleTemplate.effective_from_date <= data.sowing_date,
        )
        # Attempt exact match (region + variety)
        rule_template = (
            base_query.filter(
                CropRuleTemplate.region == data.region,
                CropRuleTemplate.variety == data.variety,
            )
            .order_by(CropRuleTemplate.effective_from_date.desc())
            .first()
        )

        # Fallback exactly matching region ignoring variety
        if not rule_template:
            rule_template = (
                base_query.filter(
                    CropRuleTemplate.region == data.region,
                    CropRuleTemplate.variety == None,
                )
                .order_by(CropRuleTemplate.effective_from_date.desc())
                .first()
            )

        # Fallback exactly matching global configurations ignoring both
        if not rule_template:
            rule_template = (
                base_query.filter(
                    CropRuleTemplate.region == None, CropRuleTemplate.variety == None
                )
                .order_by(CropRuleTemplate.effective_from_date.desc())
                .first()
            )

        assigned_rule_id = rule_template.id if rule_template else None

        if not assigned_rule_id:
            import logging

            logging.warning(
                f"CTIS Validation Warning: NO active rule template found parsing {data.crop_type} scope."
            )

        # Assign seasonal window (immutable at creation — MSDD 1.9)
        window = assign_seasonal_window(
            self.db, data.sowing_date, data.crop_type, data.region
        )

        crop = CropInstance(
            farmer_id=farmer.id,
            crop_type=data.crop_type,
            variety=data.variety,
            sowing_date=data.sowing_date,
            region=data.region,
            sub_region=data.sub_region,
            land_area=data.land_area,
            land_parcel_id=data.land_parcel_id,
            rule_template_id=data.rule_template_id or assigned_rule_id,
            seasonal_window_category=window,
            state="Created",
            metadata_extra=data.metadata_extra or {},
        )
        self.db.add(crop)
        self.db.flush()

        # Mark onboarding complete on first successful crop creation
        if not farmer.is_onboarded:
            farmer.is_onboarded = True
            self.db.add(farmer)

        # Initialize deviation profile
        deviation = DeviationProfile(crop_instance_id=crop.id)
        self.db.add(deviation)

        self.db.commit()
        self.db.refresh(crop)
        return crop

    def list_crops(
        self,
        farmer_id: UUID,
        page: int = 1,
        per_page: int = 20,
        state: Optional[str] = None,
        crop_type: Optional[str] = None,
        region: Optional[str] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
        seasonal_window_category: Optional[str] = None,
    ) -> PaginatedResponse:
        """List crops with pagination and filtering."""

        query = self.db.query(CropInstance).filter(
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        )

        if not include_archived:
            query = query.filter(CropInstance.state != "Archived")

        if state:
            query = query.filter(CropInstance.state == state)
        if crop_type:
            query = query.filter(CropInstance.crop_type == crop_type)
        if region:
            query = query.filter(CropInstance.region == region)
        if seasonal_window_category:
            query = query.filter(
                CropInstance.seasonal_window_category == seasonal_window_category
            )
        if search:
            query = query.filter(
                (CropInstance.crop_type.ilike(f"%{search}%"))
                | (CropInstance.variety.ilike(f"%{search}%"))
            )

        total = query.count()
        total_pages = math.ceil(total / per_page) if total > 0 else 1

        items = (
            query.order_by(CropInstance.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    def get_crop(self, crop_id: UUID, farmer_id: UUID) -> Optional[CropInstance]:
        """Get a single crop instance."""
        return (
            self.db.query(CropInstance)
            .filter(
                CropInstance.id == crop_id,
                CropInstance.farmer_id == farmer_id,
                CropInstance.is_deleted == False,
            )
            .first()
        )

    def update_crop(
        self, crop_id: UUID, farmer_id: UUID, data: CropInstanceUpdate
    ) -> Optional[CropInstance]:
        """Update a crop (non-state, non-sowing-date fields)."""
        crop = self.get_crop(crop_id, farmer_id)
        if not crop:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if (
            "land_parcel_id" in update_data
            and update_data["land_parcel_id"] is not None
        ):
            parcel = (
                self.db.query(LandParcel)
                .filter(
                    LandParcel.id == update_data["land_parcel_id"],
                    LandParcel.farmer_id == farmer_id,
                    LandParcel.is_deleted == False,
                )
                .first()
            )
            if not parcel:
                raise ValueError("Invalid land_parcel_id for this farmer")

        for field, value in update_data.items():
            setattr(crop, field, value)

        self.db.commit()
        self.db.refresh(crop)
        return crop

    def modify_sowing_date(
        self, crop_id: UUID, farmer_id: UUID, new_sowing_date: date
    ) -> Optional[CropInstance]:
        """
        Modify sowing date — triggers full replay.
        Note: seasonal_window_category is NOT recalculated (immutable).
        """
        crop = self.get_crop(crop_id, farmer_id)
        if not crop:
            return None

        crop.sowing_date = new_sowing_date
        # Reset replay-derived fields under controlled mutation context.
        with allow_ctis_mutation():
            crop.current_day_number = 0
            crop.stress_score = 0.0
            crop.risk_index = 0.0
            crop.stage = None
            crop.stage_offset_days = 0
            self.db.flush()

        # Trigger full replay via Event Dispatcher
        dispatcher = DBEventDispatcher(self.db)
        dispatcher.publish(
            event_type=CTISEvents.REPLAY_TRIGGERED,
            entity_type="CropInstance",
            entity_id=str(crop.id),
            payload={
                "crop_instance_id": str(crop.id),
                "reason": "sowing_date_modified",
                "new_sowing_date": crop.sowing_date.isoformat(),
            },
        )

        self.db.commit()
        self.db.refresh(crop)
        return crop

    def change_state(
        self, crop_id: UUID, farmer_id: UUID, new_state: str
    ) -> Optional[CropInstance]:
        """Change the state of a crop."""
        crop = self.get_crop(crop_id, farmer_id)
        if not crop:
            return None

        dispatcher = DBEventDispatcher(self.db)
        dispatcher.publish(
            event_type=CTISEvents.CROP_STATE_CHANGE_REQUESTED,
            entity_type="CropInstance",
            entity_id=crop.id,
            payload={
                "target_state": new_state,
                "requested_by": str(farmer_id),
            },
            partition_key=crop.id,
        )
        # Preserve synchronous endpoint semantics by handling the event immediately.
        dispatcher.process_pending(batch_size=10)

        self.db.refresh(crop)
        return crop

    def set_archived(
        self, crop_id: UUID, farmer_id: UUID, is_archived: bool
    ) -> Optional[CropInstance]:
        """Set the archived status of a crop."""
        crop = self.get_crop(crop_id, farmer_id)
        if not crop:
            return None
        crop.is_archived = is_archived
        self.db.commit()

        if is_archived:
            self.change_state(crop_id, farmer_id, "Archived")

        self.db.refresh(crop)
        return crop
