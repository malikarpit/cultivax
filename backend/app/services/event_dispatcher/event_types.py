"""
Event Types Catalog

Formal event type constants for the CultivaX Event Dispatcher.
MSDD Section 3.3 — Centralized taxonomy of all system events.

Usage:
    from app.services.event_dispatcher.event_types import CTISEvents, SOEEvents
    dispatcher.publish(CTISEvents.ACTION_LOGGED, payload={...})
"""


class CTISEvents:
    """Crop Timeline Intelligence System events."""

    ACTION_LOGGED = "ctis.action_logged"
    CROP_STATE_CHANGE_REQUESTED = "ctis.crop_state_change_requested"
    CROP_METRICS_UPDATE_REQUESTED = "ctis.crop_metrics_update_requested"
    REPLAY_TRIGGERED = "ctis.replay_triggered"
    REPLAY_REQUESTED = "ctis.replay_requested"  # FX-EVENTS-P1-0005: admin force-replay
    REPLAY_COMPLETED = "ctis.replay_completed"
    REPLAY_FAILED = "ctis.replay_failed"
    STAGE_CHANGED = "ctis.stage_changed"
    STRESS_UPDATED = "ctis.stress_updated"
    RISK_UPDATED = "ctis.risk_updated"
    YIELD_SUBMITTED = "ctis.yield_submitted"
    SOWING_DATE_MODIFIED = "ctis.sowing_date_modified"
    DRIFT_THRESHOLD_EXCEEDED = "ctis.drift_threshold_exceeded"
    SNAPSHOT_CREATED = "ctis.snapshot_created"
    CROP_CREATED = "ctis.crop_created"
    CROP_ARCHIVED = "ctis.crop_archived"
    RECOVERY_REQUIRED = "ctis.recovery_required"
    SUGGEST_SERVICE = "ctis.suggest_service"  # MSDD 2.11: CTIS→SOE suggestion


class SOEEvents:
    """Service Orchestration Ecosystem events."""

    SERVICE_REQUESTED = "soe.service_requested"
    PROVIDER_CONTACTED = "soe.provider_contacted"
    REQUEST_ACCEPTED = "soe.request_accepted"
    REQUEST_COMPLETED = "soe.request_completed"
    REQUEST_CANCELLED = "soe.request_cancelled"
    REQUEST_DISPUTED = "soe.request_disputed"
    REQUEST_ESCALATED = "soe.request_escalated"
    REVIEW_SUBMITTED = "soe.review_submitted"
    TRUST_SCORE_UPDATED = "soe.trust_score_updated"
    PROVIDER_FLAGGED = "soe.provider_flagged"
    PROVIDER_SUSPENDED = "soe.provider_suspended"


class MLEvents:
    """Machine Learning subsystem events."""

    RISK_COMPUTED = "ml.risk_computed"
    MEDIA_ANALYZED = "ml.media_analyzed"
    CLUSTER_UPDATED = "ml.cluster_updated"
    MODEL_REGISTERED = "ml.model_registered"
    MODEL_ACTIVATED = "ml.model_activated"
    PREDICTION_LOW_CONFIDENCE = "ml.prediction_low_confidence"


class AdminEvents:
    """Administrative action events."""

    USER_ROLE_CHANGED = "admin.user_role_changed"
    PROVIDER_VERIFIED = "admin.provider_verified"
    PROVIDER_SUSPENDED = "admin.provider_suspended"
    FEATURE_TOGGLED = "admin.feature_toggled"
    RULE_TEMPLATE_PUBLISHED = "admin.rule_template_published"
    DEAD_LETTER_RETRIED = "admin.dead_letter_retried"
    ABUSE_FLAGGED = "admin.abuse_flagged"


class NotificationEvents:
    """Notification and alert events."""

    ALERT_GENERATED = "notification.alert_generated"
    ALERT_DELIVERED = "notification.alert_delivered"
    ALERT_ACKNOWLEDGED = "notification.alert_acknowledged"
    RECOMMENDATION_CREATED = "notification.recommendation_created"
    RECOMMENDATION_ACTED = "notification.recommendation_acted"
    WEATHER_UPDATED = "notification.weather_updated"


# All event types for validation
ALL_EVENT_TYPES = (
    [v for k, v in vars(CTISEvents).items() if not k.startswith("_")]
    + [v for k, v in vars(SOEEvents).items() if not k.startswith("_")]
    + [v for k, v in vars(MLEvents).items() if not k.startswith("_")]
    + [v for k, v in vars(AdminEvents).items() if not k.startswith("_")]
    + [v for k, v in vars(NotificationEvents).items() if not k.startswith("_")]
)


def is_valid_event_type(event_type: str) -> bool:
    """Check if an event type string is a recognized system event."""
    return event_type in ALL_EVENT_TYPES
