"""
Crop Enhancements Module — 26 march: Phase 7C

Remaining enhancement implementations:
  - Trust decay mechanism for inactive providers
  - Provider exposure fairness ranking
  - Stage-aware alpha in stress smoothing
  - Action log compression for archived crops
  - Projected harvest date computation
"""

import logging
import math
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

logger = logging.getLogger(__name__)


# ===========================================================================
# 7C.1: Trust Decay for Inactive Providers
# ===========================================================================

# Already implemented in trust_engine.py via DECAY_FACTOR_PER_MONTH (0.98)
# This module provides the batch decay runner for scheduled execution.

DECAY_FACTOR_PER_MONTH = 0.98
INACTIVITY_THRESHOLD_DAYS = 90  # Start decaying after 90 days inactive


def batch_apply_trust_decay(db: Session) -> dict:
    """
    Batch job: apply trust decay to all providers inactive > 90 days.
    Run on a scheduled interval (e.g., weekly cron).

    Returns:
        {"decayed_count": int, "providers": list of dicts}
    """
    from datetime import datetime, timezone

    from app.models.service_provider import ServiceProvider

    cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_THRESHOLD_DAYS)

    inactive_providers = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.is_deleted == False,
            ServiceProvider.updated_at < cutoff,
            ServiceProvider.trust_score > 0.1,  # Don't decay already-low scores
        )
        .all()
    )

    results = []
    for provider in inactive_providers:
        months_inactive = (
            datetime.now(timezone.utc) - provider.updated_at
        ).days / 30.44
        decay = math.pow(DECAY_FACTOR_PER_MONTH, months_inactive)
        old_score = provider.trust_score or 0.5
        new_score = round(old_score * decay, 4)

        provider.trust_score = max(0.1, new_score)  # Floor at 0.1
        results.append(
            {
                "provider_id": str(provider.id),
                "old_score": old_score,
                "new_score": provider.trust_score,
                "months_inactive": round(months_inactive, 1),
            }
        )

    db.commit()
    logger.info(f"Trust decay applied to {len(results)} inactive providers")

    return {"decayed_count": len(results), "providers": results}


# ===========================================================================
# 7C.2: Provider Exposure Fairness
# ===========================================================================

MAX_TOP_PROVIDER_EXPOSURE = 0.70  # Top 3 providers shouldn't exceed 70% exposure


def compute_exposure_fairness(
    provider_request_counts: Dict[str, int],
    top_n: int = 3,
) -> dict:
    """
    Check if top N providers exceed the fairness threshold (70% of total requests).

    Args:
        provider_request_counts: {provider_id: request_count}
        top_n: Number of top providers to check

    Returns:
        {"fair": bool, "top_exposure": float, "details": dict}
    """
    total = sum(provider_request_counts.values())
    if total == 0:
        return {"fair": True, "top_exposure": 0.0, "details": {}}

    sorted_providers = sorted(
        provider_request_counts.items(), key=lambda x: x[1], reverse=True
    )

    top_providers = sorted_providers[:top_n]
    top_total = sum(count for _, count in top_providers)
    exposure = top_total / total

    is_fair = exposure <= MAX_TOP_PROVIDER_EXPOSURE

    if not is_fair:
        logger.warning(
            f"Exposure fairness violation: top {top_n} providers have "
            f"{exposure:.1%} exposure (threshold: {MAX_TOP_PROVIDER_EXPOSURE:.0%})"
        )

    return {
        "fair": is_fair,
        "top_exposure": round(exposure, 4),
        "threshold": MAX_TOP_PROVIDER_EXPOSURE,
        "top_providers": [
            {"provider_id": pid, "requests": count, "share": round(count / total, 4)}
            for pid, count in top_providers
        ],
    }


# ===========================================================================
# 7C.3: Stage-Aware Alpha in Stress Smoothing
# ===========================================================================

# Different growth stages have different stress sensitivity
STAGE_ALPHA = {
    "germination": 0.3,  # Low sensitivity — early days
    "seedling": 0.4,
    "vegetative": 0.5,  # Moderate
    "flowering": 0.7,  # High — critical stage
    "maturity": 0.6,
    "harvest": 0.3,  # Low — near end
}

DEFAULT_ALPHA = 0.5


def stage_aware_stress_smooth(
    current_stress: float,
    raw_stress: float,
    stage: Optional[str] = None,
) -> float:
    """
    Apply stage-aware exponential smoothing to stress scores.

    Formula: smoothed = α × raw + (1 − α) × current
    where α depends on the growth stage.

    Flowering stage α=0.7 → more sensitive to new readings.
    Germination α=0.3 → more stability, less reactivity.
    """
    alpha = STAGE_ALPHA.get(stage, DEFAULT_ALPHA) if stage else DEFAULT_ALPHA
    smoothed = alpha * raw_stress + (1 - alpha) * current_stress
    return round(max(0.0, min(100.0, smoothed)), 4)


# ===========================================================================
# 7C.4: Action Log Compression for Archived Crops
# ===========================================================================


def compress_action_logs(db: Session, crop_instance_id: UUID) -> dict:
    """
    Compress action logs for an archived crop by aggregating
    per-day actions into daily summaries.

    Preserves the original data in a JSONB summary but reduces
    row count by grouping same-day actions.

    Returns:
        {"original_count": int, "compressed_count": int, "ratio": float}
    """
    from app.models.action_log import ActionLog

    actions = (
        db.query(ActionLog)
        .filter(
            ActionLog.crop_instance_id == crop_instance_id,
            ActionLog.is_deleted == False,
        )
        .order_by(ActionLog.effective_date)
        .all()
    )

    if not actions:
        return {"original_count": 0, "compressed_count": 0, "ratio": 1.0}

    original_count = len(actions)

    # Group actions by date
    daily_groups: Dict[str, list] = {}
    for action in actions:
        day_key = str(action.effective_date) if action.effective_date else "unknown"
        daily_groups.setdefault(day_key, []).append(action)

    compressed_count = len(daily_groups)

    # For each group with > 1 action, soft-delete extras and store summary
    for day_key, group in daily_groups.items():
        if len(group) <= 1:
            continue

        # Keep the first action, mark others as compressed
        primary = group[0]
        summary = {
            "compressed": True,
            "original_count": len(group),
            "action_types": [a.action_type for a in group],
            "compressed_at": str(date.today()),
        }
        primary.metadata_json = {**(primary.metadata_json or {}), **summary}

        for extra in group[1:]:
            extra.is_deleted = True

    db.commit()

    ratio = round(compressed_count / original_count, 4) if original_count > 0 else 1.0
    logger.info(
        f"Compressed actions for crop {crop_instance_id}: "
        f"{original_count} → {compressed_count} ({ratio:.0%})"
    )

    return {
        "original_count": original_count,
        "compressed_count": compressed_count,
        "ratio": ratio,
    }


# ===========================================================================
# 7C.5: Projected Harvest Date Computation
# ===========================================================================

# Default crop duration in days (fallback if no rule template)
DEFAULT_CROP_DURATIONS = {
    "wheat": 120,
    "rice": 135,
    "cotton": 180,
    "sugarcane": 365,
    "maize": 100,
    "soybean": 90,
    "default": 120,
}


def compute_projected_harvest_date(
    sowing_date: date,
    crop_type: str,
    stage_offset_days: int = 0,
    stage_definitions: Optional[list] = None,
) -> dict:
    """
    Compute the projected harvest date based on sowing date and crop duration.

    Args:
        sowing_date: Date when the crop was sown
        crop_type: Type of crop
        stage_offset_days: Current drift from expected timeline
        stage_definitions: Optional stage definitions from rule template

    Returns:
        {"projected_date": str, "total_duration_days": int, "adjusted_by": int}
    """
    # Use rule template if available
    if stage_definitions:
        total_days = sum(
            s.get("duration_days", 0) for s in stage_definitions if isinstance(s, dict)
        )
    else:
        total_days = DEFAULT_CROP_DURATIONS.get(
            crop_type.lower(), DEFAULT_CROP_DURATIONS["default"]
        )

    # Adjust by current drift
    adjusted_days = total_days + stage_offset_days
    projected = sowing_date + timedelta(days=adjusted_days)

    return {
        "projected_date": projected.isoformat(),
        "total_duration_days": total_days,
        "adjusted_by": stage_offset_days,
        "crop_type": crop_type,
    }
