"""
Crop Service

Business logic for crop instance CRUD operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import Optional
from datetime import date
import math

from app.models.crop_instance import CropInstance
from app.models.deviation import DeviationProfile
from app.models.user import User
from app.schemas.crop_instance import CropInstanceCreate, CropInstanceUpdate
from app.schemas.common import PaginatedResponse
from app.services.ctis.seasonal_window import assign_seasonal_window


class CropService:
    def __init__(self, db: Session):
        self.db = db

    def create_crop(self, farmer: User, data: CropInstanceCreate) -> CropInstance:
        """Create a new crop instance with seasonal window assignment."""

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
            rule_template_id=data.rule_template_id,
            seasonal_window_category=window,
            state="Created",
            metadata_extra=data.metadata_extra or {},
        )
        self.db.add(crop)

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

        total = query.count()
        total_pages = math.ceil(total / per_page) if total > 0 else 1

        items = query.order_by(CropInstance.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    def get_crop(self, crop_id: UUID, farmer_id: UUID) -> Optional[CropInstance]:
        """Get a single crop instance."""
        return self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()

    def update_crop(
        self, crop_id: UUID, farmer_id: UUID, data: CropInstanceUpdate
    ) -> Optional[CropInstance]:
        """Update a crop (non-state, non-sowing-date fields)."""
        crop = self.get_crop(crop_id, farmer_id)
        if not crop:
            return None

        update_data = data.model_dump(exclude_unset=True)
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
        # Reset state for replay
        crop.current_day_number = 0
        crop.stress_score = 0.0
        crop.risk_index = 0.0
        crop.stage = None
        crop.stage_offset_days = 0

        # TODO: In Day 12, trigger full replay via Event Dispatcher

        self.db.commit()
        self.db.refresh(crop)
        return crop
