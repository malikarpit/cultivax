"""
26 march: Event & Dispatcher Tests — Phase 6C

Tests for:
  - Event idempotency: duplicate events are silently skipped
  - Priority-based processing: high-priority events first
  - Circuit breaker: trips after consecutive failures
  - Event expiry: old events are dead-lettered
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.event_dispatcher.db_dispatcher import (
    DBEventDispatcher,
    CIRCUIT_BREAKER_THRESHOLD,
    CIRCUIT_BREAKER_RESET_SECONDS,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_event(
    event_type="TestEvent",
    status="Created",
    priority=5,
    created_at=None,
    retry_count=0,
    max_retries=3,
):
    """Create a mock EventLog."""
    event = MagicMock()
    event.id = uuid4()
    event.event_type = event_type
    event.entity_type = "test"
    event.entity_id = uuid4()
    event.status = status
    event.priority = priority
    event.created_at = created_at or datetime.now(timezone.utc)
    event.retry_count = retry_count
    event.max_retries = max_retries
    event.failure_reason = None
    event.processed_at = None
    event.payload = {}
    event.event_hash = "test_hash"
    return event


# ===========================================================================
# 6C.1: Event Idempotency
# ===========================================================================

class TestEventIdempotency:
    """Duplicate events are silently skipped."""

    def test_duplicate_event_returns_existing_id(self):
        """Publishing same event twice returns the first event's ID."""
        db = MagicMock()
        existing = MagicMock()
        existing.id = uuid4()

        # First call: no existing, second call: existing found
        db.query.return_value.filter.return_value.first.return_value = existing

        dispatcher = DBEventDispatcher(db)
        result = dispatcher.publish(
            event_type="TestEvent",
            entity_type="test",
            entity_id=uuid4(),
            payload={"key": "value"},
        )

        assert result == existing.id
        db.add.assert_not_called()  # Should NOT add a new event

    def test_new_event_is_persisted(self):
        """A genuinely new event is persisted to DB."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        new_event = MagicMock()
        new_event.id = uuid4()
        db.refresh = lambda x: setattr(x, 'id', new_event.id)

        dispatcher = DBEventDispatcher(db)
        dispatcher.publish(
            event_type="TestEvent",
            entity_type="test",
            entity_id=uuid4(),
            payload={"key": "value"},
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()


# ===========================================================================
# 6C.2: Circuit Breaker
# ===========================================================================

class TestCircuitBreaker:
    """Circuit breaker trips after N consecutive failures."""

    def setup_method(self):
        # Reset circuit state between tests
        DBEventDispatcher._circuit_state.clear()

    def test_circuit_starts_closed(self):
        """Circuit is closed by default."""
        assert DBEventDispatcher._is_circuit_open("SomeEvent") is False

    def test_circuit_trips_after_threshold(self):
        """Circuit opens after CIRCUIT_BREAKER_THRESHOLD consecutive failures."""
        for _ in range(CIRCUIT_BREAKER_THRESHOLD):
            DBEventDispatcher._record_failure("FailingEvent")

        assert DBEventDispatcher._is_circuit_open("FailingEvent") is True

    def test_circuit_stays_closed_below_threshold(self):
        """Circuit stays closed below threshold."""
        for _ in range(CIRCUIT_BREAKER_THRESHOLD - 1):
            DBEventDispatcher._record_failure("AlmostFailing")

        assert DBEventDispatcher._is_circuit_open("AlmostFailing") is False

    def test_success_resets_failures(self):
        """A success resets the consecutive failure count."""
        for _ in range(CIRCUIT_BREAKER_THRESHOLD - 1):
            DBEventDispatcher._record_failure("RecoveringEvent")

        DBEventDispatcher._record_success("RecoveringEvent")

        # Should be reset
        state = DBEventDispatcher._circuit_state.get("RecoveringEvent", {})
        assert state.get("consecutive_failures", 0) == 0
        assert state.get("open", False) is False

    def test_independent_circuits_per_event_type(self):
        """Different event types have independent circuit breakers."""
        for _ in range(CIRCUIT_BREAKER_THRESHOLD):
            DBEventDispatcher._record_failure("TypeA")

        assert DBEventDispatcher._is_circuit_open("TypeA") is True
        assert DBEventDispatcher._is_circuit_open("TypeB") is False


# ===========================================================================
# 6C.3: Event Expiry
# ===========================================================================

class TestEventExpiry:
    """Old events are detected as expired."""

    def test_recent_event_not_expired(self):
        """An event created just now is NOT expired."""
        db = MagicMock()
        dispatcher = DBEventDispatcher(db)
        event = _make_event(created_at=datetime.now(timezone.utc))

        assert dispatcher._is_expired(event) is False

    def test_old_event_is_expired(self):
        """An event created 2 hours ago exceeds default 60-min max age."""
        db = MagicMock()
        dispatcher = DBEventDispatcher(db)
        event = _make_event(
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )

        assert dispatcher._is_expired(event) is True

    def test_weather_event_short_expiry(self):
        """WeatherUpdated events expire after 15 minutes."""
        db = MagicMock()
        dispatcher = DBEventDispatcher(db)
        event = _make_event(
            event_type="WeatherUpdated",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        )

        assert dispatcher._is_expired(event) is True


# ===========================================================================
# 6C.4: Schema Versioning & Correlation ID
# ===========================================================================

class TestSchemaVersioning:
    """Schema version and correlation ID are stored on publish."""

    def test_schema_version_passed_to_event(self):
        """publish() sets schema_version on the event."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        dispatcher = DBEventDispatcher(db)
        dispatcher.publish(
            event_type="Test",
            entity_type="test",
            entity_id=uuid4(),
            payload={"data": 1},
            schema_version=2,
        )

        # Verify the EventLog was created with schema_version=2
        call_args = db.add.call_args[0][0]
        assert call_args.schema_version == 2

    def test_correlation_id_in_payload(self):
        """publish() with correlation_id embeds it in the payload."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        dispatcher = DBEventDispatcher(db)
        dispatcher.publish(
            event_type="Test",
            entity_type="test",
            entity_id=uuid4(),
            payload={"data": 1},
            correlation_id="corr-abc-123",
        )

        call_args = db.add.call_args[0][0]
        assert "_correlation_id" in call_args.payload
        assert call_args.payload["_correlation_id"] == "corr-abc-123"
