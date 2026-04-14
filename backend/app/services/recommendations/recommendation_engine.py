"""
Recommendation Engine

Computes daily prioritized recommendations for crop management actions.

Patch Module 2, Sec 15
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.crop_instance import CropInstance
from app.models.recommendation import Recommendation

logger = logging.getLogger(__name__)

# Urgency weights for recommendation types
URGENCY_WEIGHTS = {
    "harvest_prep": 1.0,
    "irrigation": 0.8,
    "fertilizer": 0.6,
    "pesticide": 0.7,
    "general": 0.3,
}

# Top N recommendations surfaced per crop per day
MAX_DAILY_RECOMMENDATIONS = 3


class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def compute_recommendations(self, crop_instance_id: UUID) -> List[Recommendation]:
        """
        Compute prioritized recommendations for a crop instance.

        Priority formula (Patch Sec 15):
            score = urgency * stage_criticality + risk_index * 0.4
                    + days_until_deadline * -0.1

        FR-6: Adapts recommendations based on deviation profile.
        FR-9: Populates structured rationale on every recommendation.
        """
        crop = (
            self.db.query(CropInstance)
            .filter(
                CropInstance.id == crop_instance_id,
                CropInstance.is_deleted == False,
            )
            .first()
        )

        if not crop:
            return []

        # FR-6: Load deviation profile for adaptive guidance
        deviation_profile = self._load_deviation_profile(crop_instance_id)

        recommendations = []

        # Generate recommendations based on crop state
        if crop.state == "Active":
            recommendations.extend(self._generate_active_recommendations(crop))
        elif crop.state == "AtRisk":
            recommendations.extend(self._generate_risk_recommendations(crop))
        elif crop.state == "ReadyToHarvest":
            recommendations.extend(self._generate_harvest_recommendations(crop))

        # FR-6: Inject deviation-aware adaptive recommendations
        if deviation_profile:
            recommendations.extend(
                self._generate_deviation_recommendations(crop, deviation_profile)
            )

        # Sort by priority and limit
        recommendations.sort(key=lambda r: r.priority_rank, reverse=True)
        return [
            r for i, r in enumerate(recommendations) if i < MAX_DAILY_RECOMMENDATIONS
        ]

    def _load_deviation_profile(self, crop_instance_id: UUID):
        """Load the deviation profile for adaptive recommendation filtering (FR-6)."""
        try:
            from app.models.deviation import DeviationProfile

            return (
                self.db.query(DeviationProfile)
                .filter(
                    DeviationProfile.crop_instance_id == crop_instance_id,
                    DeviationProfile.is_deleted == False,
                )
                .first()
            )
        except Exception:
            return None

    def _generate_deviation_recommendations(
        self, crop: CropInstance, deviation
    ) -> List[Recommendation]:
        """FR-6: Generate corrective recommendations when crop deviates from timeline."""
        recs = []
        consecutive = getattr(deviation, "consecutive_count", 0) or 0
        trend_slope = getattr(deviation, "trend_slope", 0.0) or 0.0
        cumulative_days = getattr(deviation, "cumulative_days", 0) or 0

        if consecutive >= 3:
            recs.append(
                Recommendation(
                    crop_instance_id=crop.id,
                    recommendation_type="general",
                    priority_rank=self._compute_priority("general", 0.6, crop) + 20,
                    message_key="deviation_corrective_action",
                    message_parameters={
                        "consecutive_count": consecutive,
                        "cumulative_days": cumulative_days,
                    },
                    basis="Crop has deviated from expected timeline for multiple consecutive observations",
                    rationale={
                        "trigger": "consecutive_deviation >= 3",
                        "evidence": {
                            "consecutive_count": consecutive,
                            "trend_slope": trend_slope,
                            "cumulative_days": cumulative_days,
                        },
                        "confidence": 0.75,
                        "source": "deviation_tracker",
                    },
                    status="active",
                )
            )

        if trend_slope > 0.1:
            recs.append(
                Recommendation(
                    crop_instance_id=crop.id,
                    recommendation_type="irrigation",
                    priority_rank=self._compute_priority("irrigation", 0.7, crop) + 15,
                    message_key="timeline_correction_needed",
                    message_parameters={"trend_slope": f"{trend_slope:.2f}"},
                    basis="Deviation trend is accelerating — corrective action recommended",
                    rationale={
                        "trigger": "trend_slope > 0.1",
                        "evidence": {"trend_slope": trend_slope},
                        "confidence": 0.7,
                        "source": "deviation_tracker",
                    },
                    status="active",
                )
            )

        return recs

    def _generate_active_recommendations(
        self, crop: CropInstance
    ) -> List[Recommendation]:
        """Generate recommendations for active crops."""
        recs = []
        stress = float(crop.stress_score or 0.0)

        if stress > 0.5:
            recs.append(
                Recommendation(
                    crop_instance_id=crop.id,
                    recommendation_type="irrigation",
                    priority_rank=self._compute_priority("irrigation", stress, crop),
                    message_key="stress_high_irrigate",
                    message_parameters={"stress_level": f"{stress:.0%}"},
                    basis="Stress score elevated above 50%, irrigation may reduce stress",
                    rationale={
                        "trigger": "stress_score > 50%",
                        "evidence": {"stress_score": stress, "stage": crop.stage},
                        "confidence": 0.8,
                        "source": "stress_engine",
                    },
                    status="active",
                )
            )

        if stress > 0.3:
            recs.append(
                Recommendation(
                    crop_instance_id=crop.id,
                    recommendation_type="general",
                    priority_rank=self._compute_priority("general", stress, crop),
                    message_key="monitor_stress",
                    message_parameters={"stress_level": f"{stress:.0%}"},
                    basis="Stress score elevated — monitor closely",
                    rationale={
                        "trigger": "stress_score > 30%",
                        "evidence": {"stress_score": stress, "stage": crop.stage},
                        "confidence": 0.6,
                        "source": "stress_engine",
                    },
                    status="active",
                )
            )

        return recs

    def _generate_risk_recommendations(
        self, crop: CropInstance
    ) -> List[Recommendation]:
        """Generate recommendations for at-risk crops."""
        risk = float(crop.risk_index or 0.0)
        return [
            Recommendation(
                crop_instance_id=crop.id,
                recommendation_type="irrigation",
                priority_rank=self._compute_priority("irrigation", risk, crop),
                message_key="risk_high_immediate_action",
                message_parameters={"risk_level": f"{risk:.0%}"},
                basis="Crop at risk — immediate intervention recommended",
                rationale={
                    "trigger": "state == AtRisk",
                    "evidence": {"risk_index": risk, "state": crop.state},
                    "confidence": 0.9,
                    "source": "risk_pipeline",
                },
                status="active",
            ),
        ]

    def _generate_harvest_recommendations(
        self, crop: CropInstance
    ) -> List[Recommendation]:
        """Generate harvest preparation recommendations."""
        return [
            Recommendation(
                crop_instance_id=crop.id,
                recommendation_type="harvest_prep",
                priority_rank=100,
                message_key="ready_to_harvest",
                basis="Crop has reached maturity — prepare for harvest",
                rationale={
                    "trigger": "state == ReadyToHarvest",
                    "evidence": {"state": crop.state, "stage": crop.stage},
                    "confidence": 1.0,
                    "source": "stage_progression",
                },
                status="active",
            ),
        ]

    def _compute_priority(
        self, rec_type: str, risk_score: float, crop: CropInstance
    ) -> int:
        """Compute priority rank for a recommendation."""
        urgency = URGENCY_WEIGHTS.get(rec_type, 0.3)
        stage_criticality = 0.7 if crop.state in ("AtRisk", "Delayed") else 0.4
        score = urgency * stage_criticality + risk_score * 0.4
        return int(score * 100)

    def get_recommendations(self, crop_instance_id: UUID) -> List[Recommendation]:
        """Get active recommendations for a crop."""
        return (
            self.db.query(Recommendation)
            .filter(
                Recommendation.crop_instance_id == crop_instance_id,
                Recommendation.status == "active",
                Recommendation.is_deleted == False,
            )
            .order_by(Recommendation.priority_rank.desc())
            .limit(MAX_DAILY_RECOMMENDATIONS)
            .all()
        )

    def refresh_recommendations(
        self,
        crop_instance_id: UUID,
    ) -> List[Recommendation]:
        """
        Regenerate recommendations for a crop and persist fresh active records.

        Existing active recommendations are soft-expired before inserting new rows.
        """
        now = datetime.now(timezone.utc)

        existing_active = (
            self.db.query(Recommendation)
            .filter(
                Recommendation.crop_instance_id == crop_instance_id,
                Recommendation.status == "active",
                Recommendation.is_deleted == False,
            )
            .all()
        )

        for rec in existing_active:
            rec.status = "expired"
            rec.valid_until = now

        generated = self.compute_recommendations(crop_instance_id)
        for rec in generated:
            rec.valid_from = now
            if rec.valid_until is None:
                rec.valid_until = now + timedelta(days=1)
            self.db.add(rec)

        self.db.commit()
        return self.get_recommendations(crop_instance_id)

    def ensure_recommendations(
        self,
        crop_instance_id: UUID,
    ) -> List[Recommendation]:
        """
        Return active recommendations and auto-generate when missing.
        """
        recs = self.get_recommendations(crop_instance_id)
        if recs:
            return recs
        return self.refresh_recommendations(crop_instance_id)

    def update_status(
        self,
        crop_instance_id: UUID,
        recommendation_id: UUID,
        status: str,
        reason: Optional[str] = None,
    ) -> Recommendation:
        """Update recommendation status to dismissed or acted."""
        rec = (
            self.db.query(Recommendation)
            .filter(
                Recommendation.id == recommendation_id,
                Recommendation.crop_instance_id == crop_instance_id,
                Recommendation.is_deleted == False,
            )
            .first()
        )

        if not rec:
            raise ValueError("Recommendation not found")

        if status not in ("dismissed", "acted"):
            raise ValueError("Invalid recommendation status")

        rec.status = status
        rec.valid_until = datetime.now(timezone.utc)

        params = rec.message_parameters or {}
        if reason:
            params["resolution_reason"] = reason
            rec.message_parameters = params

        self.db.commit()
        self.db.refresh(rec)
        return rec

    def refresh_for_active_crops(self) -> int:
        """Generate recommendations for all non-archived active crop instances."""
        crops = (
            self.db.query(CropInstance)
            .filter(
                CropInstance.is_deleted == False,
                CropInstance.is_archived == False,
                CropInstance.state.in_(["Active", "AtRisk", "ReadyToHarvest"]),
            )
            .all()
        )

        refreshed = 0
        for crop in crops:
            self.refresh_recommendations(crop.id)
            refreshed += 1

        return refreshed

    def override_recommendation(
        self,
        crop_instance_id: UUID,
        recommendation_id: UUID,
        farmer_id: UUID,
        override_action: str,
        farmer_reason: Optional[str] = None,
    ) -> "RecommendationOverride":
        """
        FR-7/FR-8: Record a farmer override of a recommendation.

        Args:
            override_action: dismissed | ignored | acted_differently
        """
        from app.models.recommendation_override import RecommendationOverride

        rec = (
            self.db.query(Recommendation)
            .filter(
                Recommendation.id == recommendation_id,
                Recommendation.crop_instance_id == crop_instance_id,
                Recommendation.is_deleted == False,
            )
            .first()
        )
        if not rec:
            raise ValueError("Recommendation not found")

        if override_action not in ("dismissed", "ignored", "acted_differently"):
            raise ValueError("Invalid override action")

        override = RecommendationOverride(
            recommendation_id=rec.id,
            crop_instance_id=crop_instance_id,
            farmer_id=farmer_id,
            override_action=override_action,
            farmer_reason=farmer_reason,
            original_recommendation_type=rec.recommendation_type,
            original_priority_rank=rec.priority_rank,
            original_rationale=rec.rationale,
        )
        self.db.add(override)

        rec.status = "overridden"
        rec.valid_until = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(override)
        return override

    def get_overrides(self, crop_instance_id: UUID) -> list:
        """FR-8: Get override history for a crop instance."""
        from app.models.recommendation_override import RecommendationOverride

        return (
            self.db.query(RecommendationOverride)
            .filter(
                RecommendationOverride.crop_instance_id == crop_instance_id,
                RecommendationOverride.is_deleted == False,
            )
            .order_by(RecommendationOverride.created_at.desc())
            .all()
        )

    def create_service_suggestion(
        self,
        crop_instance_id: UUID,
        service_type: str,
        urgency: str = "medium",
    ) -> Recommendation:
        """
        MSDD 2.11: Create a recommendation linking CTIS needs to SOE services.
        Called when the replay engine detects a service need.
        """
        priority = 75 if urgency == "high" else 50

        rec = Recommendation(
            crop_instance_id=crop_instance_id,
            recommendation_type="service_suggestion",
            priority_rank=priority,
            message_key=f"soe_suggest_{service_type}",
            message_parameters={
                "service_type": service_type,
                "urgency": urgency,
            },
            basis=f"CTIS replay detected need for {service_type}",
            rationale={
                "trigger": "ctis_suggest_service_event",
                "evidence": {
                    "service_type": service_type,
                    "urgency": urgency,
                },
                "confidence": 0.85,
                "source": "ctis_replay_engine",
            },
            status="active",
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec
