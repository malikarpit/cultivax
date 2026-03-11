"""
DB-Backed Event Dispatcher

Concrete event dispatcher using PostgreSQL event_log table.
Implements idempotent publish, partition-keyed FIFO processing,
and SELECT FOR UPDATE SKIP LOCKED concurrency.
TDD Section 3.3–3.12.
"""

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
