"""
DB-Backed Event Dispatcher v2

Concrete event dispatcher using PostgreSQL event_log table.
Implements idempotent publish, partition-keyed FIFO processing,
SELECT FOR UPDATE SKIP LOCKED concurrency, and background
polling loop with crash recovery.

Hardening:
  - Priority-based processing (MSDD 3.8)
  - Schema versioning (Patch 1.1)
  - Correlation ID propagation (Patch 1.2)
  - Event expiry policy (MSDD Enh Sec 3)
  - Circuit breaker per handler (Ed Enh 7)
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.event_log import EventLog
from app.services.event_dispatcher.interface import EventDispatcherInterface
from app.services.event_dispatcher.handlers import get_handler

logger = logging.getLogger(__name__)

# Event expiry config (MSDD Enh Sec 3)
DEFAULT_MAX_AGE_MINUTES = 60  # Default max processing age
EVENT_MAX_AGE_OVERRIDES = {
    "AlertCreated": 30,
    "WeatherUpdated": 15,
    "MediaAnalyzed": 120,
}

# Circuit breaker config (Ed Enh 7)
CIRCUIT_BREAKER_THRESHOLD = 5  # Consecutive failures to trip
CIRCUIT_BREAKER_RESET_SECONDS = 300  # 5 minutes


class DBEventDispatcher(EventDispatcherInterface):
    """DB-backed event dispatcher with idempotency and partitioned FIFO."""

    # Class-level circuit breaker state (per handler)
    _circuit_state: Dict[str, Dict[str, Any]] = {}

    def __init__(self, db: Session):
        self.db = db

    def _compute_event_hash(
        self,
        event_type: str,
        entity_id: UUID,
        payload: Dict[str, Any],
    ) -> str:
        """Compute a unique hash for idempotent event deduplication."""
        raw = f"{event_type}:{entity_id}:{json.dumps(payload, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def publish(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        payload: Dict[str, Any],
        partition_key: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
        schema_version: int = 1,
    ) -> UUID:
        """
        Publish an event to the event_log table.
        Idempotent: duplicate event_hash is silently skipped.
        Supports correlation ID propagation (Patch 1.2) and schema versioning (Patch 1.1).
        """
        event_hash = self._compute_event_hash(event_type, entity_id, payload)

        # Check for duplicate
        existing = self.db.query(EventLog).filter(
            EventLog.event_hash == event_hash
        ).first()
        if existing:
            logger.info(f"Duplicate event skipped: {event_hash[:12]}...")
            return existing.id

        event = EventLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            partition_key=partition_key or entity_id,
            event_hash=event_hash,
            status="Created",
            # Phase 4B: schema versioning (Patch 1.1)
            schema_version=schema_version,
        )

        # Correlation ID propagation (Patch 1.2)
        if correlation_id:
            event.payload = {**payload, "_correlation_id": correlation_id}

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.info(f"Event published: {event_type} for {entity_type}/{entity_id}")
        return event.id

    def process_pending(self, batch_size: int = 10) -> int:
        """
        Process pending events using SELECT FOR UPDATE SKIP LOCKED.
        Processes in FIFO order per partition_key.
        """
        # Get oldest pending events, locking rows
        # Phase 4B: Priority-based processing (MSDD 3.8)
        events = self.db.query(EventLog).filter(
            EventLog.status == "Created",
        ).order_by(
            EventLog.priority.desc(),     # Higher priority first
            EventLog.created_at.asc(),    # Then oldest first (FIFO)
        ).limit(batch_size).with_for_update(skip_locked=True).all()

        processed_count = 0
        for event in events:
            try:
                # Event expiry check (MSDD Enh Sec 3)
                if self._is_expired(event):
                    event.status = "DeadLetter"
                    event.failure_reason = "Event expired (exceeded max processing age)"
                    logger.warning(f"Event {event.id} expired, moved to DeadLetter")
                    continue

                # Circuit breaker check (Ed Enh 7)
                if self._is_circuit_open(event.event_type):
                    event.status = "Created"  # Leave for later retry
                    logger.warning(
                        f"Circuit breaker OPEN for {event.event_type}, skipping event {event.id}"
                    )
                    continue

                event.status = "Processing"
                self.db.flush()

                # Get and execute handler
                handler = get_handler(event.event_type)
                if handler:
                    handler(self.db, event)
                else:
                    logger.warning(f"No handler for event type: {event.event_type}")

                event.status = "Completed"
                event.processed_at = datetime.now(timezone.utc)
                processed_count += 1

                # Reset circuit breaker on success
                self._record_success(event.event_type)

            except Exception as e:
                event.retry_count += 1
                # Record failure for circuit breaker
                self._record_failure(event.event_type)

                if event.retry_count >= event.max_retries:
                    event.status = "DeadLetter"
                    event.failure_reason = str(e)
                    logger.error(f"Event {event.id} moved to DeadLetter: {e}")
                else:
                    event.status = "Created"  # Reset for retry
                    event.failure_reason = str(e)
                    logger.warning(f"Event {event.id} retry {event.retry_count}: {e}")

        self.db.commit()
        return processed_count

    @classmethod
    def reset_stale_processing(cls, db: Session) -> int:
        """
        Crash recovery: reset events stuck in 'Processing' back to 'Created'.

        On startup, any events left in 'Processing' status indicate the server
        crashed mid-processing. These are safely reset for re-processing.
        """
        stale_events = db.query(EventLog).filter(
            EventLog.status == "Processing",
        ).all()

        reset_count = 0
        for event in stale_events:
            event.status = "Created"
            event.failure_reason = "Reset after server restart (crash recovery)"
            reset_count += 1

        if reset_count > 0:
            db.commit()
            logger.warning(
                f"Crash recovery: reset {reset_count} stale Processing events to Created"
            )

        return reset_count

    async def run_processing_loop(
        self,
        interval_seconds: float = 5.0,
        shutdown_event: Optional[asyncio.Event] = None,
    ) -> None:
        """
        Long-running async loop that polls for pending events.

        Runs process_pending() at a configurable interval. Handles exceptions
        gracefully to prevent the loop from crashing. Supports cancellation
        via shutdown_event or asyncio.CancelledError.

        Args:
            interval_seconds: Polling interval in seconds (default 5.0).
            shutdown_event: Optional asyncio.Event to signal graceful shutdown.
        """
        logger.info(
            f"Background event processor started (interval={interval_seconds}s)"
        )

        while True:
            # Check for shutdown signal
            if shutdown_event and shutdown_event.is_set():
                logger.info("Shutdown signal received, stopping event processor")
                break

            try:
                processed = self.process_pending(batch_size=10)
                if processed > 0:
                    logger.info(f"Event processor cycle: processed {processed} events")
            except Exception as e:
                logger.error(f"Event processor cycle error: {e}", exc_info=True)

            try:
                if shutdown_event:
                    # Wait with shutdown awareness
                    try:
                        await asyncio.wait_for(
                            shutdown_event.wait(), timeout=interval_seconds
                        )
                        # If we get here, shutdown was signaled
                        logger.info("Shutdown signal received during wait")
                        break
                    except asyncio.TimeoutError:
                        pass  # Normal timeout, continue loop
                else:
                    await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                logger.info("Event processor task cancelled")
                break

        logger.info("Background event processor stopped")

    # --- Phase 4B: Event Expiry (MSDD Enh Sec 3) ---

    def _is_expired(self, event: EventLog) -> bool:
        """Check if an event has exceeded its max processing age."""
        if not event.created_at:
            return False
        max_age = EVENT_MAX_AGE_OVERRIDES.get(
            event.event_type, DEFAULT_MAX_AGE_MINUTES
        )
        age_minutes = (
            datetime.now(timezone.utc) - event.created_at.replace(tzinfo=timezone.utc)
        ).total_seconds() / 60
        return age_minutes > max_age

    # --- Phase 4B: Circuit Breaker (Ed Enh 7) ---

    @classmethod
    def _is_circuit_open(cls, event_type: str) -> bool:
        """Check if the circuit breaker is tripped for a given handler."""
        state = cls._circuit_state.get(event_type)
        if not state:
            return False
        if state.get("open", False):
            # Check if cooldown has elapsed
            tripped_at = state.get("tripped_at")
            if tripped_at:
                elapsed = (datetime.now(timezone.utc) - tripped_at).total_seconds()
                if elapsed >= CIRCUIT_BREAKER_RESET_SECONDS:
                    # Reset the breaker (half-open → allow retry)
                    state["open"] = False
                    state["consecutive_failures"] = 0
                    logger.info(f"Circuit breaker RESET for {event_type}")
                    return False
            return True
        return False

    @classmethod
    def _record_failure(cls, event_type: str):
        """Record a handler failure for circuit breaker tracking."""
        if event_type not in cls._circuit_state:
            cls._circuit_state[event_type] = {
                "consecutive_failures": 0,
                "open": False,
                "tripped_at": None,
            }
        state = cls._circuit_state[event_type]
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

        if state["consecutive_failures"] >= CIRCUIT_BREAKER_THRESHOLD:
            state["open"] = True
            state["tripped_at"] = datetime.now(timezone.utc)
            logger.error(
                f"Circuit breaker TRIPPED for {event_type} "
                f"after {state['consecutive_failures']} consecutive failures"
            )

    @classmethod
    def _record_success(cls, event_type: str):
        """Record a handler success — resets consecutive failure count."""
        if event_type in cls._circuit_state:
            cls._circuit_state[event_type]["consecutive_failures"] = 0
            cls._circuit_state[event_type]["open"] = False

