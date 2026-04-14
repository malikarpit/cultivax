"""
ML Feedback Aggregator — FR-10

Aggregates farmer feedback on ML predictions to adjust confidence
and improve recommendation accuracy over time.

Collects rejection/confirmation rates per model version and computes
a confidence adjustment factor that downstream predictors use to
scale their output confidence.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ml_feedback import MLFeedback

logger = logging.getLogger(__name__)

# Minimum feedback records before adjustments take effect
MIN_FEEDBACK_FOR_ADJUSTMENT = 5

# Maximum confidence reduction from feedback
MAX_CONFIDENCE_PENALTY = 0.5


class FeedbackAggregator:
    """
    Aggregates farmer feedback on ML predictions.

    FR-10: "System shall improve recommendation accuracy by learning
           from user feedback."

    This provides the feedback→confidence loop. When farmers consistently
    reject a model's predictions, the confidence factor is reduced,
    causing downstream systems to treat the model's output as less certain.
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_adjustment_factor(self, model_version: str) -> float:
        """
        Compute a confidence adjustment factor based on farmer feedback.

        Returns a value in [0.5, 1.0]:
          - 1.0 = no adjustment (insufficient data or all confirmed)
          - 0.5 = maximum penalty (high rejection rate)
        """
        feedbacks = (
            self.db.query(MLFeedback)
            .filter(
                MLFeedback.model_version == model_version,
                MLFeedback.is_deleted == False,
            )
            .all()
        )

        if len(feedbacks) < MIN_FEEDBACK_FOR_ADJUSTMENT:
            logger.debug(
                f"Insufficient feedback ({len(feedbacks)} < {MIN_FEEDBACK_FOR_ADJUSTMENT})"
                f" for model {model_version} — no adjustment applied"
            )
            return 1.0

        confirmed = sum(
            1 for f in feedbacks if f.feedback_type in ("confirmed", "partially_correct")
        )
        rejected = sum(1 for f in feedbacks if f.feedback_type == "rejected")
        total = len(feedbacks)

        confirmation_rate = confirmed / total
        rejection_rate = rejected / total

        # Linear penalty: 0% rejection → 1.0, 100% rejection → 0.5
        adjustment = 1.0 - (rejection_rate * MAX_CONFIDENCE_PENALTY)
        adjustment = max(1.0 - MAX_CONFIDENCE_PENALTY, min(1.0, adjustment))

        logger.info(
            f"Feedback adjustment for {model_version}: "
            f"confirmed={confirmed}, rejected={rejected}, total={total}, "
            f"factor={adjustment:.3f}"
        )
        return round(adjustment, 4)

    def get_feedback_summary(self, model_version: Optional[str] = None) -> dict:
        """
        Return a human-readable feedback summary for the admin dashboard.
        """
        query = self.db.query(MLFeedback).filter(MLFeedback.is_deleted == False)
        if model_version:
            query = query.filter(MLFeedback.model_version == model_version)

        feedbacks = query.all()

        total = len(feedbacks)
        if total == 0:
            return {
                "model_version": model_version or "all",
                "total_feedback": 0,
                "confirmed": 0,
                "rejected": 0,
                "partially_correct": 0,
                "confirmation_rate": None,
                "adjustment_factor": 1.0,
            }

        confirmed = sum(1 for f in feedbacks if f.feedback_type == "confirmed")
        rejected = sum(1 for f in feedbacks if f.feedback_type == "rejected")
        partial = sum(1 for f in feedbacks if f.feedback_type == "partially_correct")

        return {
            "model_version": model_version or "all",
            "total_feedback": total,
            "confirmed": confirmed,
            "rejected": rejected,
            "partially_correct": partial,
            "confirmation_rate": round(confirmed / total, 4) if total > 0 else None,
            "adjustment_factor": (
                self.compute_adjustment_factor(model_version)
                if model_version
                else 1.0
            ),
        }
