"""
Event Handlers

Maps event types to handler functions.
Handlers are called by the Event Dispatcher when processing events.
TDD Section 3.5–3.12.
"""

import logging
from typing import Callable, Optional, Dict
from sqlalchemy.orm import Session

from app.models.event_log import EventLog

logger = logging.getLogger(__name__)


def handle_action_logged(db: Session, event: EventLog):
    """Handle ActionLogged event — trigger stage progression check."""
    logger.info(f"Processing ActionLogged for entity {event.entity_id}")
    # TODO: Day 12–13 — integrate with Replay Engine + State Machine


def handle_replay_triggered(db: Session, event: EventLog):
    """Handle ReplayTriggered event — run full or incremental replay."""
    logger.info(f"Processing ReplayTriggered for entity {event.entity_id}")
    # TODO: Day 12 — implement replay logic


def handle_stress_updated(db: Session, event: EventLog):
    """Handle StressUpdated event — recalculate risk index."""
    logger.info(f"Processing StressUpdated for entity {event.entity_id}")
    # TODO: Day 14 — integrate with stress engine


def handle_media_analyzed(db: Session, event: EventLog):
    """Handle MediaAnalyzed event — update crop stress from media signals."""
    logger.info(f"Processing MediaAnalyzed for entity {event.entity_id}")
    # TODO: Day 13 — integrate with media analysis


def handle_weather_updated(db: Session, event: EventLog):
    """Handle WeatherUpdated event — feed weather data into stress model."""
    logger.info(f"Processing WeatherUpdated for entity {event.entity_id}")
    # TODO: Day 14 — integrate with weather service


# Event type → handler mapping
_HANDLER_MAP: Dict[str, Callable] = {
    "ActionLogged": handle_action_logged,
    "ReplayTriggered": handle_replay_triggered,
    "StressUpdated": handle_stress_updated,
    "MediaAnalyzed": handle_media_analyzed,
    "WeatherUpdated": handle_weather_updated,
}


def get_handler(event_type: str) -> Optional[Callable]:
    """Get the handler function for a given event type."""
    return _HANDLER_MAP.get(event_type)
