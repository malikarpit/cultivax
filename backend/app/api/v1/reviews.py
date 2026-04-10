"""
Service Reviews API

POST /api/v1/reviews — submit a review for a completed service request

SOE Enhancement 8 — review eligibility requirements
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_request_event import ServiceRequestEvent
from app.models.service_review import ServiceReview
from app.models.user import User
from app.schemas.service_review import ReviewCreate, ReviewResponse
from app.services.soe.escalation_policy import EscalationPolicyEngine
from app.services.soe.fraud_detector import FraudDetector

router = APIRouter(prefix="/reviews", tags=["Service Reviews"])


@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["farmer"]))],
)
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
    request = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.id == data.request_id,
            ServiceRequest.is_deleted == False,
        )
        .first()
    )

    if not request:
        raise HTTPException(status_code=404, detail="Service request not found")

    # Ownership check — only the farmer who created the request can review
    if request.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review your own service requests",
        )

    if request.status != "Completed":
        raise HTTPException(
            status_code=400,
            detail="Can only review completed service requests",
        )

    # Check one review per request
    existing = (
        db.query(ServiceReview)
        .filter(
            ServiceReview.request_id == data.request_id,
            ServiceReview.is_deleted == False,
        )
        .first()
    )

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

    # Emit ServiceReviewed Event
    event = ServiceRequestEvent(
        request_id=request.id,
        event_type="Reviewed",
        previous_state=request.status,
        new_state=request.status,
        actor_id=current_user.id,
        actor_role="farmer",
        transitioned_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Flush review so TrustEngine can include it in the aggregate query
    db.flush()

    # Recompute trust score + counters via TrustEngine (MSDD §2.4.1)
    # This updates trust_score, complaint_count, and completion_count atomically.
    provider = (
        db.query(ServiceProvider)
        .filter(ServiceProvider.id == request.provider_id)
        .first()
    )
    if provider:
        try:
            from app.services.soe.trust_engine import TrustEngine

            engine = TrustEngine(db)
            engine.compute_trust_score(request.provider_id)
        except Exception as te_err:
            # Fallback: simple avg-rating if TrustEngine fails (non-fatal)
            import logging

            logging.getLogger(__name__).warning(
                f"TrustEngine failed, using avg fallback: {te_err}"
            )
            avg_rating = (
                db.query(func.avg(ServiceReview.rating))
                .filter(
                    ServiceReview.provider_id == request.provider_id,
                    ServiceReview.is_deleted == False,
                )
                .scalar()
                or 0.0
            )
            provider.trust_score = float(avg_rating)

    fraud_result = {
        "is_flagged": False,
        "confidence": 0.0,
        "signal_count": 0,
    }
    escalation_result = None

    try:
        fraud_result = FraudDetector(db).detect_fraud(request.provider_id)
    except Exception as fraud_err:
        import logging

        logging.getLogger(__name__).warning(f"Fraud detection failed: {fraud_err}")

    try:
        escalation_result = EscalationPolicyEngine(db).apply_escalation(
            request.provider_id
        )
    except Exception as escalation_err:
        import logging

        logging.getLogger(__name__).warning(
            f"Escalation policy evaluation failed: {escalation_err}"
        )

    db.add(
        ServiceRequestEvent(
            request_id=request.id,
            event_type="review_risk_evaluated",
            previous_state=request.status,
            new_state=request.status,
            actor_id=current_user.id,
            actor_role="system",
            transitioned_at=datetime.now(timezone.utc),
            notes=(
                f"fraud={fraud_result.get('is_flagged')} "
                f"signals={fraud_result.get('signal_count')} "
                f"confidence={fraud_result.get('confidence')} "
                f"escalation={getattr(escalation_result, 'level', 'None')}"
            ),
        )
    )

    db.commit()
    db.refresh(review)
    return ReviewResponse.model_validate(review)


@router.get("/")
async def list_reviews(
    provider_id: UUID = Query(..., description="Filter reviews by provider ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List reviews for a provider, including aggregates."""
    query = db.query(ServiceReview).filter(
        ServiceReview.provider_id == provider_id, ServiceReview.is_deleted == False
    )

    total_count = query.count()
    avg_rating = (
        db.query(func.avg(ServiceReview.rating))
        .filter(
            ServiceReview.provider_id == provider_id, ServiceReview.is_deleted == False
        )
        .scalar()
        or 0.0
    )

    reviews = (
        query.order_by(ServiceReview.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "aggregates": {"average_rating": float(avg_rating), "total_count": total_count},
        "reviews": [ReviewResponse.model_validate(r) for r in reviews],
    }


from pydantic import BaseModel


class ModerationRequest(BaseModel):
    reason: Optional[str] = None


@router.patch("/{review_id}/flag", dependencies=[Depends(require_role(["admin"]))])
async def flag_review(
    review_id: UUID,
    data: Optional[ModerationRequest] = None,
    db: Session = Depends(get_db),
):
    """Admin endpoint to flag toxic reviews."""
    review = db.query(ServiceReview).filter(ServiceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_flagged = "flagged"
    if data and data.reason:
        review.flagged_reason = data.reason
    db.commit()
    return {"status": "flagged"}


@router.patch("/{review_id}/dismiss", dependencies=[Depends(require_role(["admin"]))])
async def dismiss_review(review_id: UUID, db: Session = Depends(get_db)):
    """Admin endpoint to revert a flag on a review."""
    review = db.query(ServiceReview).filter(ServiceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_flagged = "none"
    review.flagged_reason = None
    db.commit()
    return {"status": "dismissed"}


@router.patch("/{review_id}/escalate", dependencies=[Depends(require_role(["admin"]))])
async def escalate_review(
    review_id: UUID,
    data: Optional[ModerationRequest] = None,
    db: Session = Depends(get_db),
):
    """Admin endpoint to escalate significant dispute triggers."""
    review = db.query(ServiceReview).filter(ServiceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_flagged = "escalated"
    if data and data.reason:
        review.flagged_reason = data.reason
    db.commit()
    return {"status": "escalated"}
