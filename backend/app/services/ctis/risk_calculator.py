"""
Risk Index Calculator

Computes composite risk index from weather and farmer-behavior signals.

TDD 4.6 — risk_index = weather_weight * weather_risk + farmer_weight * farmer_risk
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default weights
DEFAULT_WEATHER_WEIGHT = 0.7
DEFAULT_FARMER_WEIGHT = 0.3

# Risk thresholds
RISK_LOW = 0.3
RISK_MODERATE = 0.5
RISK_HIGH = 0.7
RISK_CRITICAL = 0.85


class RiskCalculator:
    """
    Calculates composite risk index from multiple factors.

    Formula: risk_index = weather_weight * weather_risk + farmer_weight * stress_score
    """

    def __init__(
        self,
        weather_weight: float = DEFAULT_WEATHER_WEIGHT,
        farmer_weight: float = DEFAULT_FARMER_WEIGHT,
    ):
        # Ensure weights sum to 1.0
        total = weather_weight + farmer_weight
        self.weather_weight = weather_weight / total
        self.farmer_weight = farmer_weight / total

    def compute_risk_index(
        self,
        weather_risk: float = 0.0,
        stress_score: float = 0.0,
        deviation_penalty: float = 0.0,
        seasonal_risk_factor: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compute composite risk index.

        Args:
            weather_risk: Weather-derived risk (0-1)
            stress_score: Current crop stress score (0-1)
            deviation_penalty: Timeline deviation penalty (0-1)
            seasonal_risk_factor: Seasonal window risk adjustment

        Returns:
            Dict with risk_index, classification, contributing_factors
        """
        # Clamp inputs
        weather_risk = max(0.0, min(1.0, weather_risk))
        stress_score = max(0.0, min(1.0, stress_score))
        deviation_penalty = max(0.0, min(1.0, deviation_penalty))
        seasonal_risk_factor = max(0.0, min(0.2, seasonal_risk_factor))

        # Farmer-side risk combines stress and deviation
        farmer_risk = stress_score * 0.7 + deviation_penalty * 0.3

        # Core risk computation
        risk_index = (
            self.weather_weight * weather_risk + self.farmer_weight * farmer_risk
        )

        # Add seasonal risk adjustment
        risk_index += seasonal_risk_factor

        # Final clamp
        risk_index = max(0.0, min(1.0, float(int(risk_index * 10000)) / 10000))

        # Classify
        classification = self._classify_risk(risk_index)

        result = {
            "risk_index": risk_index,
            "classification": classification,
            "contributing_factors": {
                "weather_risk": float(int(weather_risk * 10000)) / 10000,
                "stress_score": float(int(stress_score * 10000)) / 10000,
                "deviation_penalty": float(int(deviation_penalty * 10000)) / 10000,
                "seasonal_risk_factor": float(int(seasonal_risk_factor * 10000))
                / 10000,
                "farmer_composite": float(int(farmer_risk * 10000)) / 10000,
            },
            "weights": {
                "weather": float(int(self.weather_weight * 10000)) / 10000,
                "farmer": float(int(self.farmer_weight * 10000)) / 10000,
            },
        }

        logger.info(
            f"Risk computed: {risk_index:.3f} ({classification}) — "
            f"weather={weather_risk:.3f}, stress={stress_score:.3f}"
        )

        return result

    def _classify_risk(self, risk_index: float) -> str:
        """Classify risk level."""
        if risk_index < RISK_LOW:
            return "low"
        elif risk_index < RISK_MODERATE:
            return "moderate"
        elif risk_index < RISK_HIGH:
            return "high"
        elif risk_index < RISK_CRITICAL:
            return "very_high"
        else:
            return "critical"

    def should_trigger_alert(self, risk_index: float) -> bool:
        """Determine if risk level warrants an alert."""
        return risk_index >= RISK_HIGH
