"""
Recommendations API

GET /api/v1/crops/{crop_id}/recommendations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendations.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/crops", tags=["Recommendations"])


@router.get("/{crop_id}/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prioritized recommendations for a crop instance."""
    engine = RecommendationEngine(db)
    recs = engine.get_recommendations(crop_id)
    return [RecommendationResponse.model_validate(r) for r in recs]
