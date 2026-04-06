"""
Security Guards — Data Integrity & Abuse Detection

Phase 5B hardening modules:
  - Offline timestamp clamping (MSDD 11.5)
  - Abuse detection (Patch 4.1)
  - ML data poisoning defense (Patch 4.4)

26 march: Phase 5C environment safety:
  - Production DB host verification (Patch 5.3)
  - Secrets rotation policy documentation
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 5B: Offline Timestamp Clamping (MSDD 11.5)
# ---------------------------------------------------------------------------

TIMESTAMP_TOLERANCE_MINUTES = 10


def clamp_device_timestamp(
    device_timestamp: datetime,
    server_time: Optional[datetime] = None,
    tolerance_minutes: int = TIMESTAMP_TOLERANCE_MINUTES,
) -> tuple:
    """
    Clamp a device-reported timestamp if it exceeds server time + tolerance.

    Returns:
        (clamped_timestamp, was_adjusted: bool, adjustment_seconds: float)
    """
    if server_time is None:
        server_time = datetime.now(timezone.utc)

    # Ensure both are timezone-aware
    if device_timestamp.tzinfo is None:
        device_timestamp = device_timestamp.replace(tzinfo=timezone.utc)
    if server_time.tzinfo is None:
        server_time = server_time.replace(tzinfo=timezone.utc)

    max_allowed = server_time + timedelta(minutes=tolerance_minutes)

    if device_timestamp > max_allowed:
        adjustment = (device_timestamp - server_time).total_seconds()
        logger.warning(
            f"Device timestamp clamped: {device_timestamp.isoformat()} → "
            f"{server_time.isoformat()} (adjustment: {adjustment:.1f}s)"
        )
        return server_time, True, adjustment

    return device_timestamp, False, 0.0


# ---------------------------------------------------------------------------
# 5B: Abuse Detection (Patch 4.1)
# ---------------------------------------------------------------------------

ABUSE_ACTION_DENSITY_THRESHOLD = 20  # Max actions per hour before flagging


class AbuseDetector:
    """
    Detects abuse patterns in farmer action submissions.

    Flags:
      - High action density (>20 actions/hour)
      - Repeated identical actions (potential replay attack)
      - Unusual device patterns
    """

    @staticmethod
    def check_action_density(
        action_timestamps: List[datetime],
        threshold: int = ABUSE_ACTION_DENSITY_THRESHOLD,
    ) -> dict:
        """
        Check if action density exceeds threshold (Patch 4.1).

        Args:
            action_timestamps: List of action timestamps within a batch
            threshold: Max allowed actions per hour

        Returns:
            Dict with is_flagged, density, and details
        """
        if not action_timestamps:
            return {"is_flagged": False, "density": 0, "reason": None}

        # Sort timestamps
        sorted_ts = sorted(action_timestamps)

        # Count actions within any 1-hour sliding window
        max_density = 0
        for i, ts in enumerate(sorted_ts):
            window_end = ts + timedelta(hours=1)
            count = sum(1 for t in sorted_ts[i:] if t <= window_end)
            max_density = max(max_density, count)

        is_flagged = max_density > threshold
        if is_flagged:
            logger.warning(
                f"Abuse flag: action density {max_density} exceeds "
                f"threshold {threshold} actions/hour"
            )

        return {
            "is_flagged": is_flagged,
            "density": max_density,
            "reason": (
                f"Action density {max_density}/hr exceeds {threshold}/hr"
                if is_flagged
                else None
            ),
        }

    @staticmethod
    def check_duplicate_actions(
        actions: List[dict],
        duplicate_threshold: int = 5,
    ) -> dict:
        """
        Check for repeated identical actions (potential replay attack).

        Args:
            actions: List of action dicts with action_type and metadata
            duplicate_threshold: Max identical actions before flagging

        Returns:
            Dict with is_flagged and duplicate groups
        """
        from collections import Counter

        # Hash each action by type + key metadata
        hashes = []
        for a in actions:
            key = f"{a.get('action_type', '')}:{a.get('crop_instance_id', '')}"
            hashes.append(key)

        counts = Counter(hashes)
        duplicates = {k: v for k, v in counts.items() if v > duplicate_threshold}

        is_flagged = len(duplicates) > 0
        if is_flagged:
            logger.warning(f"Abuse flag: duplicate actions detected — {duplicates}")

        return {
            "is_flagged": is_flagged,
            "duplicates": duplicates,
            "reason": (
                f"Duplicate action groups: {list(duplicates.keys())}"
                if is_flagged
                else None
            ),
        }


# ---------------------------------------------------------------------------
# 5B: ML Data Poisoning Defense (Patch 4.4)
# ---------------------------------------------------------------------------


class DataPoisoningGuard:
    """
    Z-score outlier exclusion for ML training data (Patch 4.4).
    Skips samples with features > 3σ from mean.
    """

    @staticmethod
    def filter_outliers(
        values: List[float],
        z_threshold: float = 3.0,
    ) -> tuple:
        """
        Filter outliers using Z-score.

        Returns:
            (clean_values, excluded_indices, excluded_count)
        """
        if len(values) < 5:
            # Too few samples for meaningful Z-score
            return values, [], 0

        import statistics

        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        if stdev == 0:
            return values, [], 0

        clean = []
        excluded_indices = []
        for i, v in enumerate(values):
            z = abs(v - mean) / stdev
            if z > z_threshold:
                excluded_indices.append(i)
                logger.info(f"ML poisoning guard: excluded sample {i} (z={z:.2f})")
            else:
                clean.append(v)

        # Fallback for highly skewed small samples where mean/stdev can be pulled
        # by an extreme value enough that the classic z-score misses it.
        if not excluded_indices:
            median = statistics.median(values)
            abs_dev = [abs(v - median) for v in values]
            mad = statistics.median(abs_dev)
            if mad > 0:
                robust_threshold = 3.5
                robust_excluded = []
                for i, v in enumerate(values):
                    modified_z = 0.6745 * abs(v - median) / mad
                    if modified_z > robust_threshold:
                        robust_excluded.append(i)
                        logger.info(
                            f"ML poisoning guard: excluded sample {i} "
                            f"(modified_z={modified_z:.2f})"
                        )

                if robust_excluded:
                    excluded_set = set(robust_excluded)
                    clean = [v for i, v in enumerate(values) if i not in excluded_set]
                    excluded_indices = robust_excluded

        return clean, excluded_indices, len(excluded_indices)


# ---------------------------------------------------------------------------
# 5C: Environment Safety (Patch 5.3)
# ---------------------------------------------------------------------------


def verify_production_environment() -> bool:
    """
    Startup check: if ENV=production, verify DB host matches prod allowlist.
    Aborts if a dev/local DB is detected in production (Patch 5.3).

    Returns:
        True if safe, raises RuntimeError if unsafe.
    """
    from urllib.parse import urlparse

    from app.config import settings

    if settings.APP_ENV != "production":
        logger.info(f"Environment: {settings.APP_ENV} — skipping prod DB check")
        return True

    # Parse the DB URL to extract host
    parsed = urlparse(settings.DATABASE_URL)
    db_host = parsed.hostname or ""

    # Check against prod allowlist
    allowed_hosts = settings.prod_db_hosts
    if not allowed_hosts:
        logger.warning(
            "Production environment but no PROD_DB_HOST_ALLOWLIST configured"
        )
        return True  # No allowlist = skip check (but warn)

    dev_indicators = ["localhost", "127.0.0.1", "host.docker.internal", "db"]
    if db_host in dev_indicators or db_host not in allowed_hosts:
        error_msg = (
            f"PRODUCTION SAFETY ABORT: DB host '{db_host}' is not in the "
            f"prod allowlist {allowed_hosts}. Refusing to start."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Production DB host '{db_host}' verified against allowlist ✓")
    return True


# ---------------------------------------------------------------------------
# 5C: Secrets Rotation Policy (MSDD Enh Sec 9)
# ---------------------------------------------------------------------------

SECRETS_ROTATION_POLICY = {
    "jwt_secret_key": {
        "rotation_days": 90,
        "description": "JWT signing key — rotate every 90 days",
    },
    "database_password": {
        "rotation_days": 180,
        "description": "PostgreSQL password — rotate every 180 days",
    },
    "api_keys": {
        "rotation_days": 365,
        "description": "Third-party API keys — rotate annually",
    },
}


def get_rotation_policy() -> dict:
    """Return the secrets rotation policy for documentation/auditing."""
    return SECRETS_ROTATION_POLICY
