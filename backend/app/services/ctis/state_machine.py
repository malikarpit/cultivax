"""
Crop Instance State Machine — MSDD 1.5

Enforces valid state transitions for crop instances.
Every transition emits a StageChanged event.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class InvalidStateTransition(Exception):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, current_state: str, new_state: str):
        self.current_state = current_state
        self.new_state = new_state
        super().__init__(
            f"Invalid state transition: '{current_state}' → '{new_state}'"
        )


# Valid state transitions (MSDD 1.5)
VALID_TRANSITIONS = {
    "Created": ["Active"],
    "Active": ["Delayed", "AtRisk", "ReadyToHarvest"],
    "Delayed": ["Active", "AtRisk"],
    "AtRisk": ["Active", "Delayed"],
    "ReadyToHarvest": ["Harvested"],
    "Harvested": ["Closed"],
    "Closed": ["Archived"],
    "RecoveryRequired": ["Active"],  # MSDD 1.18 — admin resolution only
}

# All recognized states
ALL_STATES = set(VALID_TRANSITIONS.keys()) | {
    state for targets in VALID_TRANSITIONS.values() for state in targets
}

# Terminal states — no actions allowed
TERMINAL_STATES = {"Closed", "Archived"}

# States that block new action logging
BLOCKED_STATES = {"RecoveryRequired", "Closed", "Archived"}


class CropStateMachine:
    """
    State machine for crop instance lifecycle.

    Usage:
        sm = CropStateMachine("Active")
        sm.transition("Delayed")   # ok
        sm.transition("Archived")  # raises InvalidStateTransition

        # Check without raising
        if sm.can_transition("AtRisk"):
            sm.transition("AtRisk")
    """

    def __init__(self, current_state: str):
        if current_state not in ALL_STATES:
            raise ValueError(f"Unknown state: '{current_state}'")
        self._state = current_state
        self._history: list[dict] = []

    @property
    def state(self) -> str:
        return self._state

    @property
    def history(self) -> list[dict]:
        return self._history.copy()

    def can_transition(self, new_state: str) -> bool:
        """Check if a transition is valid without performing it."""
        allowed = VALID_TRANSITIONS.get(self._state, [])
        return new_state in allowed

    def get_allowed_transitions(self) -> list[str]:
        """Return list of valid next states from the current state."""
        return list(VALID_TRANSITIONS.get(self._state, []))

    def transition(self, new_state: str, reason: Optional[str] = None) -> str:
        """
        Perform a state transition.

        Args:
            new_state: Target state to transition to.
            reason: Optional reason for the transition.

        Returns:
            The new state after transition.

        Raises:
            InvalidStateTransition: If the transition is not allowed.
        """
        if not self.can_transition(new_state):
            raise InvalidStateTransition(self._state, new_state)

        old_state = self._state
        self._state = new_state

        self._history.append({
            "from": old_state,
            "to": new_state,
            "reason": reason,
        })

        logger.info(
            f"State transition: {old_state} → {new_state}"
            f"{f' ({reason})' if reason else ''}"
        )

        return self._state

    def is_terminal(self) -> bool:
        """Check if current state is terminal (no further transitions)."""
        return self._state in TERMINAL_STATES

    def is_blocked(self) -> bool:
        """Check if current state blocks new action logging."""
        return self._state in BLOCKED_STATES

    def is_actionable(self) -> bool:
        """Check if actions can be logged in the current state."""
        return not self.is_blocked()


def validate_transition(current_state: str, new_state: str) -> bool:
    """
    Standalone validator — no state machine instance needed.
    Returns True if the transition is valid, False otherwise.
    """
    return new_state in VALID_TRANSITIONS.get(current_state, [])


def get_transition_event_payload(
    crop_instance_id: str,
    old_state: str,
    new_state: str,
    reason: Optional[str] = None,
) -> dict:
    """Build an event payload for a StageChanged event (MSDD 1.5)."""
    return {
        "crop_instance_id": crop_instance_id,
        "old_state": old_state,
        "new_state": new_state,
        "reason": reason,
    }
