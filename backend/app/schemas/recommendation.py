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
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
