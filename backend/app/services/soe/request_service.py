"""
Service Request Service

Business logic for service request lifecycle: matchmaking,
state transitions, and event emission.

SOE Enhancement 7 — emit ServiceRequestEvent on each state change.
SOE Enhancement 8 — review eligibility verification.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import logging

from app.models.service_request import ServiceRequest
from app.models.service_request_event import ServiceRequestEvent
from app.models.service_provider import ServiceProvider
from app.schemas.service_request import ServiceRequestCreate

logger = logging.getLogger(__name__)

# Valid state transitions for service requests
VALID_REQUEST_TRANSITIONS = {
    "Pending": ["Accepted", "Cancelled"],
    "Accepted": ["InProgress", "Cancelled"],
    "InProgress": ["Completed", "Cancelled"],
    "Completed": [],
    "Cancelled": [],
}


class RequestService:
    """
    Manages service request lifecycle with state machine enforcement
    and event tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_request(
        self, farmer_id: UUID, data: ServiceRequestCreate
    ) -> ServiceRequest:
        """
        Create a new service request and attempt matchmaking.
        """
        request = ServiceRequest(
            farmer_id=farmer_id,
            service_type=data.service_type,
            description=data.description,
            preferred_date=data.preferred_date,
            region=data.region,
            crop_instance_id=data.crop_instance_id,
            urgency=data.urgency or "normal",
            status="Pending",
        )
        self.db.add(request)

        # Emit creation event
        self._emit_event(request, None, "Pending", farmer_id, "farmer")

        self.db.commit()
        self.db.refresh(request)

        logger.info(f"Service request {request.id} created by farmer {farmer_id}")
        return request

    def accept_request(
        self, request_id: UUID, provider_id: UUID
    ) -> ServiceRequest:
        """Provider accepts a service request."""
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")

        self._validate_transition(request.status, "Accepted")

        old_status = request.status
        request.status = "Accepted"
        request.provider_id = provider_id
        request.provider_acknowledged_at = datetime.now(timezone.utc)

        self._emit_event(request, old_status, "Accepted", provider_id, "provider")

        self.db.commit()
        self.db.refresh(request)

        logger.info(
            f"Service request {request_id} accepted by provider {provider_id}"
        )
        return request

    def complete_request(
        self, request_id: UUID, actor_id: UUID
    ) -> ServiceRequest:
        """Mark a service request as completed."""
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")

        self._validate_transition(request.status, "Completed")

        old_status = request.status
        request.status = "Completed"
        request.completed_at = datetime.now(timezone.utc)

        self._emit_event(request, old_status, "Completed", actor_id, "system")

        self.db.commit()
        self.db.refresh(request)

        logger.info(f"Service request {request_id} completed")
        return request

    def _get_request(self, request_id: UUID) -> Optional[ServiceRequest]:
        return self.db.query(ServiceRequest).filter(
            ServiceRequest.id == request_id,
            ServiceRequest.is_deleted == False,
        ).first()

    def _validate_transition(self, current: str, target: str) -> None:
        valid = VALID_REQUEST_TRANSITIONS.get(current, [])
        if target not in valid:
            raise ValueError(
                f"Invalid transition: '{current}' → '{target}'. "
                f"Valid transitions: {valid}"
            )

    def _emit_event(
        self,
        request: ServiceRequest,
        previous_state: Optional[str],
        new_state: str,
        actor_id: UUID,
        actor_role: str,
    ) -> None:
        """Emit a ServiceRequestEvent (SOE Enhancement 7)."""
        event = ServiceRequestEvent(
            request_id=request.id,
            event_type=f"status_changed_to_{new_state.lower()}",
            previous_state=previous_state,
            new_state=new_state,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        self.db.add(event)
