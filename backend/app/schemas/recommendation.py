"""
Recommendation Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RecommendationStatusUpdateRequest(BaseModel):
    reason: Optional[str] = None


class RecommendationStatusUpdateResponse(BaseModel):
    id: str
    crop_instance_id: str
    status: str
    updated_at: datetime
    reason: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: UUID
    crop_instance_id: UUID
    recommendation_type: str
    priority_rank: int
    message_key: str
    message_parameters: Optional[dict]
    basis: Optional[str]
    rationale: Optional[dict] = None  # FR-9: structured rationale
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationOverrideRequest(BaseModel):
    """FR-7: Request body for overriding a recommendation."""
    action: str  # dismissed | ignored | acted_differently
    reason: Optional[str] = None


class RecommendationOverrideResponse(BaseModel):
    """FR-8: Response for override tracking."""
    id: UUID
    recommendation_id: UUID
    crop_instance_id: UUID
    farmer_id: UUID
    override_action: str
    farmer_reason: Optional[str] = None
    original_recommendation_type: str
    original_priority_rank: int
    created_at: datetime

    class Config:
        from_attributes = True
