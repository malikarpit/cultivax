"""
Recommendation Engine

Computes daily prioritized recommendations for crop management actions.

Patch Module 2, Sec 15
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

from app.models.recommendation import Recommendation
from app.models.crop_instance import CropInstance

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

    def compute_recommendations(
        self, crop_instance_id: UUID
    ) -> List[Recommendation]:
        """
        Compute prioritized recommendations for a crop instance.

        Priority formula (Patch Sec 15):
            score = urgency * stage_criticality + risk_index * 0.4
                    + days_until_deadline * -0.1
        """
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_instance_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            return []

        recommendations = []

        # Generate recommendations based on crop state
        if crop.state == "Active":
            recommendations.extend(
                self._generate_active_recommendations(crop)
            )
        elif crop.state == "AtRisk":
            recommendations.extend(
                self._generate_risk_recommendations(crop)
            )
        elif crop.state == "ReadyToHarvest":
            recommendations.extend(
                self._generate_harvest_recommendations(crop)
            )

        # Sort by priority and limit
        recommendations.sort(key=lambda r: r.priority_rank, reverse=True)
        return [r for i, r in enumerate(recommendations) if i < MAX_DAILY_RECOMMENDATIONS]

    def _generate_active_recommendations(
        self, crop: CropInstance
    ) -> List[Recommendation]:
        """Generate recommendations for active crops."""
        recs = []
        stress = float(crop.stress_score or 0.0)

        if stress > 0.5:
            recs.append(Recommendation(
                crop_instance_id=crop.id,
                recommendation_type="irrigation",
                priority_rank=self._compute_priority("irrigation", stress, crop),
                message_key="stress_high_irrigate",
                message_parameters={"stress_level": f"{stress:.0%}"},
                basis="Stress score elevated above 50%, irrigation may reduce stress",
                status="active",
            ))

        if stress > 0.3:
            recs.append(Recommendation(
                crop_instance_id=crop.id,
                recommendation_type="general",
                priority_rank=self._compute_priority("general", stress, crop),
                message_key="monitor_stress",
                message_parameters={"stress_level": f"{stress:.0%}"},
                basis="Stress score elevated — monitor closely",
                status="active",
            ))

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

    def get_recommendations(
        self, crop_instance_id: UUID
    ) -> List[Recommendation]:
        """Get active recommendations for a crop."""
        return self.db.query(Recommendation).filter(
            Recommendation.crop_instance_id == crop_instance_id,
            Recommendation.status == "active",
            Recommendation.is_deleted == False,
        ).order_by(Recommendation.priority_rank.desc()).limit(
            MAX_DAILY_RECOMMENDATIONS
        ).all()
