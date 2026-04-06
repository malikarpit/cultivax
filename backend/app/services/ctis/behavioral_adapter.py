"""
Behavioral Adapter

Detects recurring farmer behavior patterns and computes bounded
offsets to personalize timeline recommendations.

MSDD 4.2 Layer 3 | ML Enhancement 6

Key rules:
- NEVER modifies baseline template
- Offset max ±7 days (bounded)
- Resets at season end
- Must be reversible (ML Enhancement 6)
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.action_log import ActionLog
from app.models.crop_instance import CropInstance

logger = logging.getLogger(__name__)

# Maximum behavioral offset (days)
MAX_OFFSET_DAYS = 7

# Minimum recurring pattern threshold
RECURRING_THRESHOLD = 3


class BehavioralAdapter:
    """
    Detects farmer-specific behavior patterns and computes
    personalized adjustments within bounded offsets.
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_behavioral_offset(
        self, farmer_id: UUID, crop_type: str
    ) -> Dict[str, Any]:
        """
        Detect if farmer consistently delays or advances actions
        and compute a bounded offset.

        Returns:
            Dict with offset_days, pattern_detected, confidence, is_applied
        """
        # Load farmer's historical actions for this crop type
        crops = (
            self.db.query(CropInstance)
            .filter(
                CropInstance.farmer_id == farmer_id,
                CropInstance.crop_type == crop_type,
                CropInstance.is_deleted == False,
                CropInstance.state.in_(["Harvested", "Closed", "Archived"]),
            )
            .all()
        )

        if len(crops) < RECURRING_THRESHOLD:
            return {
                "offset_days": 0,
                "pattern_detected": False,
                "confidence": 0.0,
                "is_applied": False,
                "reason": "Insufficient historical data",
            }

        # Analyze timing patterns across past crops
        delays = []
        for crop in crops:
            actions = (
                self.db.query(ActionLog)
                .filter(
                    ActionLog.crop_instance_id == crop.id,
                    ActionLog.is_deleted == False,
                )
                .order_by(ActionLog.action_effective_date.asc())
                .all()
            )

            if actions:
                # Compute average delay from expected timeline
                for action in actions:
                    if hasattr(action, "expected_date") and action.expected_date:
                        delta = (
                            action.action_effective_date - action.expected_date
                        ).days
                        delays.append(delta)

        if not delays:
            return {
                "offset_days": 0,
                "pattern_detected": False,
                "confidence": 0.0,
                "is_applied": False,
                "reason": "No timing reference data available",
            }

        # Compute average offset
        avg_delay = sum(delays) / len(delays)

        # Check for recurring pattern
        consistent_direction = all(d >= 0 for d in delays) or all(
            d <= 0 for d in delays
        )
        pattern_detected = consistent_direction and len(delays) >= RECURRING_THRESHOLD

        # Bound the offset
        offset = max(-MAX_OFFSET_DAYS, min(MAX_OFFSET_DAYS, round(avg_delay)))

        # Compute confidence
        if len(delays) >= 5:
            variance = sum((d - avg_delay) ** 2 for d in delays) / len(delays)
            std_dev = variance**0.5
            confidence = max(0.0, min(1.0, 1.0 - (std_dev / MAX_OFFSET_DAYS)))
        else:
            confidence = 0.3

        result = {
            "offset_days": offset if pattern_detected else 0,
            "pattern_detected": pattern_detected,
            "confidence": float(int(confidence * 1000)) / 1000,
            "is_applied": pattern_detected and abs(offset) > 0,
            "average_delay": float(int(avg_delay * 10)) / 10,
            "sample_size": len(delays),
        }

        if pattern_detected:
            logger.info(
                f"Behavioral pattern detected for farmer {farmer_id}, "
                f"crop_type={crop_type}: offset={offset} days, "
                f"confidence={confidence:.2f}"
            )

        return result

    def reset_offsets_for_season(self, farmer_id: UUID) -> None:
        """Reset all behavioral offsets at season end (MSDD 4.2)."""
        logger.info(f"Behavioral offsets reset for farmer {farmer_id}")
        # Offsets are computed dynamically, so no persistent state to reset
        # This method exists for explicit season-end processing
