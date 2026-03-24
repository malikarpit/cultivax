"""
DB-Backed Event Dispatcher

Concrete event dispatcher using PostgreSQL event_log table.
Implements idempotent publish, partition-keyed FIFO processing,
SELECT FOR UPDATE SKIP LOCKED concurrency, and background
polling loop with crash recovery.
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


class DBEventDispatcher(EventDispatcherInterface):
    """DB-backed event dispatcher with idempotency and partitioned FIFO."""

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
    ) -> UUID:
        """
        Publish an event to the event_log table.
        Idempotent: duplicate event_hash is silently skipped.
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
        )
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
        events = self.db.query(EventLog).filter(
            EventLog.status == "Created",
        ).order_by(
            EventLog.partition_key,
            EventLog.created_at,
        ).limit(batch_size).with_for_update(skip_locked=True).all()

        processed_count = 0
        for event in events:
            try:
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

            except Exception as e:
                event.retry_count += 1
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
