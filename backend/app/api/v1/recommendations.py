"""
Recommendations API

GET /api/v1/crops/{crop_id}/recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationStatusUpdateRequest,
    RecommendationStatusUpdateResponse,
)
from app.services.recommendations.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/crops", tags=["Recommendations"])


@router.get(
    "/{crop_id}/recommendations",
    response_model=list[RecommendationResponse],
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def get_recommendations(
    crop_id: UUID,
    on_demand: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prioritized recommendations for a crop instance. Owner only."""
    # Ownership check
    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    if current_user.role != "admin" and crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this crop",
        )

    engine = RecommendationEngine(db)
    recs = engine.ensure_recommendations(crop_id) if on_demand else engine.get_recommendations(crop_id)
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.patch(
    "/{crop_id}/recommendations/{recommendation_id}/dismiss",
    response_model=RecommendationStatusUpdateResponse,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def dismiss_recommendation(
    crop_id: UUID,
    recommendation_id: UUID,
    request: RecommendationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss a recommendation for an owned crop instance."""
    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    if current_user.role != "admin" and crop.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this crop")

    engine = RecommendationEngine(db)
    try:
        rec = engine.update_status(crop_id, recommendation_id, "dismissed", reason=request.reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RecommendationStatusUpdateResponse(
        id=str(rec.id),
        crop_instance_id=str(rec.crop_instance_id),
        status=rec.status,
        updated_at=rec.updated_at,
        reason=request.reason,
    )


@router.patch(
    "/{crop_id}/recommendations/{recommendation_id}/act",
    response_model=RecommendationStatusUpdateResponse,
    dependencies=[Depends(require_role(["farmer", "admin"]))],
)
async def mark_recommendation_acted(
    crop_id: UUID,
    recommendation_id: UUID,
    request: RecommendationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a recommendation as acted/completed for an owned crop instance."""
    crop = db.query(CropInstance).filter(
        CropInstance.id == crop_id,
        CropInstance.is_deleted == False,
    ).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    if current_user.role != "admin" and crop.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this crop")

    engine = RecommendationEngine(db)
    try:
        rec = engine.update_status(crop_id, recommendation_id, "acted", reason=request.reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RecommendationStatusUpdateResponse(
        id=str(rec.id),
        crop_instance_id=str(rec.crop_instance_id),
        status=rec.status,
        updated_at=rec.updated_at,
        reason=request.reason,
    )

