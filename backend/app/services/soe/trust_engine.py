"""
Trust Score Engine — SOE Provider Trust Computation

Computes a provider's trust score from their service history
using a weighted multi-factor formula with temporal decay.

TDD Section 5.5 | SOE Enhancements 2 (Temporal Decay), 5 (Consistency Score)
"""

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import case, func  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.service_provider import ServiceProvider  # type: ignore
from app.models.service_request import ServiceRequest  # type: ignore
from app.models.service_review import ServiceReview  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — Weights (must sum to ~1.0 for the positive components)
# ---------------------------------------------------------------------------

WEIGHTS = {
    "completion_ratio": 0.25,  # w1: completed / total requests
    "complaint_ratio": 0.20,  # w2: applied as (1 - CPR)
    "normalized_rating": 0.25,  # w3: avg rating normalized to 0-1
    "verification_bonus": 0.05,  # w4: binary — verified or not
    "consistency_score": 0.15,  # w5: 1 − variance of completion times
    "escalation_penalty": 0.10,  # w6: subtracted for active escalations
}

# Temporal decay: multiply trust by 0.98 for each month of inactivity
DECAY_FACTOR_PER_MONTH = 0.98

# Minimum requests needed for a meaningful trust score
MIN_REQUESTS_FOR_TRUST = 3


class TrustEngine:
    """
    Computes a provider's trust score from their service history.

    Formula (TDD 5.5 + SOE Enhancements 2, 5):
        trust = w1*CR + w2*(1-CPR) + w3*norm_rating + w4*VB + w5*Consistency - w6*EP
        trust *= decay_factor ^ months_inactive
        trust = clamp(trust, 0, 1)
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_trust_score(self, provider_id: UUID) -> dict:
        """
        Compute the trust score for a provider.

        Returns a dict with the final score and all component breakdowns:
        {
            "trust_score": float,
            "components": { ... },
            "total_requests": int,
            "months_inactive": float,
            "is_new_provider": bool,
        }
        """

        # Load provider
        provider = (
            self.db.query(ServiceProvider)
            .filter(
                ServiceProvider.id == provider_id,
                ServiceProvider.is_deleted == False,
            )
            .first()
        )

        if not provider:
            raise ValueError(f"ServiceProvider {provider_id} not found")

        # Gather raw statistics
        stats = self._gather_stats(provider_id)

        # Check if provider has enough history
        if stats["total_requests"] < MIN_REQUESTS_FOR_TRUST:
            return {
                "trust_score": provider.trust_score or 0.5,
                "components": {},
                "total_requests": stats["total_requests"],
                "months_inactive": 0.0,
                "is_new_provider": True,
            }

        # Compute individual components
        cr = self._completion_ratio(stats)
        cpr = self._complaint_ratio(stats)
        norm_rating = self._normalized_rating(stats)
        vb = self._verification_bonus(provider)
        consistency = self._consistency_score(stats)
        ep = self._escalation_penalty(stats)

        # Weighted sum
        trust = (
            WEIGHTS["completion_ratio"] * cr
            + WEIGHTS["complaint_ratio"] * (1.0 - cpr)
            + WEIGHTS["normalized_rating"] * norm_rating
            + WEIGHTS["verification_bonus"] * vb
            + WEIGHTS["consistency_score"] * consistency
            - WEIGHTS["escalation_penalty"] * ep
        )

        # Temporal decay (SOE Enhancement 2)
        months_inactive = self._months_since_last_activity(stats)
        if months_inactive > 0:
            trust *= math.pow(DECAY_FACTOR_PER_MONTH, months_inactive)

        # Clamp to [0, 1]
        trust = max(0.0, min(1.0, float(round(trust, 4))))  # type: ignore

        # Persist the new trust score and counter fields (MSDD 2.4.1)
        provider.trust_score = trust
        provider.completion_count = stats["completed_requests"]
        provider.complaint_count = len(stats["complaints"])
        provider.resolution_score = round(cr * (1.0 - cpr), 4)
        self.db.commit()

        logger.info(
            f"Trust score for provider {provider_id}: {trust:.4f} "
            f"(CR={cr:.2f}, CPR={cpr:.2f}, rating={norm_rating:.2f}, "
            f"consistency={consistency:.2f}, decay_months={months_inactive:.1f})"
        )

        return {
            "trust_score": trust,
            "components": {
                "completion_ratio": float(round(cr, 4)),  # type: ignore
                "complaint_ratio": float(round(cpr, 4)),  # type: ignore
                "normalized_rating": float(round(norm_rating, 4)),  # type: ignore
                "verification_bonus": vb,
                "consistency_score": float(round(consistency, 4)),  # type: ignore
                "escalation_penalty": float(round(ep, 4)),  # type: ignore
            },
            "total_requests": stats["total_requests"],
            "months_inactive": float(round(months_inactive, 1)),  # type: ignore
            "is_new_provider": False,
        }

    # -----------------------------------------------------------------------
    # Component computations
    # -----------------------------------------------------------------------

    def _gather_stats(self, provider_id: UUID) -> dict:
        """Gather all raw statistics needed for trust computation."""

        # Total requests
        total_requests = (
            self.db.query(func.count(ServiceRequest.id))
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceRequest.is_deleted == False,
            )
            .scalar()
            or 0
        )

        # Completed requests
        completed_requests = (
            self.db.query(func.count(ServiceRequest.id))
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceRequest.status == "Completed",
                ServiceRequest.is_deleted == False,
            )
            .scalar()
            or 0
        )

        # Reviews with ratings
        reviews = (
            self.db.query(ServiceReview)
            .join(ServiceRequest, ServiceReview.request_id == ServiceRequest.id)
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceReview.is_deleted == False,
            )
            .all()
        )

        total_reviews = len(reviews)
        ratings = [r.rating for r in reviews if r.rating is not None]
        complaints = [r for r in reviews if r.complaint_category is not None]

        # Completion times (for consistency score)
        completion_times = []
        completed_with_dates = (
            self.db.query(ServiceRequest)
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceRequest.status == "Completed",
                ServiceRequest.preferred_date.isnot(None),
                ServiceRequest.completed_at.isnot(None),
                ServiceRequest.is_deleted == False,
            )
            .all()
        )

        for req in completed_with_dates:
            if req.completed_at and req.preferred_date:
                delta = (req.completed_at - req.preferred_date).total_seconds()
                completion_times.append(max(delta, 0))

        # Last activity date
        last_activity = (
            self.db.query(func.max(ServiceRequest.updated_at))
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceRequest.is_deleted == False,
            )
            .scalar()
        )

        return {
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "total_reviews": total_reviews,
            "ratings": ratings,
            "complaints": complaints,
            "completion_times": completion_times,
            "last_activity": last_activity,
        }

    def _completion_ratio(self, stats: dict) -> float:
        """CR = completed / total requests."""
        if stats["total_requests"] == 0:
            return 0.0
        return stats["completed_requests"] / stats["total_requests"]

    def _complaint_ratio(self, stats: dict) -> float:
        """CPR = complaints / total reviews."""
        if stats["total_reviews"] == 0:
            return 0.0
        return len(stats["complaints"]) / stats["total_reviews"]

    def _normalized_rating(self, stats: dict) -> float:
        """Average rating normalized to 0-1 scale (from 1-5)."""
        ratings = stats["ratings"]
        if not ratings:
            return 0.5  # neutral default
        avg = sum(ratings) / len(ratings)
        # Normalize from [1, 5] to [0, 1]
        return max(0.0, min(1.0, (avg - 1.0) / 4.0))

    def _verification_bonus(self, provider: ServiceProvider) -> float:
        """Binary bonus: 1.0 if verified, 0.0 if not."""
        return 1.0 if provider.is_verified else 0.0

    def _consistency_score(self, stats: dict) -> float:
        """
        ConsistencyScore = 1 − normalized_variance(completion_times)
        SOE Enhancement 5.
        """
        times = stats["completion_times"]
        if len(times) < 2:
            return 0.5  # neutral default for insufficient data

        mean_time = sum(times) / len(times)
        if mean_time == 0:
            return 1.0  # all instant completions

        # Compute variance
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        std_dev = math.sqrt(variance)

        # Normalize: coefficient of variation (std/mean), capped at 1.0
        cv = min(std_dev / mean_time, 1.0)

        # Consistency = 1 - CV
        return max(0.0, 1.0 - cv)

    def _escalation_penalty(self, stats: dict) -> float:
        """
        Penalty based on active complaint escalations.
        Ranges from 0.0 (no complaints) to 1.0 (severe).
        """
        complaints = stats["complaints"]
        total = stats["total_reviews"]

        if total == 0 or not complaints:
            return 0.0

        ratio = len(complaints) / total
        # Scale: 0-10% complaints = low penalty, 20%+ = high penalty
        return min(ratio * 2.0, 1.0)

    def _months_since_last_activity(self, stats: dict) -> float:
        """Calculate months of inactivity for temporal decay."""
        last_activity = stats.get("last_activity")
        if not last_activity:
            return 0.0

        # Ensure timezone awareness
        now = datetime.now(timezone.utc)
        if last_activity.tzinfo is None:
            from datetime import timezone as tz

            last_activity = last_activity.replace(tzinfo=tz.utc)

        delta = now - last_activity
        months = delta.days / 30.44  # average days per month

        return max(0.0, months)


class TrustScoreEngine(TrustEngine):
    """Backward-compatible alias for legacy imports."""

    pass
