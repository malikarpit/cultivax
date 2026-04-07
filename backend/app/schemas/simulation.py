"""Simulation schemas for what-if projections."""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

ALLOWED_ACTION_TYPES = {
    "irrigation",
    "fertilizer",
    "pesticide",
    "fungicide",
    "herbicide",
    "pruning",
    "thinning",
    "transplanting",
    "harvesting",
    "monitoring",
    "soil_amendment",
    "other",
    "delayed_action",
    "weeding",
    "inspection",
}


class HypotheticalAction(BaseModel):
    action_type: str
    action_date: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in ALLOWED_ACTION_TYPES:
            raise ValueError(
                f"Invalid action_type '{value}'. Allowed values: {sorted(ALLOWED_ACTION_TYPES)}"
            )
        return normalized

    @field_validator("action_date")
    @classmethod
    def validate_action_date(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        try:
            action_day = datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise ValueError("action_date must be a valid ISO date string") from exc

        max_day = date.today() + timedelta(days=365)
        if action_day > max_day:
            raise ValueError("action_date cannot be more than 365 days in the future")
        return value


class SimulationRequest(BaseModel):
    hypothetical_actions: list[HypotheticalAction] = Field(min_length=1, max_length=100)


class SimulationResponse(BaseModel):
    current_state: dict[str, Any]
    projected_state: dict[str, Any]
    deltas: dict[str, Any]
    action_breakdowns: list[dict[str, Any]]
    state_transitions: list[dict[str, Any]]
    warnings: list[str]
    actions_applied: int

    # Backward-compatible scalar fields consumed by the existing frontend page.
    projected_stress: float
    projected_risk: float
    projected_day_number: int
    projected_stage: Optional[str]
