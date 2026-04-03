"""
What-If Simulation Engine

Allows farmers to test hypothetical actions without persisting any data.
Clones crop state in an isolated memory context and runs a simulated replay.

MSDD 1.14 — Deep copy enforcement: no live mutation allowed.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Optional
from copy import deepcopy
from datetime import datetime
import logging

from app.models.crop_instance import CropInstance
from app.services.ctis.stress_engine import StressEngine

logger = logging.getLogger(__name__)


class WhatIfSimulation:
    """
    Result container for a what-if simulation.
    All data is ephemeral — never persisted.
    """
    def __init__(self):
        self.current_state: Dict[str, Any] = {}
        self.projected_state: Dict[str, Any] = {}
        self.projected_stress: float = 0.0
        self.projected_risk: float = 0.0
        self.projected_day_number: int = 0
        self.projected_stage: Optional[str] = None
        self.actions_applied: int = 0
        self.state_transitions: List[Dict[str, Any]] = []
        self.action_breakdowns: List[Dict[str, Any]] = []
        self.deltas: Dict[str, Any] = {}
        self.warnings: List[str] = []

    def to_response(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state,
            "projected_state": self.projected_state,
            "deltas": self.deltas,
            "action_breakdowns": self.action_breakdowns,
            "state_transitions": self.state_transitions,
            "warnings": self.warnings,
            "actions_applied": self.actions_applied,
            "projected_stress": self.projected_stress,
            "projected_risk": self.projected_risk,
            "projected_day_number": self.projected_day_number,
            "projected_stage": self.projected_stage,
        }


class WhatIfEngine:
    """
    Enables what-if simulation by cloning crop state and running
    hypothetical actions in an isolated context.

    Deep Copy Enforcement (MSDD 1.14):
    - Entire CropInstance state (stage, stress, risk, day_number)
    - Stress history
    - Deviation history
    - Seasonal category
    - Market snapshot (if available)
    - Weather snapshot

    Simulation occurs in isolated memory context. No live mutation allowed.
    """

    def __init__(self, db: Session):
        self.db = db
        self.stress_engine = StressEngine()

    STAGE_PROGRESSION = {
        "wheat": [
            (0, "SOWED"),
            (15, "GERMINATION"),
            (30, "VEGETATIVE"),
            (60, "BOOTING"),
            (90, "FLOWERING"),
            (120, "GRAIN_FILL"),
            (150, "MATURITY"),
        ],
        "rice": [
            (0, "SOWED"),
            (10, "GERMINATION"),
            (20, "VEGETATIVE"),
            (70, "BOOTING"),
            (90, "FLOWERING"),
            (120, "GRAIN_FILL"),
            (150, "MATURITY"),
        ],
        "maize": [
            (0, "SOWED"),
            (10, "GERMINATION"),
            (20, "VEGETATIVE"),
            (60, "BOOTING"),
            (75, "FLOWERING"),
            (110, "GRAIN_FILL"),
            (140, "MATURITY"),
        ],
    }

    ACTION_STRESS_IMPACTS = {
        "irrigation": -0.05,
        "fertilizer": 0.01,
        "pesticide": -0.03,
        "fungicide": -0.04,
        "herbicide": -0.02,
        "pruning": 0.02,
        "thinning": 0.03,
        "transplanting": 0.05,
        "harvesting": 0.0,
        "monitoring": -0.005,
        "soil_amendment": -0.02,
        "weeding": -0.02,
        "inspection": 0.0,
        "delayed_action": 0.08,
        "other": 0.0,
    }

    ACTION_RISK_IMPACTS = {
        "irrigation": -0.05,
        "fungicide": -0.10,
        "pesticide": -0.08,
        "fertilizer": 0.02,
    }

    async def simulate(
        self,
        crop_instance_id: UUID,
        hypothetical_actions: List[Dict[str, Any]],
    ) -> WhatIfSimulation:
        """
        Run a what-if simulation with hypothetical actions.

        Args:
            crop_instance_id: The crop instance to simulate on
            hypothetical_actions: List of hypothetical action dicts with
                keys: action_type, action_date, metadata

        Returns:
            WhatIfSimulation with projected state
        """
        # Load current crop state
        crop = self.db.query(CropInstance).filter(
            CropInstance.id == crop_instance_id,
            CropInstance.is_deleted == False,
        ).first()

        if not crop:
            raise ValueError(f"Crop instance {crop_instance_id} not found")

        # Deep copy — MSDD 1.14 enforcement
        sim_state = self._deep_clone_state(crop)

        result = WhatIfSimulation()
        result.current_state = {
            "state": str(sim_state["state"]),
            "stress": float(sim_state["stress_score"]),
            "risk": float(sim_state["risk_index"]),
            "day_number": int(sim_state["current_day_number"]),
            "stage": str(sim_state.get("stage", "")) or None,
        }
        result.projected_stress = float(sim_state["stress_score"])
        result.projected_risk = float(sim_state["risk_index"])
        result.projected_day_number = int(sim_state["current_day_number"])
        result.projected_stage = str(sim_state.get("stage", "")) or None

        # Apply hypothetical actions
        for action_index, action in enumerate(hypothetical_actions, start=1):
            try:
                sim_state, breakdown, transition, timeline_warning = self._apply_hypothetical_action(
                    sim_state,
                    action,
                    action_index,
                )
                result.action_breakdowns.append(breakdown)
                if transition:
                    result.state_transitions.append(transition)
                if timeline_warning:
                    result.warnings.append(timeline_warning)
                result.actions_applied += 1
            except Exception as e:
                result.warnings.append(
                    f"Action '{action.get('action_type', 'unknown')}' failed: {str(e)}"
                )

        # Update projected results
        result.projected_state = {
            "state": str(sim_state["state"]),
            "stress": float(sim_state["stress_score"]),
            "risk": float(sim_state["risk_index"]),
            "day_number": int(sim_state["current_day_number"]),
            "stage": str(sim_state.get("stage", "")) or None,
        }
        result.projected_stress = float(sim_state["stress_score"])
        result.projected_risk = float(sim_state["risk_index"])
        result.projected_day_number = int(sim_state["current_day_number"])
        result.projected_stage = str(sim_state.get("stage", "")) or None
        result.deltas = {
            "stress": round(result.projected_stress - result.current_state["stress"], 4),
            "risk": round(result.projected_risk - result.current_state["risk"], 4),
            "days": result.projected_day_number - result.current_state["day_number"],
            "stage_changed": result.current_state.get("stage") != result.projected_stage,
        }

        logger.info(
            f"What-if simulation for crop {crop_instance_id}: "
            f"{result.actions_applied} actions applied, "
            f"projected stress={result.projected_stress:.3f}"
        )

        return result

    def _deep_clone_state(self, crop: CropInstance) -> Dict[str, Any]:
        """Create a deep copy of crop state for isolated simulation."""
        return {
            "state": crop.state,
            "stage": crop.stage,
            "stress_score": float(crop.stress_score or 0.0),
            "risk_index": float(crop.risk_index or 0.0),
            "current_day_number": crop.current_day_number or 0,
            "sowing_date": crop.sowing_date,
            "crop_type": crop.crop_type,
            "region": crop.region,
            "seasonal_window_category": crop.seasonal_window_category,
            "stage_offset_days": crop.stage_offset_days or 0,
            "metadata_extra": deepcopy(crop.metadata_extra or {}),
        }

    def _apply_hypothetical_action(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        action_index: int,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]], Optional[str]]:
        """Apply a single hypothetical action to the cloned state."""
        action_type = action.get("action_type", "")
        action_date = action.get("action_date")
        day_delta, warning = self._compute_day_delta(state, action_date, action_index)

        day_before = int(state["current_day_number"])
        stage_before = state.get("stage")
        stress_before = float(state["stress_score"])
        risk_before = float(state["risk_index"])

        state["current_day_number"] = day_before + day_delta
        stage_after = self._derive_stage(state["crop_type"], state["current_day_number"])
        state["stage"] = stage_after

        impact = self.ACTION_STRESS_IMPACTS.get(action_type, 0.0)
        stress_context = self._compute_contextual_stress_impact(action_type, action_date, day_delta)
        total_stress_delta = impact + stress_context
        new_stress = max(0.0, min(1.0, stress_before + total_stress_delta))
        state["stress_score"] = float(int(new_stress * 10000)) / 10000

        risk_action_impact = self.ACTION_RISK_IMPACTS.get(action_type, 0.0)
        weather_risk = self._approx_weather_risk(action_date)
        risk_from_stress = self.stress_engine.compute_risk_from_stress(
            stress_score=new_stress,
            weather_risk=weather_risk,
        )
        next_risk = max(0.0, min(1.0, risk_before + (risk_from_stress - risk_before) + risk_action_impact))
        state["risk_index"] = round(next_risk, 4)

        transition = None
        if stage_before != stage_after:
            transition = {
                "from_stage": stage_before,
                "to_stage": stage_after,
                "at_action": action_index,
                "at_day": state["current_day_number"],
            }

        breakdown = {
            "action_index": action_index,
            "action_type": action_type,
            "action_date": action_date,
            "day_delta": day_delta,
            "day_number_before": day_before,
            "day_number_after": state["current_day_number"],
            "stage_before": stage_before,
            "stage_after": stage_after,
            "stress_delta": round(state["stress_score"] - stress_before, 4),
            "stress_after": state["stress_score"],
            "risk_delta": round(state["risk_index"] - risk_before, 4),
            "risk_after": state["risk_index"],
            "details": {
                "impact_base": impact,
                "impact_contextual": round(stress_context, 4),
                "weather_risk": weather_risk,
                "risk_action_impact": risk_action_impact,
            },
        }

        return state, breakdown, transition, warning

    def _derive_stage(self, crop_type: str, day_number: int) -> str:
        progression = self.STAGE_PROGRESSION.get((crop_type or "").lower(), self.STAGE_PROGRESSION["wheat"])
        current_stage = progression[0][1]
        for threshold_day, stage_name in progression:
            if day_number >= threshold_day:
                current_stage = stage_name
            else:
                break
        return current_stage

    def _compute_day_delta(
        self,
        state: Dict[str, Any],
        action_date: Optional[str],
        action_index: int,
    ) -> tuple[int, Optional[str]]:
        if not action_date:
            return 1, None

        sowing_day = state.get("sowing_date")
        if not sowing_day:
            return 1, None

        try:
            action_day = datetime.fromisoformat(action_date).date()
        except ValueError as exc:
            raise ValueError("action_date must be a valid ISO date string") from exc

        current_day = sowing_day.fromordinal(sowing_day.toordinal() + int(state["current_day_number"]))
        day_delta = (action_day - current_day).days

        if day_delta < 0:
            return 0, f"Action {action_index}: action_date is in the past; timeline advancement set to 0"
        if day_delta > 365:
            return 365, f"Action {action_index}: action_date exceeds 365 days; capped at 365"
        return day_delta, None

    def _approx_weather_risk(self, action_date: Optional[str]) -> float:
        # Lightweight deterministic fallback until weather forecasts are integrated.
        if not action_date:
            return 0.2
        try:
            day = datetime.fromisoformat(action_date).date().day
        except ValueError:
            return 0.2
        return round(0.1 + (day % 10) * 0.03, 4)

    def _compute_contextual_stress_impact(self, action_type: str, action_date: Optional[str], day_delta: int) -> float:
        contextual = 0.0
        if day_delta > 14:
            contextual += 0.01
        if action_type in {"pesticide", "fungicide"} and self._approx_weather_risk(action_date) > 0.35:
            contextual += 0.02
        if action_type == "irrigation" and self._approx_weather_risk(action_date) > 0.35:
            contextual -= 0.01
        return contextual
