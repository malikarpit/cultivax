"""
ML Module Tests

Tests for:
- RiskPredictor  — rule-based risk prediction with confidence propagation
- ModelRegistry  — model version lifecycle (register, activate, query)

"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.ml.risk_predictor import RiskPredictor, RiskPrediction, MODEL_VERSION


# ═══════════════════════════════════════════════════════════════════════
# RiskPredictor Tests
# ═══════════════════════════════════════════════════════════════════════


class TestRiskPrediction:
    """Tests for the RiskPrediction data class."""

    def test_prediction_clamps_values(self):
        """Values outside 0-1 are clamped."""
        pred = RiskPrediction(
            prediction_value=1.5,
            confidence_score=-0.2,
            data_sufficiency_index=2.0,
        )
        assert pred.prediction_value == 1.0
        assert pred.confidence_score == 0.0
        assert pred.data_sufficiency_index == 1.0

    def test_risk_adjusted_calculation(self):
        """risk_adjusted = prediction_value × confidence_score."""
        pred = RiskPrediction(
            prediction_value=0.8,
            confidence_score=0.5,
            data_sufficiency_index=0.9,
        )
        assert abs(pred.risk_adjusted - 0.4) < 0.01

    def test_risk_labels(self):
        """Verify all risk label thresholds."""
        # critical: >= 0.8
        assert RiskPrediction(0.85, 0.5, 0.5).risk_label == "critical"
        # high: >= 0.6
        assert RiskPrediction(0.65, 0.5, 0.5).risk_label == "high"
        # moderate: >= 0.4
        assert RiskPrediction(0.45, 0.5, 0.5).risk_label == "moderate"
        # low: >= 0.2
        assert RiskPrediction(0.25, 0.5, 0.5).risk_label == "low"
        # minimal: < 0.2
        assert RiskPrediction(0.10, 0.5, 0.5).risk_label == "minimal"

    def test_recommendation_tone(self):
        """High confidence → assertive, low → tentative."""
        assert RiskPrediction(0.5, 0.9, 0.5).recommendation_tone == "assertive"
        assert RiskPrediction(0.5, 0.6, 0.5).recommendation_tone == "moderate"
        assert RiskPrediction(0.5, 0.3, 0.5).recommendation_tone == "tentative"

    def test_to_dict_fields(self):
        """Serialized dict has all required fields."""
        pred = RiskPrediction(0.5, 0.6, 0.7)
        d = pred.to_dict()
        assert "prediction_value" in d
        assert "confidence_score" in d
        assert "data_sufficiency_index" in d
        assert "risk_adjusted" in d
        assert "risk_label" in d
        assert "model_version" in d
        assert "generated_at" in d

    def test_model_version(self):
        """Default model version is the module constant."""
        pred = RiskPrediction(0.5, 0.5, 0.5)
        assert pred.model_version == MODEL_VERSION


class TestRiskPredictor:
    """Tests for the RiskPredictor rule-based engine."""

    def setup_method(self):
        self.predictor = RiskPredictor()

    def test_minimal_data_low_confidence(self):
        """With zero actions, confidence should be very low."""
        result = self.predictor.predict_risk(
            stress_score=50.0,
            action_count=0,
            current_day_number=30,
        )
        assert result.confidence_score <= 0.2
        assert result.data_sufficiency_index == 0.0

    def test_high_stress_critical_risk(self):
        """Stress score of 90 should yield critical risk."""
        result = self.predictor.predict_risk(
            stress_score=90.0,
            risk_index=0.8,
            action_count=15,
            current_day_number=60,
        )
        assert result.risk_label in ("critical", "high")
        assert result.prediction_value >= 0.5

    def test_normal_conditions_moderate_risk(self):
        """Moderate inputs → moderate risk."""
        result = self.predictor.predict_risk(
            stress_score=35.0,
            risk_index=0.3,
            stage_offset_days=2,
            action_count=8,
            current_day_number=30,
        )
        assert result.risk_label in ("low", "moderate")
        assert result.prediction_value < 0.6

    def test_confidence_increases_with_data(self):
        """More actions → higher confidence."""
        low_data = self.predictor.predict_risk(
            stress_score=50.0, action_count=2, current_day_number=30
        )
        high_data = self.predictor.predict_risk(
            stress_score=50.0, action_count=15, current_day_number=30
        )
        assert high_data.confidence_score > low_data.confidence_score

    def test_data_sufficiency_computation(self):
        """data_sufficiency scales with action_count / expected."""
        result = self.predictor.predict_risk(
            stress_score=30.0,
            action_count=10,
            current_day_number=30,
        )
        # 30 days → expected ~10 actions (30/3) → sufficiency = 1.0
        assert result.data_sufficiency_index == 1.0

    def test_zero_day_number(self):
        """Day 0 should still return a valid prediction."""
        result = self.predictor.predict_risk(
            stress_score=0.0, action_count=0, current_day_number=0
        )
        assert result.data_sufficiency_index == 0.0
        assert result.prediction_value >= 0.0

    def test_critical_stage_amplification(self):
        """Flowering/maturity stages amplify risk by 1.15×."""
        base = self.predictor.predict_risk(
            stress_score=60.0,
            action_count=10,
            current_day_number=60,
            stage="vegetative",
        )
        amplified = self.predictor.predict_risk(
            stress_score=60.0,
            action_count=10,
            current_day_number=60,
            stage="flowering",
        )
        assert amplified.prediction_value >= base.prediction_value

    def test_drift_penalty(self):
        """Large stage offset should increase risk."""
        no_drift = self.predictor.predict_risk(
            stress_score=30.0,
            stage_offset_days=0,
            action_count=10,
            current_day_number=30,
        )
        high_drift = self.predictor.predict_risk(
            stress_score=30.0,
            stage_offset_days=7,
            max_allowed_drift=7,
            action_count=10,
            current_day_number=30,
        )
        assert high_drift.prediction_value > no_drift.prediction_value


# ═══════════════════════════════════════════════════════════════════════
# ModelRegistry Tests (requires DB mock)
# ═══════════════════════════════════════════════════════════════════════


class TestModelRegistry:
    """Tests for ML model registry lifecycle."""

    def _make_mock_db(self):
        """Create a mock DB session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        return db

    def test_register_model(self):
        """Registering a model creates a DB record."""
        from app.services.ml.model_registry import ModelRegistry

        db = self._make_mock_db()
        registry = ModelRegistry(db)
        result = registry.register_model(
            model_type="risk_predictor",
            version="v1.0",
            artifact_path="/models/risk_v1.pkl",
            metrics={"accuracy": 0.92},
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_activate_model(self):
        """Activating a model deactivates others of the same type."""
        from app.services.ml.model_registry import ModelRegistry

        db = self._make_mock_db()
        # Simulate an existing model to activate
        mock_model = MagicMock()
        mock_model.model_type = "risk_predictor"
        mock_model.is_active = False
        db.query.return_value.filter.return_value.first.return_value = mock_model
        db.query.return_value.filter.return_value.all.return_value = []

        registry = ModelRegistry(db)
        registry.activate_model(model_id=uuid4())

        assert mock_model.is_active is True
        db.commit.assert_called()

    def test_get_active_model(self):
        """Querying active model returns the correct one."""
        from app.services.ml.model_registry import ModelRegistry

        db = self._make_mock_db()
        mock_model = MagicMock()
        mock_model.model_type = "risk_predictor"
        mock_model.is_active = True
        db.query.return_value.filter.return_value.first.return_value = mock_model

        registry = ModelRegistry(db)
        result = registry.get_active_model("risk_predictor")

        assert result is not None
        assert result.is_active is True
