"""
Marketplace Fraud Detection Engine

Detects suspicious patterns in service reviews and provider behavior.

MSDD Enhancement 8 | SOE Enhancement 8
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.abuse_flag import AbuseFlag
from app.models.service_provider import ServiceProvider
from app.models.service_review import ServiceReview

logger = logging.getLogger(__name__)

# Fraud detection thresholds
SAME_REVIEWER_THRESHOLD = 3  # Flag if same reviewer reviews provider N+ times
RATING_SPIKE_STD_DEV = 1.5  # Flag if rating std_dev in 7 days exceeds this
RATING_SPIKE_WINDOW_DAYS = 7
MIN_REVIEWS_FOR_ANALYSIS = 5


class FraudDetector:
    """
    Multi-signal fraud detection for the service marketplace.

    Checks:
    1. Review pattern anomaly — same reviewer for same provider
    2. Sudden rating spike — abnormal std_dev in short window
    3. IP correlation — between reviewer and provider (future)
    4. Timing anomaly — multiple reviews in suspiciously short periods
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_fraud(self, provider_id: UUID) -> Dict[str, Any]:
        """
        Run all fraud detection checks for a provider.

        Returns:
            Dict with is_flagged, fraud_signals, confidence, recommendations
        """
        signals = []

        # Check 1: Review pattern anomaly
        pattern_result = self._check_review_pattern(provider_id)
        if pattern_result["flagged"]:
            signals.append(pattern_result)

        # Check 2: Rating spike detection
        spike_result = self._check_rating_spike(provider_id)
        if spike_result["flagged"]:
            signals.append(spike_result)

        # Check 3: Timing anomaly
        timing_result = self._check_timing_anomaly(provider_id)
        if timing_result["flagged"]:
            signals.append(timing_result)

        is_flagged = len(signals) > 0
        confidence = min(1.0, len(signals) * 0.35)

        recommendations: List[str] = []

        result: Dict[str, Any] = {
            "provider_id": str(provider_id),
            "is_flagged": is_flagged,
            "fraud_signals": signals,
            "signal_count": len(signals),
            "confidence": float(int(float(confidence) * 1000)) / 1000,
            "recommendations": recommendations,
        }

        if is_flagged:
            recommendations.append("Reduce trust weight for this provider")
            recommendations.append("Flag for manual admin review")
            if confidence > 0.6:
                recommendations.append(
                    "Consider temporary suspension pending investigation"
                )

            # Create abuse flag
            self._create_abuse_flag(provider_id, result)

            logger.warning(
                f"Fraud signals detected for provider {provider_id}: "
                f"{len(signals)} signals, confidence={confidence:.2f}"
            )

        return result

    def _check_review_pattern(self, provider_id: UUID) -> Dict[str, Any]:
        """Check if same reviewer has reviewed this provider multiple times."""
        reviews = (
            self.db.query(ServiceReview)
            .filter(
                ServiceReview.provider_id == provider_id,
                ServiceReview.is_deleted == False,
            )
            .all()
        )

        reviewer_counts: Dict[str, int] = {}
        for review in reviews:
            reviewer_key = str(review.reviewer_id)
            reviewer_counts[reviewer_key] = reviewer_counts.get(reviewer_key, 0) + 1

        repeat_reviewers = {
            k: v for k, v in reviewer_counts.items() if v >= SAME_REVIEWER_THRESHOLD
        }

        return {
            "check": "review_pattern_anomaly",
            "flagged": len(repeat_reviewers) > 0,
            "details": {
                "repeat_reviewers": len(repeat_reviewers),
                "max_reviews_by_single": (
                    max(reviewer_counts.values()) if reviewer_counts else 0
                ),
            },
        }

    def _check_rating_spike(self, provider_id: UUID) -> Dict[str, Any]:
        """Check for sudden rating spike in a short window."""
        window_start = datetime.now(timezone.utc) - timedelta(
            days=RATING_SPIKE_WINDOW_DAYS
        )

        recent_reviews = (
            self.db.query(ServiceReview)
            .filter(
                ServiceReview.provider_id == provider_id,
                ServiceReview.created_at >= window_start,
                ServiceReview.is_deleted == False,
            )
            .all()
        )

        if len(recent_reviews) < MIN_REVIEWS_FOR_ANALYSIS:
            return {"check": "rating_spike", "flagged": False, "details": {}}

        ratings = [float(r.rating) for r in recent_reviews]
        avg = sum(ratings) / len(ratings)
        variance = sum((r - avg) ** 2 for r in ratings) / len(ratings)
        std_dev = variance**0.5

        return {
            "check": "rating_spike",
            "flagged": std_dev > RATING_SPIKE_STD_DEV,
            "details": {
                "recent_count": len(recent_reviews),
                "avg_rating": float(int(avg * 100)) / 100,
                "std_dev": float(int(std_dev * 1000)) / 1000,
                "threshold": RATING_SPIKE_STD_DEV,
            },
        }

    def _check_timing_anomaly(self, provider_id: UUID) -> Dict[str, Any]:
        """Check for suspiciously rapid review submissions."""
        reviews = (
            self.db.query(ServiceReview)
            .filter(
                ServiceReview.provider_id == provider_id,
                ServiceReview.is_deleted == False,
            )
            .order_by(ServiceReview.created_at.asc())
            .all()
        )

        if len(reviews) < 3:
            return {"check": "timing_anomaly", "flagged": False, "details": {}}

        # Check for clusters of reviews within 1 hour
        cluster_list: list[int] = []
        for i in range(len(reviews) - 2):
            time_span = (
                reviews[i + 2].created_at - reviews[i].created_at
            ).total_seconds()
            if time_span < 3600:  # 3 reviews within 1 hour
                cluster_list.append(1)

        rapid_cluster_count: int = len(cluster_list)

        return {
            "check": "timing_anomaly",
            "flagged": rapid_cluster_count > 0,
            "details": {
                "rapid_clusters": rapid_cluster_count,
                "total_reviews": len(reviews),
            },
        }

    def _create_abuse_flag(self, provider_id: UUID, result: Dict[str, Any]) -> None:
        """Create an abuse flag record for admin review.

        AbuseFlag.farmer_id refers to the flagged user's account. For provider
        fraud, we resolve the provider's user_id to populate this field.
        The entity context (provider_id, entity_type) is stored in details.
        """
        from app.models.service_provider import ServiceProvider

        provider = (
            self.db.query(ServiceProvider)
            .filter(
                ServiceProvider.id == provider_id,
                ServiceProvider.is_deleted == False,
            )
            .first()
        )

        if not provider:
            logger.warning(
                f"Cannot create AbuseFlag — ServiceProvider {provider_id} not found"
            )
            return

        enriched_details = {
            **result,
            "entity_type": "service_provider",
            "entity_id": str(provider_id),
        }

        flag = AbuseFlag(
            farmer_id=provider.user_id,  # user account behind the provider
            flag_type="marketplace_fraud",
            severity="high" if result["confidence"] > 0.6 else "medium",
            anomaly_score=result.get("confidence", 0.0),
            details=enriched_details,
        )
        self.db.add(flag)
