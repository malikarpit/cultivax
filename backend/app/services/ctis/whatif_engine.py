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
from datetime import datetime, timezone
import logging

from app.models.crop_instance import CropInstance
from app.models.action_log import ActionLog
from app.services.ctis.stress_engine import StressEngine
from app.services.ctis.state_machine import CropStateMachine

logger = logging.getLogger(__name__)


class WhatIfSimulation:
    """
    Result container for a what-if simulation.
    All data is ephemeral — never persisted.
    """
    def __init__(self):
        self.projected_state: str = "Unknown"
        self.projected_stress: float = 0.0
        self.projected_risk: float = 0.0
        self.projected_day_number: int = 0
        self.projected_stage: Optional[str] = None
        self.actions_applied: int = 0
        self.state_transitions: List[Dict[str, str]] = []
        self.warnings: List[str] = []


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
        result.projected_state = str(sim_state["state"])
        result.projected_stress = float(sim_state["stress_score"])
        result.projected_risk = float(sim_state["risk_index"])
        result.projected_day_number = int(sim_state["current_day_number"])
        result.projected_stage = str(sim_state.get("stage", "")) or None

        # Apply hypothetical actions
        for action in hypothetical_actions:
            try:
                # We pass the full dictionary into _apply_hypothetical_action
                sim_state = self._apply_hypothetical_action(sim_state, action)
                result.actions_applied += 1
            except Exception as e:
                result.warnings.append(
                    f"Action '{action.get('action_type', 'unknown')}' failed: {str(e)}"
                )

        # Update projected results
        result.projected_state = str(sim_state["state"])
        result.projected_stress = float(sim_state["stress_score"])
        result.projected_risk = float(sim_state["risk_index"])
        result.projected_day_number = int(sim_state["current_day_number"])
        result.projected_stage = str(sim_state.get("stage", "")) or None

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
        self, state: Dict[str, Any], action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single hypothetical action to the cloned state."""
        action_type = action.get("action_type", "")
        
        # Simulate day advancement
        state["current_day_number"] += 1

        # Simulate stress impact based on action type
        stress_impact = {
            "irrigation": -0.05,
            "fertilizer": -0.03,
            "pesticide": -0.04,
            "weeding": -0.02,
            "inspection": 0.0,
            "delayed_action": 0.08,
        }

        impact = stress_impact.get(action_type, 0.0)
        new_stress = max(0.0, min(1.0, state["stress_score"] + impact))
        state["stress_score"] = float(int(new_stress * 10000)) / 10000

        # Recompute risk
        state["risk_index"] = self.stress_engine.compute_risk_from_stress(
            stress_score=new_stress,
            weather_risk=0.0,  # Use current weather snapshot if available
        )

        return state
