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
from app.models.crop_instance import CropInstance
# ReplayEngine is imported lazily inside handler functions to avoid circular import:
# replay_engine → weather.py → weather_service → db_dispatcher → handlers → replay_engine
from app.services.ctis.state_machine import (  # type: ignore
    CropStateMachine,
    get_transition_event_payload,
    InvalidStateTransition,
)
from app.services.recommendations.recommendation_engine import RecommendationEngine
from app.services.notifications import AlertService

logger = logging.getLogger(__name__)


def _generate_replay_alerts(db: Session, crop_instance_id, source_event_id=None):
    """Generate alerts based on replayed crop risk/stress state."""
    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_instance_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        return

    service = AlertService(db)
    if (crop.stress_score or 0.0) >= 70.0:
        service.generate_alert(
            crop_instance_id=crop.id,
            user_id=crop.farmer_id,
            alert_type="stress_alert",
            severity="high",
            urgency_level="High",
            message="Crop stress is high. Immediate corrective action recommended.",
            details={"stress_score": float(crop.stress_score or 0.0), "state": crop.state},
            source_event_id=source_event_id,
            expires_in_hours=24,
        )

    if (crop.risk_index or 0.0) >= 0.6:
        severity = "critical" if (crop.risk_index or 0.0) >= 0.8 else "high"
        urgency = "Critical" if severity == "critical" else "High"
        service.generate_alert(
            crop_instance_id=crop.id,
            user_id=crop.farmer_id,
            alert_type="risk_alert",
            severity=severity,
            urgency_level=urgency,
            message="Crop risk is elevated. Review interventions immediately.",
            details={"risk_index": float(crop.risk_index or 0.0), "state": crop.state},
            source_event_id=source_event_id,
            expires_in_hours=24,
        )

    if crop.state == "ReadyToHarvest":
        service.generate_alert(
            crop_instance_id=crop.id,
            user_id=crop.farmer_id,
            alert_type="harvest_approaching",
            severity="medium",
            urgency_level="Medium",
            message="Crop is ready to harvest. Plan harvest activities.",
            details={"state": crop.state, "stage": crop.stage},
            source_event_id=source_event_id,
            expires_in_hours=72,
        )


def handle_action_logged(db: Session, event: EventLog):
    """
    Handle ActionLogged event — trigger replay for the crop instance.
    Wired in Day 13: ActionLogged → ReplayTriggered pipeline.
    """
    from app.services.ctis.replay_engine import ReplayEngine  # lazy to avoid circular import

    logger.info(f"Processing ActionLogged for entity {event.entity_id}")

    crop_instance_id = None
    if event.payload and isinstance(event.payload, dict):
        crop_instance_id = event.payload.get("crop_instance_id")
    if not crop_instance_id and event.entity_id:
        crop_instance_id = event.entity_id

    if not crop_instance_id:
        logger.error("ActionLogged event missing crop_instance_id")
        return

    engine = ReplayEngine(db)
    loop = asyncio.get_event_loop()
    if loop.is_running():
        raise RuntimeError(
            "ActionLogged replay handler cannot run on an active event loop in sync dispatcher context"
        )

    try:
        loop.run_until_complete(engine.replay_crop_instance(crop_instance_id))
        RecommendationEngine(db).refresh_recommendations(crop_instance_id)
        _generate_replay_alerts(db, crop_instance_id, source_event_id=event.id)
        logger.info(f"Replay completed for crop {crop_instance_id}")
    except Exception as e:
        logger.error(f"Replay failed for crop {crop_instance_id}: {e}")
        raise


def handle_replay_triggered(db: Session, event: EventLog):
    """Handle ReplayTriggered event — run full or incremental replay."""
    from app.services.ctis.replay_engine import ReplayEngine  # lazy to avoid circular import

    logger.info(f"Processing ReplayTriggered for entity {event.entity_id}")

    crop_instance_id = event.entity_id
    if not crop_instance_id:
        logger.error("ReplayTriggered event missing entity_id")
        return

    engine = ReplayEngine(db)
    loop = asyncio.get_event_loop()
    if loop.is_running():
        raise RuntimeError(
            "ReplayTriggered handler cannot run on an active event loop in sync dispatcher context"
        )

    try:
        loop.run_until_complete(engine.replay_crop_instance(crop_instance_id))
        RecommendationEngine(db).refresh_recommendations(crop_instance_id)
        _generate_replay_alerts(db, crop_instance_id, source_event_id=event.id)
    except Exception as e:
        logger.error(f"Replay failed for crop {crop_instance_id}: {e}")
        raise


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
    payload = event.payload or {}
    stress_score = float(payload.get("stress_score", 0.0))
    if stress_score < 70.0 or not event.entity_id:
        return

    crop = db.query(CropInstance).filter(
        CropInstance.id == event.entity_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        return

    AlertService(db).generate_alert(
        crop_instance_id=crop.id,
        user_id=crop.farmer_id,
        alert_type="stress_alert",
        severity="high",
        urgency_level="High",
        message="High stress detected from stress update event.",
        details={"stress_score": stress_score},
        source_event_id=event.id,
        expires_in_hours=24,
    )


def handle_media_analyzed(db: Session, event: EventLog):
    """Handle MediaAnalyzed event — update crop stress from media signals."""
    logger.info(f"Processing MediaAnalyzed for entity {event.entity_id}")
    payload = event.payload or {}
    pest_detected = bool(payload.get("pest_detected", False))
    pest_risk = float(payload.get("pest_risk", 0.0))
    if not event.entity_id or (not pest_detected and pest_risk < 0.7):
        return

    crop = db.query(CropInstance).filter(
        CropInstance.id == event.entity_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        return

    AlertService(db).generate_alert(
        crop_instance_id=crop.id,
        user_id=crop.farmer_id,
        alert_type="pest_alert",
        severity="high",
        urgency_level="High",
        message="Pest risk detected from media analysis.",
        details={"pest_detected": pest_detected, "pest_risk": pest_risk},
        source_event_id=event.id,
        expires_in_hours=24,
    )


def handle_weather_updated(db: Session, event: EventLog):
    """Handle WeatherUpdated event — feed weather data into stress model."""
    logger.info(f"Processing WeatherUpdated for entity {event.entity_id}")
    payload = event.payload or {}
    message = payload.get("message") or payload.get("advisory") or "Weather advisory issued."
    severity = (payload.get("severity") or "medium").lower()
    urgency = (payload.get("urgency_level") or "Medium")
    crop_id = payload.get("crop_instance_id") or event.entity_id
    if not crop_id:
        return

    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        return

    AlertService(db).generate_alert(
        crop_instance_id=crop.id,
        user_id=crop.farmer_id,
        alert_type="weather_alert",
        severity=severity,
        urgency_level=urgency,
        message=message,
        details=payload,
        source_event_id=event.id,
        expires_in_hours=12,
    )


from app.services.event_dispatcher.event_types import CTISEvents, MLEvents, NotificationEvents

# Event type → handler mapping
_HANDLER_MAP: Dict[str, Callable] = {
    CTISEvents.ACTION_LOGGED: handle_action_logged,
    CTISEvents.REPLAY_TRIGGERED: handle_replay_triggered,
    CTISEvents.STAGE_CHANGED: handle_stage_changed,
    CTISEvents.STRESS_UPDATED: handle_stress_updated,
    MLEvents.MEDIA_ANALYZED: handle_media_analyzed,
    NotificationEvents.WEATHER_UPDATED: handle_weather_updated,
    # Admin-triggered replay from force-replay endpoint
    "ctis.replay_requested": handle_replay_triggered,
    # Fallback to legacy names for safe transitions of in-flight queued events
    "ActionLogged": handle_action_logged,
    "ReplayTriggered": handle_replay_triggered,
    "StageChanged": handle_stage_changed,
    "StressUpdated": handle_stress_updated,
    "MediaAnalyzed": handle_media_analyzed,
    "WeatherUpdated": handle_weather_updated,
    # Additional namespaced aliases for ML events published pre-taxonomy fix
    "ml.media_analyzed": handle_media_analyzed,
    "notification.weather_updated": handle_weather_updated,
}


def get_handler(event_type: str) -> Optional[Callable]:
    """Get the handler function for a given event type."""
    return _HANDLER_MAP.get(event_type)
