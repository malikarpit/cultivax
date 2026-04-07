"""
Event Dispatcher Interface

Abstract interface for event dispatching. Concrete implementations
can be DB-backed, Redis-backed, etc.
TDD Section 3.3.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID


class EventDispatcherInterface(ABC):
    """Abstract event dispatcher contract."""

    @abstractmethod
    def publish(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        payload: Dict[str, Any],
        partition_key: Optional[UUID] = None,
    ) -> UUID:
        """
        Publish an event to the event store.

        Args:
            event_type: Type of event (ActionLogged, ReplayTriggered, etc.)
            entity_type: What entity this event is about (crop_instance, user, etc.)
            entity_id: ID of the entity
            payload: Event payload data
            partition_key: Key for FIFO ordering (defaults to entity_id)

        Returns:
            event_id: UUID of the created event
        """
        pass

    @abstractmethod
    def process_pending(self, batch_size: int = 10) -> int:
        """
        Process pending events in partition-key FIFO order.

        Returns:
            Number of events processed
        """
        pass
