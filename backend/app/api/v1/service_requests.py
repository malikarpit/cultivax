"""
Service Request API

Service request lifecycle endpoints.
POST /api/v1/service-requests             — farmer creates a request
PUT  /api/v1/service-requests/{id}/accept  — provider accepts
PUT  /api/v1/service-requests/{id}/start   — provider starts work
PUT  /api/v1/service-requests/{id}/complete — provider completes
POST /api/v1/service-requests/{id}/review  — farmer submits review (API-0128)

MSDD 2.7 — Service Request Lifecycle
TDD-8-C0033, TDD-8-C0034 — complete and review endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.service_request import (ServiceRequestCreate,
                                         ServiceRequestResponse)
from app.services.soe.request_service import RequestService

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


def _resolve_provider_profile(db: Session, user: User) -> ServiceProvider:
    """Resolve provider profile from authenticated provider user."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.user_id == user.id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No provider profile found. Create one first.",
        )
    if provider.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your provider account is suspended",
        )
    return provider


def _resolve_request_for_provider(
    db: Session,
    request_id: UUID,
    provider_id: UUID,
) -> ServiceRequest:
    """Load request and ensure it is assigned to the acting provider profile."""
    request = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.id == request_id,
            ServiceRequest.is_deleted == False,
        )
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")
    if request.provider_id != provider_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this request",
        )
    return request


@router.post(
    "/",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer"]))],
)
async def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new service request. Farmer only (MSDD §2.7)."""
    service = RequestService(db)
    try:
        request = service.create_request(current_user.id, data)
        return ServiceRequestResponse.model_validate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=PaginatedResponse[ServiceRequestResponse],
)
async def list_service_requests(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List service requests tailored accurately to user scope."""
    query = db.query(ServiceRequest).filter(ServiceRequest.is_deleted == False)

    is_farmer = current_user.role == "farmer"
    provider = (
        db.query(ServiceProvider)
        .filter(ServiceProvider.user_id == current_user.id)
        .first()
    )

    if is_farmer:
        query = query.filter(ServiceRequest.farmer_id == current_user.id)
    elif provider:
        query = query.filter(ServiceRequest.provider_id == provider.id)
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Unrecognized role structure")

    from app.models.service_review import ServiceReview

    total = query.count()
    items = (
        query.order_by(ServiceRequest.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    reviewed_ids = set()
    if items:
        reviewed_reqs = (
            db.query(ServiceReview.request_id)
            .filter(
                ServiceReview.request_id.in_([r.id for r in items]),
                ServiceReview.is_deleted == False,
            )
            .all()
        )
        reviewed_ids = {r[0] for r in reviewed_reqs}

    enriched = []
    for req in items:
        base = ServiceRequestResponse.model_validate(req).dict()

        # Capability Mapping
        status = req.status
        is_my_prov = provider and req.provider_id == provider.id

        base["can_accept"] = status == "Pending" and is_my_prov
        base["can_decline"] = status == "Pending" and is_my_prov
        base["can_start"] = status == "Accepted" and is_my_prov
        base["can_complete"] = status == "InProgress" and is_my_prov
        base["can_cancel"] = status in ["Pending", "Accepted"] and (
            is_farmer or is_my_prov
        )
        base["has_reviewed"] = req.id in reviewed_ids

        enriched.append(ServiceRequestResponse(**base))

    return PaginatedResponse(
        items=enriched,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.put(
    "/{request_id}/accept",
    dependencies=[Depends(require_role(["provider"]))],
)
async def accept_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Provider accepts a service request (MSDD §2.7.1).

    Verifies the provider profile exists and writes the correct
    service_providers.id (not users.id) into the FK.
    """
    provider = _resolve_provider_profile(db, current_user)
    _resolve_request_for_provider(db, request_id, provider.id)

    service = RequestService(db)
    try:
        service.accept_request(request_id, provider.id, current_user.id)
        return {"status": "accepted", "request_id": str(request_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/{request_id}/complete",
    dependencies=[Depends(require_role(["provider"]))],
)
async def complete_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a service request as completed (MSDD §2.7.1).

    Only the assigned provider can complete a request.
    """
    provider = _resolve_provider_profile(db, current_user)
    _resolve_request_for_provider(db, request_id, provider.id)

    service = RequestService(db)
    try:
        service.complete_request(request_id, current_user.id)
        return {"status": "completed", "request_id": str(request_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{request_id}/decline", dependencies=[Depends(require_role(["provider"]))])
async def decline_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = _resolve_provider_profile(db, current_user)
    _resolve_request_for_provider(db, request_id, provider.id)
    service = RequestService(db)
    try:
        service.decline_request(request_id, current_user.id)
        return {"status": "declined"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{request_id}/cancel")
async def cancel_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.id == request_id,
            ServiceRequest.is_deleted == False,
        )
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    if current_user.role == "farmer":
        if request.farmer_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not own this request")
    elif current_user.role == "provider":
        provider = _resolve_provider_profile(db, current_user)
        if request.provider_id != provider.id:
            raise HTTPException(
                status_code=403, detail="You are not assigned to this request"
            )
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    service = RequestService(db)
    try:
        service.cancel_request(request_id, current_user.id, current_user.role)
        return {"status": "cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{request_id}/start", dependencies=[Depends(require_role(["provider"]))])
async def start_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = _resolve_provider_profile(db, current_user)
    _resolve_request_for_provider(db, request_id, provider.id)
    service = RequestService(db)
    try:
        service.start_request(request_id, current_user.id)
        return {"status": "in_progress"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{request_id}/fail", dependencies=[Depends(require_role(["provider"]))])
async def fail_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = _resolve_provider_profile(db, current_user)
    _resolve_request_for_provider(db, request_id, provider.id)
    service = RequestService(db)
    try:
        service.fail_request(request_id, current_user.id)
        return {"status": "failed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{request_id}/complete",
    dependencies=[Depends(require_role(["provider"]))],
    summary="Compatibility alias for clients using POST complete",
)
async def complete_service_request_post_alias(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compatibility alias for legacy/doc clients that use POST for completion.
    """
    return await complete_service_request(
        request_id=request_id,
        db=db,
        current_user=current_user,
    )


@router.post(
    "/{request_id}/review",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer"]))],
    tags=["Service Reviews"],
    summary="Submit review for a completed service request (API-0128)",
)
async def review_service_request(
    request_id: UUID,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convenience route: POST /service-requests/{id}/review

    Delegates to the Reviews service, binding the request_id from the path.
    Equivalent to POST /reviews/ with request_id pre-set.

    MSDD API-0128 / TDD-8-C0034
    """
    from app.api.v1.reviews import submit_review
    from app.schemas.service_review import ReviewCreate

    # Merge path param into body
    review_data = ReviewCreate(
        request_id=request_id,
        rating=data.get("rating"),
        comment=data.get("comment"),
        complaint_category=data.get("complaint_category"),
    )
    return await submit_review(data=review_data, db=db, current_user=current_user)
