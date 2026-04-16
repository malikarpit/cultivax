"""
Service Request Service

Business logic for service request lifecycle: matchmaking,
state transitions, and event emission.

SOE Enhancement 7 — emit ServiceRequestEvent on each state change.
SOE Enhancement 8 — review eligibility verification.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_request_event import ServiceRequestEvent
from app.schemas.service_request import ServiceRequestCreate

logger = logging.getLogger(__name__)

# Valid state transitions for service requests
VALID_REQUEST_TRANSITIONS = {
    "Pending": ["Accepted", "Declined", "Cancelled", "Expired"],
    "Accepted": ["InProgress", "Cancelled", "Expired"],
    "InProgress": ["Completed", "Failed", "Cancelled"],
    "Completed": [],
    "Cancelled": [],
    "Declined": [],
    "Failed": [],
    "Expired": [],
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
        provider = (
            self.db.query(ServiceProvider)
            .filter(
                ServiceProvider.id == data.provider_id,
                ServiceProvider.is_deleted == False,
            )
            .first()
        )
        if not provider:
            raise ValueError("Provider not found")
        if provider.is_suspended:
            raise ValueError("Provider is suspended")

        existing = (
            self.db.query(ServiceRequest)
            .filter(
                ServiceRequest.farmer_id == farmer_id,
                ServiceRequest.provider_id == data.provider_id,
                ServiceRequest.service_type == data.service_type,
                ServiceRequest.status.in_(["Pending", "Accepted", "InProgress"]),
                ServiceRequest.is_deleted == False,
            )
            .first()
        )

        if existing:
            raise ValueError(
                f"You already have an active request ({existing.status}) "
                f"for '{data.service_type}' with this provider."
            )

        request = ServiceRequest(
            farmer_id=farmer_id,
            provider_id=data.provider_id,
            service_type=data.service_type,
            description=data.description,
            preferred_date=data.preferred_date,
            region=data.region,
            crop_instance_id=data.crop_instance_id,
            urgency=data.urgency or "normal",
            agreed_price=data.agreed_price,
            status="Pending",
        )
        self.db.add(request)
        self.db.flush()

        # Emit creation event
        self._emit_event(request, None, "Pending", farmer_id, "farmer")

        self.db.commit()
        self.db.refresh(request)

        logger.info(f"Service request {request.id} created by farmer {farmer_id}")
        return request

    def accept_request(
        self, request_id: UUID, provider_id: UUID, actor_id: UUID
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

        self._emit_event(request, old_status, "Accepted", actor_id, "provider")

        self.db.commit()
        self.db.refresh(request)

        logger.info(f"Service request {request_id} accepted by provider {provider_id}")
        return request

    def complete_request(self, request_id: UUID, actor_id: UUID) -> ServiceRequest:
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

    def decline_request(self, request_id: UUID, actor_id: UUID) -> ServiceRequest:
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")
        self._validate_transition(request.status, "Declined")
        old_status = request.status
        request.status = "Declined"
        self._emit_event(request, old_status, "Declined", actor_id, "provider")
        self.db.commit()
        self.db.refresh(request)
        return request

    def cancel_request(
        self, request_id: UUID, actor_id: UUID, role: str
    ) -> ServiceRequest:
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")
        self._validate_transition(request.status, "Cancelled")
        old_status = request.status
        request.status = "Cancelled"
        self._emit_event(request, old_status, "Cancelled", actor_id, role)
        self.db.commit()
        self.db.refresh(request)
        return request

    def start_request(self, request_id: UUID, actor_id: UUID) -> ServiceRequest:
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")
        self._validate_transition(request.status, "InProgress")
        old_status = request.status
        request.status = "InProgress"
        self._emit_event(request, old_status, "InProgress", actor_id, "provider")
        self.db.commit()
        self.db.refresh(request)
        return request

    def fail_request(self, request_id: UUID, actor_id: UUID) -> ServiceRequest:
        request = self._get_request(request_id)
        if not request:
            raise LookupError(f"Service request {request_id} not found")
        self._validate_transition(request.status, "Failed")
        old_status = request.status
        request.status = "Failed"
        self._emit_event(request, old_status, "Failed", actor_id, "provider")
        self.db.commit()
        self.db.refresh(request)
        return request

    def _get_request(self, request_id: UUID) -> Optional[ServiceRequest]:
        return (
            self.db.query(ServiceRequest)
            .filter(
                ServiceRequest.id == request_id,
                ServiceRequest.is_deleted == False,
            )
            .first()
        )

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
            transitioned_at=datetime.now(timezone.utc),
        )
        self.db.add(event)
