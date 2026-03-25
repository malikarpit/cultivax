"""
26 march: Security Tests — Phase 6C

Tests for:
  - Abuse detection: action density threshold
  - Duplicate action detection: replay attack prevention
  - ML data poisoning defense: Z-score outlier exclusion
  - Timestamp clamping: future timestamps are clamped
  - Environment safety: prod DB host verification
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.security.guards import (
    clamp_device_timestamp,
    AbuseDetector,
    DataPoisoningGuard,
    verify_production_environment,
    get_rotation_policy,
    TIMESTAMP_TOLERANCE_MINUTES,
    ABUSE_ACTION_DENSITY_THRESHOLD,
)


# ===========================================================================
# Timestamp Clamping (MSDD 11.5)
# ===========================================================================

class TestTimestampClamping:
    """Device timestamps beyond tolerance are clamped to server time."""

    def test_normal_timestamp_not_clamped(self):
        """A timestamp within tolerance is returned unchanged."""
        now = datetime.now(timezone.utc)
        ts = now - timedelta(minutes=5)

        result, adjusted, _ = clamp_device_timestamp(ts, server_time=now)
        assert adjusted is False
        assert result == ts

    def test_future_timestamp_clamped(self):
        """A timestamp far in the future is clamped to server time."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=2)

        result, adjusted, adjustment = clamp_device_timestamp(future, server_time=now)
        assert adjusted is True
        assert result == now
        assert adjustment > 0

    def test_slightly_future_within_tolerance(self):
        """A timestamp within tolerance window is NOT clamped."""
        now = datetime.now(timezone.utc)
        slight_future = now + timedelta(minutes=TIMESTAMP_TOLERANCE_MINUTES - 1)

        result, adjusted, _ = clamp_device_timestamp(slight_future, server_time=now)
        assert adjusted is False

    def test_past_timestamp_not_clamped(self):
        """Past timestamps are never clamped."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=30)

        result, adjusted, _ = clamp_device_timestamp(past, server_time=now)
        assert adjusted is False


# ===========================================================================
# Abuse Detection (Patch 4.1)
# ===========================================================================

class TestAbuseDetection:
    """Action density and duplicate detection."""

    def test_normal_density_not_flagged(self):
        """10 actions in an hour → NOT flagged."""
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(minutes=i * 5) for i in range(10)]

        result = AbuseDetector.check_action_density(timestamps)
        assert result["is_flagged"] is False

    def test_high_density_flagged(self):
        """30 actions in 5 minutes → flagged."""
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(seconds=i * 10) for i in range(30)]

        result = AbuseDetector.check_action_density(timestamps)
        assert result["is_flagged"] is True
        assert result["density"] > ABUSE_ACTION_DENSITY_THRESHOLD

    def test_empty_actions_not_flagged(self):
        """Empty action list → not flagged."""
        result = AbuseDetector.check_action_density([])
        assert result["is_flagged"] is False

    def test_duplicate_actions_flagged(self):
        """Many identical actions → flagged as potential replay attack."""
        actions = [
            {"action_type": "irrigation", "crop_instance_id": "crop-1"}
            for _ in range(10)
        ]

        result = AbuseDetector.check_duplicate_actions(actions, duplicate_threshold=5)
        assert result["is_flagged"] is True

    def test_varied_actions_not_flagged(self):
        """Diverse actions → NOT flagged."""
        actions = [
            {"action_type": f"type_{i}", "crop_instance_id": f"crop-{i}"}
            for i in range(10)
        ]

        result = AbuseDetector.check_duplicate_actions(actions)
        assert result["is_flagged"] is False


# ===========================================================================
# ML Data Poisoning Defense (Patch 4.4)
# ===========================================================================

class TestDataPoisoningGuard:
    """Z-score outlier exclusion for training data."""

    def test_normal_data_no_exclusions(self):
        """Clean data within 3σ → no samples excluded."""
        values = [10.0, 11.0, 9.5, 10.5, 10.2, 9.8, 10.1, 9.9, 10.3, 10.0]

        clean, excluded, count = DataPoisoningGuard.filter_outliers(values)
        assert count == 0
        assert len(clean) == len(values)

    def test_outlier_excluded(self):
        """A value > 3σ from mean is excluded."""
        values = [10.0, 10.1, 9.9, 10.0, 10.2, 9.8, 10.0, 100.0]  # 100.0 is outlier

        clean, excluded_indices, count = DataPoisoningGuard.filter_outliers(values)
        assert count >= 1
        assert 7 in excluded_indices  # Index of 100.0
        assert 100.0 not in clean

    def test_too_few_samples_no_filtering(self):
        """Less than 5 samples → no filtering applied."""
        values = [1.0, 2.0, 100.0]

        clean, excluded, count = DataPoisoningGuard.filter_outliers(values)
        assert count == 0
        assert len(clean) == 3

    def test_constant_values_no_exclusions(self):
        """All identical values (stdev=0) → no exclusions."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0]

        clean, excluded, count = DataPoisoningGuard.filter_outliers(values)
        assert count == 0


# ===========================================================================
# Secrets Rotation Policy
# ===========================================================================

class TestSecretsRotationPolicy:
    """Rotation policy is properly documented."""

    def test_policy_contains_required_keys(self):
        """Policy has entries for JWT, DB password, and API keys."""
        policy = get_rotation_policy()
        assert "jwt_secret_key" in policy
        assert "database_password" in policy
        assert "api_keys" in policy

    def test_jwt_rotation_is_90_days(self):
        """JWT key rotation is set to 90 days."""
        policy = get_rotation_policy()
        assert policy["jwt_secret_key"]["rotation_days"] == 90
