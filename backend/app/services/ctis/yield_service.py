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
from datetime import datetime, timezone, timedelta
import logging

from app.models.crop_instance import CropInstance
from app.models.yield_record import YieldRecord
from app.models.weather_snapshot import WeatherSnapshot
from app.schemas.yield_record import YieldSubmission
from app.api.v1.weather import _region_coords

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

        existing = self.db.query(YieldRecord).filter(
            YieldRecord.crop_instance_id == crop_id,
            YieldRecord.is_deleted == False,
        ).first()
        if existing:
            raise RuntimeError(
                "Yield already submitted for this crop. Resubmission is blocked; use /yield/history to review."
            )

        if crop.state != "ReadyToHarvest":
            raise ValueError(
                f"Cannot submit yield unless crop is in 'ReadyToHarvest' state (current: '{crop.state}')"
            )

        # Compute verification score (Feature 16 Weather Contribution output)
        verification_score, weather_risk_recent = self._compute_verification_score(crop)

        # Biological limit cap
        bio_limit = BIOLOGICAL_LIMITS.get(
            crop.crop_type.lower(), DEFAULT_BIOLOGICAL_LIMIT
        )
        ml_yield_value = min(data.reported_yield, bio_limit)
        was_capped = ml_yield_value < data.reported_yield

        # Create yield record
        metadata = {
            "stress_score": float(crop.stress_score or 0.0),
            "risk_index": float(crop.risk_index or 0.0),
            "weather_risk_recent": float(weather_risk_recent),
            "seasonal_window_category": crop.seasonal_window_category,
            "crop_state_at_submission": crop.state,
            "biological_cap": bio_limit,
            "reported_yield": data.reported_yield,
            "ml_yield_value": ml_yield_value,
            "bio_cap_applied": was_capped,
        }

        yield_record = YieldRecord(
            crop_instance_id=crop_id,
            reported_yield=data.reported_yield,
            ml_yield_value=ml_yield_value,
            yield_unit=data.yield_unit or "kg/acre",
            yield_verification_score=verification_score,
            harvest_date=data.harvest_date or datetime.now(timezone.utc).date(),
            quality_grade=data.quality_grade,
            moisture_pct=data.moisture_pct,
            notes=data.notes,
            biological_cap=bio_limit,
            bio_cap_applied=was_capped,
            verification_metadata=metadata,
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

    def get_latest_yield(self, crop_id: UUID, farmer_id: UUID) -> YieldRecord:
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()
        if not crop:
            raise LookupError(f"Crop instance {crop_id} not found")

        record = self.db.query(YieldRecord).filter(
            YieldRecord.crop_instance_id == crop_id,
            YieldRecord.is_deleted == False,
        ).order_by(YieldRecord.created_at.desc()).first()
        if not record:
            raise LookupError("No yield record found for this crop")
        return record

    def list_yield_history(self, crop_id: UUID, farmer_id: UUID) -> list[YieldRecord]:
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        ).first()
        if not crop:
            raise LookupError(f"Crop instance {crop_id} not found")

        return self.db.query(YieldRecord).filter(
            YieldRecord.crop_instance_id == crop_id,
            YieldRecord.is_deleted == False,
        ).order_by(YieldRecord.created_at.desc()).all()

    def _compute_verification_score(self, crop: CropInstance) -> tuple[float, float]:
        """
        Compute YieldVerificationScore (0-1) from:
        - Stress history
        - Weather conditions during season (7-day rolling average)
        - Seasonal risk category
        
        Returns: (score, weather_risk_recent)
        """
        score = 1.0

        # Penalty for high stress
        stress = float(crop.stress_score or 0.0) / 100.0  # normalize
        score -= stress * 0.3

        # Penalty for risk
        risk = float(crop.risk_index or 0.0)
        score -= risk * 0.2

        # Seasonal window penalty
        if crop.seasonal_window_category == "Late":
            score -= 0.1
        elif crop.seasonal_window_category == "Early":
            score -= 0.05

        # Feature 16: Weather Intelligence 7-day rolling risk
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        defaults = _region_coords(crop.region)
        loc_key = f"geo_{round(defaults['lat'], 2)}_{round(defaults['lng'], 2)}"
        
        recent_snapshots = self.db.query(WeatherSnapshot).filter(
            WeatherSnapshot.location_key == loc_key,
            WeatherSnapshot.captured_at >= recent_cutoff
        ).all()
        
        weather_risk_recent = 0.0
        if recent_snapshots:
            weather_risk_recent = sum(s.weather_risk_score for s in recent_snapshots) / len(recent_snapshots)
        
        # Apply up to 15% penalty for bad weather at harvest time
        score -= weather_risk_recent * 0.15

        final_score = max(0.0, min(1.0, float(int(score * 10000)) / 10000))
        return final_score, round(weather_risk_recent, 4)
