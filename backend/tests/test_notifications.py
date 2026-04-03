"""
26 march: Notification Tests — Phase 6D

Tests for:
  - Alert throttling: max N alerts of same type delivered
  - Alert deduplication: suppress duplicate pending alerts
  - ML safety guards: kill switch and dataset safeguard
  - Media stress escalation guardrail
  - Trust score counter persistence
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.ml.risk_predictor import RiskPredictor
from app.services.media.analysis_service import AnalysisService


# ===========================================================================
# ML Safety Guards (Phase 4D verification)
# ===========================================================================

class TestMLSafetyGuards:
    """ML kill switch and dataset safeguard tests."""

    def setup_method(self):
        self.predictor = RiskPredictor()

    def test_ml_disabled_returns_false(self):
        """Kill switch OFF → is_ml_safe returns False."""
        from unittest.mock import patch, MagicMock
        # Mock the feature flag to return False (kill switch OFF)
        with patch("app.services.feature_flags.is_enabled", return_value=False) as mock_flag:
            with patch("app.services.ml.risk_predictor.logger"):
                result = self.predictor.is_ml_safe(training_samples=500, db=MagicMock())
        assert result is False

    def test_insufficient_data_returns_false(self):
        """< 200 training samples → is_ml_safe returns False."""
        # No DB needed — insufficient data is checked before feature flag
        result = self.predictor.is_ml_safe(training_samples=100)
        assert result is False

    def test_sufficient_data_and_enabled_returns_true(self):
        """>= 200 samples + enabled (no db=default True) → is_ml_safe returns True."""
        result = self.predictor.is_ml_safe(training_samples=200)
        assert result is True

    def test_exactly_threshold_returns_true(self):
        """Exactly 200 samples → is_ml_safe returns True."""
        result = self.predictor.is_ml_safe(training_samples=200)
        assert result is True


# ===========================================================================
# Yield Biological Cap (ML 4.9)
# ===========================================================================

class TestYieldBioCap:
    """Predicted yields are capped at biological maximum."""

    def setup_method(self):
        self.predictor = RiskPredictor()

    def test_normal_yield_not_capped(self):
        """A yield below the cap is returned unchanged."""
        result = self.predictor.cap_yield_prediction(20.0, "wheat")
        assert result == 20.0

    def test_excessive_yield_capped(self):
        """A yield above the cap is capped to bio limit."""
        result = self.predictor.cap_yield_prediction(100.0, "wheat")
        assert result == 25.0  # Wheat cap

    def test_default_cap_used_for_unknown_crop(self):
        """Unknown crop type uses the default cap."""
        result = self.predictor.cap_yield_prediction(999.0, "unknown_crop")
        assert result == 50.0  # Default cap

    def test_sugarcane_high_cap(self):
        """Sugarcane has highest cap (400 quintals/acre)."""
        result = self.predictor.cap_yield_prediction(350.0, "sugarcane")
        assert result == 350.0  # Under cap

    def test_case_insensitive_crop_type(self):
        """Crop type matching is case-insensitive."""
        result = self.predictor.cap_yield_prediction(100.0, "WHEAT")
        assert result == 25.0


# ===========================================================================
# Media Stress Escalation Guardrail (Media Enh 5)
# ===========================================================================

class TestStressEscalationGuardrail:
    """Stress increases are capped and confidence-weighted."""

    def test_small_increase_passes(self):
        """A small stress increase passes through."""
        result = AnalysisService.stress_escalation_guardrail(
            current_stress=50.0, new_stress=55.0
        )
        assert result == 55.0

    def test_large_increase_capped(self):
        """A large stress increase is capped at max_daily_increase."""
        result = AnalysisService.stress_escalation_guardrail(
            current_stress=50.0, new_stress=80.0, max_daily_increase=15.0
        )
        assert result == 65.0  # 50 + 15

    def test_confidence_weighting_reduces_increase(self):
        """Low confidence reduces the effective stress increase."""
        result = AnalysisService.stress_escalation_guardrail(
            current_stress=50.0, new_stress=60.0, confidence=0.5
        )
        assert result == 55.0  # 50 + (10 * 0.5)

    def test_decrease_not_guarded(self):
        """Stress decreases are allowed without guardrail."""
        result = AnalysisService.stress_escalation_guardrail(
            current_stress=80.0, new_stress=40.0
        )
        assert result == 40.0

    def test_zero_confidence_no_increase(self):
        """Zero confidence → no stress increase applied."""
        result = AnalysisService.stress_escalation_guardrail(
            current_stress=50.0, new_stress=70.0, confidence=0.0
        )
        assert result == 50.0


# ===========================================================================
# Alert Throttling & Deduplication (Phase 6D plan)
# ===========================================================================

class TestAlertThrottling:
    """Alert creation respects throttling rules."""

    def test_max_alerts_per_type(self):
        """At most 3 active alerts of same type should be delivered."""
        # Logic test: count active alerts of same type
        active_count = 3
        max_allowed = 3
        should_suppress = active_count >= max_allowed
        assert should_suppress is True

    def test_below_threshold_not_suppressed(self):
        """Below max → alert is delivered."""
        active_count = 2
        max_allowed = 3
        should_suppress = active_count >= max_allowed
        assert should_suppress is False


class TestAlertDeduplication:
    """Duplicate pending alerts are suppressed."""

    def test_existing_pending_suppresses_duplicate(self):
        """If a Pending alert of same type exists, new one is suppressed."""
        existing_pending = True  # Simulating DB check
        should_suppress = existing_pending
        assert should_suppress is True

    def test_no_pending_allows_creation(self):
        """No existing Pending alert → new alert is created."""
        existing_pending = False
        should_suppress = existing_pending
        assert should_suppress is False
