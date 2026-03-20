"""
Recommendation Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RecommendationResponse(BaseModel):
    id: str
    crop_instance_id: str
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
