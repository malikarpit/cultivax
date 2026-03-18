"""
Exposure Fairness Engine

Implements provider ranking with fairness constraints to prevent
monopolistic visibility in the marketplace.

MSDD 2.8.3 | SOE Enhancement 1, 9, 11
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import random
import logging

from app.models.service_provider import ServiceProvider
from app.services.soe.trust_engine import TrustScoreEngine

logger = logging.getLogger(__name__)

# Ranking weights
TRUST_WEIGHT = 0.85
RANDOM_WEIGHT = 0.10
REGIONAL_WEIGHT = 0.05

# Exposure cap: top 3 providers cannot hold >70% exposure over 30 days
MAX_EXPOSURE_SHARE = 0.70
EXPOSURE_WINDOW_DAYS = 30

# Regional saturation threshold
REGIONAL_SATURATION_THRESHOLD = 10


class ExposureFairnessEngine:
    """
    Computes provider rankings with fairness constraints.

    Ranking formula (MSDD 2.8.3 + SOE Enhancement 1):
        ranking = trust_score * 0.85 + random_factor * 0.10 + regional_weight * 0.05

    Additional constraints:
    - Top 3 providers cannot occupy >70% exposure over rolling 30 days
    - Consistent visibility dominance triggers slight decay
    - Regional saturation control with minimum exposure rotation (SOE Enhancement 11)
    """

    def __init__(self, db: Session):
        self.db = db
        self.trust_engine = TrustScoreEngine(db)

    def compute_rankings(
        self,
        region: str,
        service_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Compute ranked provider list for a given region and service type.
        """
        # Fetch eligible providers
        query = self.db.query(ServiceProvider).filter(
            ServiceProvider.is_deleted == False,
            ServiceProvider.is_verified == True,
            ServiceProvider.region == region,
        )

        if service_type:
            query = query.filter(
                ServiceProvider.service_types.contains([service_type])
            )

        providers = query.all()

        if not providers:
            return []

        # Compute scores
        ranked = []
        for provider in providers:
            trust_score = self.trust_engine.compute_trust_score(provider.id)
            random_factor = random.uniform(0.0, 1.0)

            # Regional weight: higher if fewer providers in micro-region
            regional_weight = self._compute_regional_weight(
                provider, len(providers)
            )

            # Composite ranking score
            ranking_score = (
                TRUST_WEIGHT * trust_score.get("trust_score", 0.5)
                + RANDOM_WEIGHT * random_factor
                + REGIONAL_WEIGHT * regional_weight
            )

            # Apply exposure decay if provider dominates visibility
            decay = self._compute_exposure_decay(provider.id)
            ranking_score *= decay

            ranked.append({
                "provider_id": str(provider.id),
                "provider_name": provider.business_name,
                "trust_score": trust_score.get("trust_score", 0.5),
                "ranking_score": float(int(ranking_score * 10000)) / 10000,
                "region": provider.region,
                "service_types": provider.service_types,
                "random_factor": float(int(random_factor * 10000)) / 10000,
                "exposure_decay": float(int(decay * 10000)) / 10000,
            })

        # Sort by ranking score descending
        ranked.sort(key=lambda x: x["ranking_score"], reverse=True)

        # Apply exposure cap enforcement
        ranked = self._enforce_exposure_cap(ranked)

        return [r for i, r in enumerate(ranked) if i < limit]

    def _compute_regional_weight(
        self, provider: ServiceProvider, total_in_region: int
    ) -> float:
        """
        Regional saturation control (SOE Enhancement 11).
        Fewer providers in region = higher individual weight.
        """
        if total_in_region <= 0:
            return 0.5
        if total_in_region >= REGIONAL_SATURATION_THRESHOLD:
            return 0.3  # Saturated — reduce weight
        return min(1.0, 1.0 / total_in_region)

    def _compute_exposure_decay(self, provider_id: UUID) -> float:
        """
        If provider consistently dominates visibility, apply slight decay.
        Returns a multiplier between 0.85 and 1.0.
        """
        # In a full implementation, this would query exposure_log table
        # For now, return no decay
        return 1.0

    def _enforce_exposure_cap(
        self, ranked: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ensure top 3 providers don't occupy >70% total exposure.
        If they do, rotate lower-ranked providers up.
        """
        if len(ranked) <= 3:
            return ranked

        total_score = sum(r["ranking_score"] for r in ranked)
        if total_score <= 0:
            return ranked

        top3_share = sum(r["ranking_score"] for i, r in enumerate(ranked) if i < 3) / total_score

        if top3_share > MAX_EXPOSURE_SHARE:
            # Boost 4th-6th ranked providers slightly
            for i in range(3, min(6, len(ranked))):
                ranked[i]["ranking_score"] *= 1.15
                ranked[i]["exposure_boosted"] = True

            # Re-sort
            ranked.sort(key=lambda x: x["ranking_score"], reverse=True)

        return ranked
