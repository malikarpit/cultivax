"""
Stress Score Integration Engine — Multi-Signal Stress Computation

Integrates multiple signals (ML prediction, weather risk, deviation penalty,
edge signals) into a unified stress score using weighted EMA.

TDD Section 4.7 | MSDD 1.9
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — signal weights (must sum to 1.0)
# ---------------------------------------------------------------------------

SIGNAL_WEIGHTS = {
    "backend_ml": 0.35,  # ML risk prediction signal
    "weather_risk": 0.25,  # Weather-based risk
    "deviation_penalty": 0.25,  # Timeline deviation penalty
    "edge_signal": 0.15,  # Edge/media analysis signal
}

# EMA smoothing factor (higher = more weight on new signal)
ALPHA = 0.3

# Maximum allowed daily stress jump (prevents spikes)
MAX_DAILY_JUMP = 0.15

# Stress bounds
STRESS_MIN = 0.0
STRESS_MAX = 1.0


class StressEngine:
    """
    Multi-signal stress score integration engine.

    Formula (TDD 4.7):
        signal = w_ml*backend_ml + w_weather*weather_risk
                 + w_deviation*deviation_penalty + w_edge*edge_signal
        effective = signal * confidence
        new_stress = alpha * effective + (1 - alpha) * previous_stress
        new_stress = clamp(new_stress, 0, 1)
        daily_jump = clamp(|new_stress - previous|, max=MAX_DAILY_JUMP)
    """

    def integrate_stress(
        self,
        backend_ml: float = 0.0,
        weather_risk: float = 0.0,
        deviation_penalty: float = 0.0,
        edge_signal: float = 0.0,
        previous_stress: float = 0.0,
        confidence: float = 1.0,
    ) -> dict:
        """
        Compute integrated stress score from multiple signals.

        Args:
            backend_ml: ML risk prediction (0-1)
            weather_risk: Weather-derived risk (0-1)
            deviation_penalty: Timeline deviation penalty (0-1)
            edge_signal: Edge/media analysis signal (0-1)
            previous_stress: Previous stress score (0-1)
            confidence: ML confidence score (0-1), scales effective signal

        Returns:
            Dict with new_stress, signal_breakdown, effective_signal, was_clamped

        """
        # Clamp all inputs to [0, 1]
        backend_ml = max(0.0, min(1.0, backend_ml))
        weather_risk = max(0.0, min(1.0, weather_risk))
        deviation_penalty = max(0.0, min(1.0, deviation_penalty))
        edge_signal = max(0.0, min(1.0, edge_signal))
        previous_stress = max(0.0, min(1.0, previous_stress))
        confidence = max(0.0, min(1.0, confidence))

        # Weighted composite signal
        raw_signal = (
            SIGNAL_WEIGHTS["backend_ml"] * backend_ml
            + SIGNAL_WEIGHTS["weather_risk"] * weather_risk
            + SIGNAL_WEIGHTS["deviation_penalty"] * deviation_penalty
            + SIGNAL_WEIGHTS["edge_signal"] * edge_signal
        )

        # Scale by confidence (low confidence → softer signal)
        effective_signal = raw_signal * confidence

        # EMA integration with previous stress
        new_stress = ALPHA * effective_signal + (1 - ALPHA) * previous_stress

        # Clamp daily jump to prevent spikes
        was_clamped = False
        delta = new_stress - previous_stress
        if abs(delta) > MAX_DAILY_JUMP:
            was_clamped = True
            if delta > 0:
                new_stress = previous_stress + MAX_DAILY_JUMP
            else:
                new_stress = previous_stress - MAX_DAILY_JUMP

        # Final bounds
        new_stress = max(STRESS_MIN, min(STRESS_MAX, new_stress))

        result = {
            "new_stress": float(round(new_stress, 4)),  # type: ignore
            "previous_stress": float(round(previous_stress, 4)),  # type: ignore
            "raw_signal": float(round(raw_signal, 4)),  # type: ignore
            "effective_signal": float(round(effective_signal, 4)),  # type: ignore
            "confidence_applied": float(round(confidence, 4)),  # type: ignore
            "delta": float(round(new_stress - previous_stress, 4)),  # type: ignore
            "was_clamped": was_clamped,
            "signal_breakdown": {
                "backend_ml": float(round(backend_ml * SIGNAL_WEIGHTS["backend_ml"], 4)),  # type: ignore
                "weather_risk": float(round(weather_risk * SIGNAL_WEIGHTS["weather_risk"], 4)),  # type: ignore
                "deviation_penalty": float(
                    round(  # type: ignore
                        deviation_penalty * SIGNAL_WEIGHTS["deviation_penalty"], 4
                    )
                ),
                "edge_signal": float(round(edge_signal * SIGNAL_WEIGHTS["edge_signal"], 4)),  # type: ignore
            },
        }

        logger.info(
            f"Stress integration: {previous_stress:.3f} → {new_stress:.3f} "
            f"(signal={raw_signal:.3f}, confidence={confidence:.2f}, "
            f"clamped={was_clamped})"
        )

        return result

    def compute_risk_from_stress(
        self,
        stress_score: float,
        weather_weight: float = 0.7,
        farmer_weight: float = 0.3,
        weather_risk: float = 0.0,
    ) -> float:
        """
        Derive risk index from stress score.
        risk_index = weather_weight * weather_risk + farmer_weight * stress_score
        """
        risk = weather_weight * weather_risk + farmer_weight * stress_score
        return max(0.0, min(1.0, float(round(risk, 4))))  # type: ignore
