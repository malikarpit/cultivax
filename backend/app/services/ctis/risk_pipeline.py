"""Unified risk computation path shared across replay and what-if flows."""

from app.services.ctis.risk_calculator import RiskCalculator


class RiskPipeline:
    """Normalize inputs and delegate to RiskCalculator for one canonical risk path."""

    def __init__(self):
        self.calc = RiskCalculator()

    def compute(
        self,
        *,
        stress_score_0_100: float,
        weather_risk: float,
        deviation_penalty: float,
        seasonal_risk_factor: float = 0.0,
    ):
        stress_norm = max(0.0, min(1.0, float(stress_score_0_100) / 100.0))
        return self.calc.compute_risk_index(
            weather_risk=float(max(0.0, min(1.0, weather_risk))),
            stress_score=stress_norm,
            deviation_penalty=float(max(0.0, min(1.0, deviation_penalty))),
            seasonal_risk_factor=float(max(0.0, min(0.2, seasonal_risk_factor))),
        )
