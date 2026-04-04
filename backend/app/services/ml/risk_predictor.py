"""
ML Risk Predictor — V1 Rule-Based Risk Engine

Predicts risk for a crop instance using rule-based logic.
Will be replaced with a trained ML model in future iterations.

ML Enhancement 2: Confidence Propagation — every output includes
prediction_value, confidence_score, data_sufficiency_index, model_version.

TDD Section 5.3 | ML Enhancement 2
"""

from typing import Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Current model version
MODEL_VERSION = "rule-based-v1"

# Stress thresholds for risk classification
RISK_THRESHOLDS = {
    "critical": 80.0,   # stress >= 80 → high risk
    "high": 60.0,       # stress >= 60 → elevated risk
    "moderate": 40.0,   # stress >= 40 → moderate risk
    "low": 20.0,        # stress >= 20 → low risk
}

# Minimum data points required for reliable prediction
MIN_DATA_POINTS_FOR_HIGH_CONFIDENCE = 10
MIN_DATA_POINTS_FOR_MEDIUM_CONFIDENCE = 5


class RiskPrediction:
    """
    Structured risk prediction output with confidence propagation.

    Every ML output includes:
    - prediction_value: the raw risk probability (0.0 - 1.0)
    - confidence_score: how confident the model is (0.0 - 1.0)
    - data_sufficiency_index: how much data was available (0.0 - 1.0)
    - model_version: which model produced this prediction
    - risk_adjusted: prediction × confidence (for downstream use)
    - risk_label: human-readable risk category
    """

    def __init__(
        self,
        prediction_value: float,
        confidence_score: float,
        data_sufficiency_index: float,
        model_version: str = MODEL_VERSION,
    ):
        self.prediction_value = max(0.0, min(1.0, prediction_value))
        self.confidence_score = max(0.0, min(1.0, confidence_score))
        self.data_sufficiency_index = max(0.0, min(1.0, data_sufficiency_index))
        self.model_version = model_version
        self.risk_adjusted = self.prediction_value * self.confidence_score
        self.risk_label = self._compute_label()
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def _compute_label(self) -> str:
        """Map risk probability to a human-readable label."""
        risk_pct = self.prediction_value * 100
        if risk_pct >= RISK_THRESHOLDS["critical"]:
            return "critical"
        elif risk_pct >= RISK_THRESHOLDS["high"]:
            return "high"
        elif risk_pct >= RISK_THRESHOLDS["moderate"]:
            return "moderate"
        elif risk_pct >= RISK_THRESHOLDS["low"]:
            return "low"
        return "minimal"

    def to_dict(self) -> dict:
        return {
            "prediction_value": self.prediction_value,
            "confidence_score": self.confidence_score,
            "data_sufficiency_index": self.data_sufficiency_index,
            "risk_adjusted": self.risk_adjusted,
            "risk_label": self.risk_label,
            "model_version": self.model_version,
            "model_status": "stub" if self.model_version.startswith("rule-based") else "active",
            "generated_at": self.generated_at,
        }

    @property
    def recommendation_tone(self) -> str:
        """
        Low confidence → softer recommendation tone (ML Enhancement 2).
        High confidence → assertive tone.
        """
        if self.confidence_score >= 0.8:
            return "assertive"
        elif self.confidence_score >= 0.5:
            return "moderate"
        return "tentative"


class RiskPredictor:
    """
    Rule-based risk predictor (V1 engine) with ML safety guards.

    Uses stress_score, deviation metrics, and stage progression
    to compute risk probability. No trained model — pure heuristics.

    26 march: Phase 4D Safety Guards:
      - Small dataset safeguard (Patch 3.4): fallback if < 200 samples
      - ML kill switch (ML Enh 8): respects feature flag
      - Yield biological cap (ML 4.9): cap yield predictions at crop-specific ceiling

    Will be swapped with a real ML model when training data is available.
    """

    # Minimum training samples for ML model activation (Patch 3.4)
    MIN_TRAINING_SAMPLES = 200

    # Biological yield caps per crop type (quintals/acre) (ML 4.9)
    YIELD_BIO_CAPS = {
        "wheat": 25.0,
        "rice": 30.0,
        "cotton": 12.0,
        "sugarcane": 400.0,
        "maize": 35.0,
        "soybean": 15.0,
        "default": 50.0,
    }

    def is_ml_safe(self, training_samples: int = 0, db=None) -> bool:
        """
        Check if ML prediction is safe to use (Patch 3.4 + ML Enh 8).
        Returns False if kill switch is off or insufficient training data.
        """
        ml_enabled = True
        if db:
            from app.services.feature_flags import is_enabled
            ml_enabled = is_enabled(db, "prod.ml_kill_switch", default=True)

        if not ml_enabled:
            logger.info("ML kill switch is OFF — using rule-based fallback")
            return False
        if training_samples < self.MIN_TRAINING_SAMPLES:
            logger.info(
                f"Insufficient training data ({training_samples} < {self.MIN_TRAINING_SAMPLES}) "
                "— using rule-based fallback"
            )
            return False
        return True

    def cap_yield_prediction(
        self, predicted_yield: float, crop_type: str = "default"
    ) -> float:
        """
        Apply biological yield cap (ML 4.9).
        Prevents unrealistic yield predictions beyond crop-specific ceilings.
        """
        cap = self.YIELD_BIO_CAPS.get(crop_type.lower(), self.YIELD_BIO_CAPS["default"])
        if predicted_yield > cap:
            logger.warning(
                f"Yield prediction {predicted_yield:.2f} exceeds bio cap {cap:.2f} "
                f"for {crop_type} — capping"
            )
            return cap
        return predicted_yield

    def predict_risk(
        self,
        stress_score: float = 0.0,
        risk_index: float = 0.0,
        current_day_number: int = 0,
        stage: Optional[str] = None,
        stage_offset_days: int = 0,
        consecutive_deviations: int = 0,
        action_count: int = 0,
        max_allowed_drift: int = 7,
        db=None,
        training_samples: int = 0,
    ) -> RiskPrediction:
        """
        Predict risk for a crop instance using rule-based logic.

        Args:
            stress_score: Current cumulative stress (0-100)
            risk_index: Current risk index (0-1)
            current_day_number: Days since sowing
            stage: Current crop stage
            stage_offset_days: Drift from expected timeline
            consecutive_deviations: Number of consecutive deviations
            action_count: Total actions logged (for data sufficiency)
            max_allowed_drift: Maximum allowed drift days

        Returns:
            RiskPrediction with all confidence propagation fields.
        """

        # --- Compute data sufficiency ---
        data_sufficiency = self._compute_data_sufficiency(
            action_count, current_day_number
        )

        # --- Compute confidence ---
        confidence = self._compute_confidence(
            action_count, current_day_number, data_sufficiency
        )

        # --- Compute risk probability (rule-based) ---
        risk_probability = self._compute_risk(
            stress_score=stress_score,
            risk_index=risk_index,
            stage_offset_days=stage_offset_days,
            consecutive_deviations=consecutive_deviations,
            max_allowed_drift=max_allowed_drift,
            stage=stage,
        )

        # --- Dynamically resolve active model (Audit 31) ---
        active_version = MODEL_VERSION
        inference_source = "fallback_rule_based"
        if db and self.is_ml_safe(training_samples=training_samples, db=db):
            try:
                from app.services.ml.model_registry import ModelRegistry
                registry = ModelRegistry(db)
                active_model = registry.get_active_model("risk_predictor")
                if active_model:
                    active_version = f"v{active_model.version}"
                    inference_source = "registry_ml_inference"
            except Exception as e:
                logger.error(f"Failed to resolve active ML Model, failing over safely: {e}")

        prediction = RiskPrediction(
            prediction_value=risk_probability,
            confidence_score=confidence,
            data_sufficiency_index=data_sufficiency,
            model_version=active_version,
        )

        logger.info(
            f"Risk prediction: value={prediction.prediction_value:.3f}, "
            f"confidence={prediction.confidence_score:.3f}, "
            f"adjusted={prediction.risk_adjusted:.3f}, "
            f"label={prediction.risk_label}, tone={prediction.recommendation_tone}"
        )

        return prediction

    def _compute_data_sufficiency(
        self, action_count: int, day_number: int
    ) -> float:
        """
        Compute how much data is available relative to what's expected.
        A crop at day 30 with 0 actions has low sufficiency.
        """
        if day_number <= 0:
            return 0.0

        # Expected ~1 action per 3 days as baseline
        expected_actions = max(day_number / 3, 1)
        sufficiency = min(action_count / expected_actions, 1.0)
        return float(round(sufficiency, 3))  # type: ignore

    def _compute_confidence(
        self, action_count: int, day_number: int, data_sufficiency: float
    ) -> float:
        """
        Confidence based on data availability.
        Rule-based models have inherently lower confidence than trained models.
        """
        # Base confidence for rule-based model is capped at 0.7
        base_confidence = 0.7

        # Scale by data sufficiency
        if action_count >= MIN_DATA_POINTS_FOR_HIGH_CONFIDENCE:
            data_factor = 1.0
        elif action_count >= MIN_DATA_POINTS_FOR_MEDIUM_CONFIDENCE:
            data_factor = 0.7
        elif action_count > 0:
            data_factor = 0.4
        else:
            data_factor = 0.2

        confidence = base_confidence * data_factor * max(data_sufficiency, 0.3)
        return float(round(min(confidence, 0.7), 3))  # type: ignore

    def _compute_risk(
        self,
        stress_score: float,
        risk_index: float,
        stage_offset_days: int,
        consecutive_deviations: int,
        max_allowed_drift: int,
        stage: Optional[str],
    ) -> float:
        """
        Rule-based risk computation from multiple signals.
        """
        risk = 0.0

        # Signal 1: Stress score contribution (40% weight)
        stress_normalized = min(stress_score / 100.0, 1.0)
        risk += 0.40 * stress_normalized

        # Signal 2: Existing risk index (20% weight)
        risk += 0.20 * min(risk_index, 1.0)

        # Signal 3: Drift penalty (25% weight)
        if max_allowed_drift > 0:
            drift_ratio = min(abs(stage_offset_days) / max_allowed_drift, 2.0)
            risk += 0.25 * min(drift_ratio / 2.0, 1.0)

        # Signal 4: Consecutive deviations (15% weight)
        deviation_penalty = min(consecutive_deviations / 5.0, 1.0)
        risk += 0.15 * deviation_penalty

        # Stage-specific adjustment
        if stage in ("flowering", "maturity"):
            # Critical stages — amplify risk slightly
            risk *= 1.15

        # Guardrail: very high stress should never remain in low/moderate buckets
        # even when other signals are sparse.
        if stress_score >= 85:
            risk = max(risk, 0.65)
        elif stress_score >= 75:
            risk = max(risk, 0.55)

        return float(round(min(risk, 1.0), 4))  # type: ignore
