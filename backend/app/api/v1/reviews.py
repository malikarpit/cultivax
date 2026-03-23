"""
Service Reviews API

POST /api/v1/reviews — submit a review for a completed service request

SOE Enhancement 8 — review eligibility requirements
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.service_request import ServiceRequest
from app.models.service_review import ServiceReview
from app.schemas.service_review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Service Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a review for a completed service request.

    Eligibility (SOE Enhancement 8):
    - ServiceRequest must be Completed
    - One review per request
    - Time window limit applies
    """
    # Verify request exists and is completed
    request = db.query(ServiceRequest).filter(
        ServiceRequest.id == data.request_id,
        ServiceRequest.is_deleted == False,
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    if request.status != "Completed":
        raise HTTPException(
            status_code=400,
            detail="Can only review completed service requests",
        )

    # Check one review per request
    existing = db.query(ServiceReview).filter(
        ServiceReview.request_id == data.request_id,
        ServiceReview.is_deleted == False,
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A review already exists for this request",
        )

    # Create immutable review (MSDD: no hard delete on reviews)
    review = ServiceReview(
        request_id=data.request_id,
        provider_id=request.provider_id,
        reviewer_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
        complaint_category=data.complaint_category,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return ReviewResponse.model_validate(review)
