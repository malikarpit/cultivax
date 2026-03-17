"""
Service Request API

Service request lifecycle endpoints.
POST /api/v1/service-requests
PUT  /api/v1/service-requests/{id}/accept
PUT  /api/v1/service-requests/{id}/complete
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.service_request import ServiceRequestCreate, ServiceRequestResponse
from app.services.soe.request_service import RequestService

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.post("/", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new service request."""
    service = RequestService(db)
    try:
        request = service.create_request(current_user.id, data)
        return ServiceRequestResponse.model_validate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{request_id}/accept")
async def accept_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provider accepts a service request."""
    service = RequestService(db)
    try:
        result = service.accept_request(request_id, current_user.id)
        return {"status": "accepted", "request_id": str(request_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{request_id}/complete")
async def complete_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a service request as completed."""
    service = RequestService(db)
    try:
        result = service.complete_request(request_id, current_user.id)
        return {"status": "completed", "request_id": str(request_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
