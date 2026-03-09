"""
Drift Enforcement Service

Clamps stage_offset to max_allowed_drift per stage to prevent
crop instances from drifting too far from expected timelines.

MSDD 1.9 | TDD 4.5
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default maximum drift limits per state (days)
DEFAULT_DRIFT_LIMITS = {
    "Created": 7,
    "Active": 14,
    "Delayed": 21,
    "AtRisk": 28,
    "ReadyToHarvest": 14,
}

# Maximum absolute drift cap
MAX_ABSOLUTE_DRIFT = 30


class DriftEnforcer:
    """
    Enforces timeline drift constraints on crop instances.

    Drift is the deviation (in days) between expected stage progression
    and actual stage progression. The enforcer clamps this drift to
    prevent excessive deviation from the crop rule template.
    """

    def __init__(self, custom_limits: Optional[Dict[str, int]] = None):
        self.drift_limits = custom_limits or DEFAULT_DRIFT_LIMITS

    def enforce_drift(
        self,
        current_state: str,
        stage_offset_days: int,
        current_day_number: int,
        expected_day_number: int,
    ) -> Dict[str, Any]:
        """
        Enforce drift constraints on a crop instance.

        Args:
            current_state: Current lifecycle state
            stage_offset_days: Current stage offset in days
            current_day_number: Actual day number
            expected_day_number: Expected day number per template

        Returns:
            Dict with clamped_offset, was_clamped, max_allowed, drift_ratio
        """
        max_allowed = self.drift_limits.get(current_state, MAX_ABSOLUTE_DRIFT)

        # Compute actual drift
        actual_drift = current_day_number - expected_day_number

        # Clamp the offset
        was_clamped = False
        clamped_offset = stage_offset_days

        if abs(stage_offset_days) > max_allowed:
            was_clamped = True
            if stage_offset_days > 0:
                clamped_offset = max_allowed
            else:
                clamped_offset = -max_allowed

        # Also enforce absolute cap
        if abs(clamped_offset) > MAX_ABSOLUTE_DRIFT:
            was_clamped = True
            clamped_offset = MAX_ABSOLUTE_DRIFT if clamped_offset > 0 else -MAX_ABSOLUTE_DRIFT

        # Drift ratio (0-1, how close to max drift)
        drift_ratio = abs(clamped_offset) / max_allowed if max_allowed > 0 else 0.0
        drift_ratio = min(1.0, drift_ratio)

        result = {
            "original_offset": stage_offset_days,
            "clamped_offset": clamped_offset,
            "was_clamped": was_clamped,
            "max_allowed": max_allowed,
            "actual_drift": actual_drift,
            "drift_ratio": float(int(drift_ratio * 10000)) / 10000,
            "drift_severity": self._classify_severity(drift_ratio),
        }

        if was_clamped:
            logger.warning(
                f"Drift clamped: offset {stage_offset_days} → {clamped_offset} "
                f"(max={max_allowed}, state={current_state})"
            )

        return result

    def _classify_severity(self, drift_ratio: float) -> str:
        """Classify drift severity based on ratio to max allowed."""
        if drift_ratio < 0.3:
            return "low"
        elif drift_ratio < 0.6:
            return "moderate"
        elif drift_ratio < 0.85:
            return "high"
        else:
            return "critical"

    def check_drift_alert(
        self, drift_ratio: float, consecutive_drift_days: int
    ) -> Optional[str]:
        """
        Determine if a drift alert should be generated.
        Returns alert type or None.
        """
        if drift_ratio >= 0.85 and consecutive_drift_days >= 5:
            return "critical_drift"
        elif drift_ratio >= 0.6 and consecutive_drift_days >= 3:
            return "high_drift_warning"
        elif drift_ratio >= 0.3 and consecutive_drift_days >= 7:
            return "moderate_drift_notice"
        return None
