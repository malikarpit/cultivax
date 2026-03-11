"""
Event Handlers

Maps event types to handler functions.
Handlers are called by the Event Dispatcher when processing events.
TDD Section 3.5–3.12.
"""

import asyncio
import logging
from typing import Callable, Optional, Dict
from sqlalchemy.orm import Session  # type: ignore

from app.models.event_log import EventLog  # type: ignore
from app.services.ctis.replay_engine import ReplayEngine  # type: ignore
from app.services.ctis.state_machine import (  # type: ignore
    CropStateMachine,
    get_transition_event_payload,
    InvalidStateTransition,
)

logger = logging.getLogger(__name__)


def handle_action_logged(db: Session, event: EventLog):
    """
    Handle ActionLogged event — trigger replay for the crop instance.
    Wired in Day 13: ActionLogged → ReplayTriggered pipeline.
    """
    logger.info(f"Processing ActionLogged for entity {event.entity_id}")

    crop_instance_id = None
    if event.payload and isinstance(event.payload, dict):
        crop_instance_id = event.payload.get("crop_instance_id")
    if not crop_instance_id and event.entity_id:
        crop_instance_id = event.entity_id

    if not crop_instance_id:
        logger.error("ActionLogged event missing crop_instance_id")
        return

    try:
        engine = ReplayEngine(db)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule as a task if we're already in an async context
            asyncio.ensure_future(engine.replay_crop_instance(crop_instance_id))
        else:
            loop.run_until_complete(engine.replay_crop_instance(crop_instance_id))
        logger.info(f"Replay completed for crop {crop_instance_id}")
    except Exception as e:
        logger.error(f"Replay failed for crop {crop_instance_id}: {e}")


def handle_replay_triggered(db: Session, event: EventLog):
    """Handle ReplayTriggered event — run full or incremental replay."""
    logger.info(f"Processing ReplayTriggered for entity {event.entity_id}")

    crop_instance_id = event.entity_id
    if not crop_instance_id:
        logger.error("ReplayTriggered event missing entity_id")
        return

    try:
        engine = ReplayEngine(db)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(engine.replay_crop_instance(crop_instance_id))
        else:
            loop.run_until_complete(engine.replay_crop_instance(crop_instance_id))
    except Exception as e:
        logger.error(f"Replay failed for crop {crop_instance_id}: {e}")


def handle_stage_changed(db: Session, event: EventLog):
    """Handle StageChanged event — validate state transition via State Machine."""
    logger.info(f"Processing StageChanged for entity {event.entity_id}")

    payload = event.payload or {}
    old_state = payload.get("old_state")
    new_state = payload.get("new_state")

    if old_state and new_state:
        try:
            sm = CropStateMachine(old_state)
            sm.transition(new_state, reason=payload.get("reason"))
            logger.info(f"State transition validated: {old_state} → {new_state}")
        except InvalidStateTransition as e:
            logger.error(f"Invalid state transition rejected: {e}")


def handle_stress_updated(db: Session, event: EventLog):
    """Handle StressUpdated event — recalculate risk index."""
    logger.info(f"Processing StressUpdated for entity {event.entity_id}")
    # TODO: Day 14 — integrate with stress engine


def handle_media_analyzed(db: Session, event: EventLog):
    """Handle MediaAnalyzed event — update crop stress from media signals."""
    logger.info(f"Processing MediaAnalyzed for entity {event.entity_id}")
    # TODO: Day 14 — integrate with media analysis


def handle_weather_updated(db: Session, event: EventLog):
    """Handle WeatherUpdated event — feed weather data into stress model."""
    logger.info(f"Processing WeatherUpdated for entity {event.entity_id}")
    # TODO: Day 14 — integrate with weather service


# Event type → handler mapping
_HANDLER_MAP: Dict[str, Callable] = {
    "ActionLogged": handle_action_logged,
    "ReplayTriggered": handle_replay_triggered,
    "StageChanged": handle_stage_changed,
    "StressUpdated": handle_stress_updated,
    "MediaAnalyzed": handle_media_analyzed,
    "WeatherUpdated": handle_weather_updated,
}


def get_handler(event_type: str) -> Optional[Callable]:
    """Get the handler function for a given event type."""
    return _HANDLER_MAP.get(event_type)
