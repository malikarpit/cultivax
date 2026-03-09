"""
Yield Service

Business logic for yield submission and verification.
Implements Farmer Truth vs ML Truth separation (TDD 4.9).

MSDD 1.12 | MSDD 4.3
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import logging

from app.models.crop_instance import CropInstance
from app.models.yield_record import YieldRecord
from app.schemas.yield_record import YieldSubmission

logger = logging.getLogger(__name__)

# Biological yield limits per crop type (tons/hectare)
BIOLOGICAL_LIMITS = {
    "wheat": 12.0,
    "rice": 15.0,
    "cotton": 6.0,
    "maize": 18.0,
    "soybean": 5.5,
}

DEFAULT_BIOLOGICAL_LIMIT = 20.0


class YieldService:
    """
    Manages yield submission with verification and truth separation.

    Three truths (MSDD 1.12 + 4.3):
    1. Farmer Truth: reported_yield — never modified in UI
    2. ML Truth: ml_yield_value — capped at biological limit, used for training
    3. Regional Truth: updates regional clusters prospectively only
    """

    def __init__(self, db: Session):
        self.db = db

    def submit_yield(
        self, crop_id: UUID, farmer_id: UUID, data: YieldSubmission
    ) -> YieldRecord:
        """
        Submit yield for a crop instance.

        Steps:
        1. Validate crop exists and belongs to farmer
        2. Compute YieldVerificationScore
        3. Cap at biological limit for ml_yield_value
        4. Create yield record
        5. Transition crop to 'Harvested'
        """
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            raise LookupError(f"Crop instance {crop_id} not found")

        if crop.state not in ("Active", "ReadyToHarvest", "AtRisk", "Delayed"):
            raise ValueError(
                f"Cannot submit yield for crop in state '{crop.state}'"
            )

        # Compute verification score
        verification_score = self._compute_verification_score(crop)

        # Biological limit cap
        bio_limit = BIOLOGICAL_LIMITS.get(
            crop.crop_type.lower(), DEFAULT_BIOLOGICAL_LIMIT
        )
        ml_yield_value = min(data.reported_yield, bio_limit)

        # Create yield record
        yield_record = YieldRecord(
            crop_instance_id=crop_id,
            farmer_id=farmer_id,
            reported_yield=data.reported_yield,
            ml_yield_value=ml_yield_value,
            yield_unit=data.yield_unit or "tons_per_hectare",
            verification_score=verification_score,
            harvest_date=data.harvest_date or datetime.now(timezone.utc).date(),
            quality_grade=data.quality_grade,
            notes=data.notes,
        )
        self.db.add(yield_record)

        # Transition crop to Harvested
        crop.state = "Harvested"
        crop.harvested_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(yield_record)

        logger.info(
            f"Yield submitted for crop {crop_id}: "
            f"reported={data.reported_yield}, ml_value={ml_yield_value}, "
            f"verification={verification_score:.2f}"
        )

        return yield_record

    def _compute_verification_score(self, crop: CropInstance) -> float:
        """
        Compute YieldVerificationScore (0-1) from:
        - Stress history
        - Weather conditions during season
        - Seasonal risk category
        """
        score = 1.0

        # Penalty for high stress
        stress = float(crop.stress_score or 0.0)
        score -= stress * 0.3

        # Penalty for risk
        risk = float(crop.risk_index or 0.0)
        score -= risk * 0.2

        # Seasonal window penalty
        if crop.seasonal_window_category == "Late":
            score -= 0.1
        elif crop.seasonal_window_category == "Early":
            score -= 0.05

        return max(0.0, min(1.0, float(int(score * 10000)) / 10000))
