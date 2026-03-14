"""
Deviation Profile Tracker — MSDD 1.9.1

Tracks consecutive deviations from the expected crop timeline,
computes trend slope, and flags recurring deviation patterns.

TDD 2.3.4 | MSDD 1.9.1
"""

from sqlalchemy.orm import Session  # type: ignore
from uuid import UUID
from typing import Optional
import logging

from app.models.deviation import DeviationProfile  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RECURRING_PATTERN_THRESHOLD = 3   # Flag if consecutive deviations >= 3
TREND_SLOPE_WARNING = 0.5         # Slope above this indicates worsening trend


class DeviationUpdate:
    """Result of a deviation profile update."""

    def __init__(
        self,
        consecutive_count: int,
        trend_slope: float,
        is_recurring: bool,
        cumulative_days: int,
        last_type: Optional[str],
        last_days: int,
    ):
        self.consecutive_count = consecutive_count
        self.trend_slope = float(round(trend_slope, 4))  # type: ignore
        self.is_recurring = is_recurring
        self.cumulative_days = cumulative_days
        self.last_type = last_type
        self.last_days = last_days

    def to_dict(self) -> dict:
        return {
            "consecutive_deviation_count": self.consecutive_count,
            "deviation_trend_slope": self.trend_slope,
            "recurring_pattern_flag": self.is_recurring,
            "cumulative_deviation_days": self.cumulative_days,
            "last_deviation_type": self.last_type,
            "last_deviation_days": self.last_days,
        }

    @property
    def severity(self) -> str:
        if self.consecutive_count >= 5:
            return "critical"
        elif self.consecutive_count >= RECURRING_PATTERN_THRESHOLD:
            return "warning"
        elif self.consecutive_count >= 1:
            return "minor"
        return "none"


class DeviationTracker:
    """
    Tracks and updates deviation profiles for crop instances.

    Deviation = farmer actions happening earlier or later than expected.
    Consecutive deviations are tracked to detect recurring patterns.
    """

    def __init__(self, db: Session):
        self.db = db

    def update_deviation_profile(
        self,
        crop_instance_id: UUID,
        current_deviation_days: int,
        deviation_type: Optional[str] = None,
    ) -> DeviationUpdate:
        """
        Update the deviation profile for a crop instance.

        Args:
            crop_instance_id: The crop to update
            current_deviation_days: How many days off from expected (positive = late)
            deviation_type: "early" or "late" (auto-detected if not provided)

        Returns:
            DeviationUpdate with the new profile state
        """

        # Load existing profile
        profile = (
            self.db.query(DeviationProfile)
            .filter(DeviationProfile.crop_instance_id == crop_instance_id)
            .first()
        )

        if not profile:
            logger.warning(
                f"No deviation profile found for crop {crop_instance_id}"
            )
            return DeviationUpdate(0, 0.0, False, 0, None, 0)

        # Auto-detect deviation type
        if deviation_type is None:
            if current_deviation_days > 0:
                deviation_type = "late"
            elif current_deviation_days < 0:
                deviation_type = "early"
            else:
                # No deviation — reset consecutive counter
                return self._reset_consecutive(profile)

        abs_days = abs(current_deviation_days)

        if abs_days == 0:
            return self._reset_consecutive(profile)

        # Increment consecutive deviation counter
        profile.consecutive_deviation_count += 1
        profile.cumulative_deviation_days += abs_days
        profile.last_deviation_type = deviation_type
        profile.last_deviation_days = abs_days

        # Compute trend slope (deviation rate over time)
        if profile.cumulative_deviation_days > 0:
            profile.deviation_trend_slope = (
                profile.consecutive_deviation_count
                / max(profile.cumulative_deviation_days, 1)
            )

        # Flag recurring pattern
        profile.recurring_pattern_flag = (
            profile.consecutive_deviation_count >= RECURRING_PATTERN_THRESHOLD
        )

        self.db.commit()

        update = DeviationUpdate(
            consecutive_count=profile.consecutive_deviation_count,
            trend_slope=profile.deviation_trend_slope,
            is_recurring=profile.recurring_pattern_flag,
            cumulative_days=profile.cumulative_deviation_days,
            last_type=profile.last_deviation_type,
            last_days=profile.last_deviation_days,
        )

        logger.info(
            f"Deviation update for crop {crop_instance_id}: "
            f"consecutive={update.consecutive_count}, "
            f"type={deviation_type}, days={abs_days}, "
            f"recurring={update.is_recurring}, severity={update.severity}"
        )

        return update

    def get_deviation_summary(self, crop_instance_id: UUID) -> Optional[dict]:
        """Get the current deviation profile summary."""
        profile = (
            self.db.query(DeviationProfile)
            .filter(DeviationProfile.crop_instance_id == crop_instance_id)
            .first()
        )

        if not profile:
            return None

        return {
            "consecutive_deviation_count": profile.consecutive_deviation_count,
            "deviation_trend_slope": profile.deviation_trend_slope,
            "recurring_pattern_flag": profile.recurring_pattern_flag,
            "cumulative_deviation_days": profile.cumulative_deviation_days,
            "last_deviation_type": profile.last_deviation_type,
            "last_deviation_days": profile.last_deviation_days,
        }

    def _reset_consecutive(self, profile: DeviationProfile) -> DeviationUpdate:
        """Reset consecutive counter when action is on-track."""
        profile.consecutive_deviation_count = 0
        self.db.commit()

        return DeviationUpdate(
            consecutive_count=0,
            trend_slope=profile.deviation_trend_slope,
            is_recurring=profile.recurring_pattern_flag,
            cumulative_days=profile.cumulative_deviation_days,
            last_type=profile.last_deviation_type,
            last_days=profile.last_deviation_days,
        )
