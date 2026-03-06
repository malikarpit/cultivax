"""
Service Review Schemas

Pydantic schemas for Service Reviews and Complaints.
Separated from service_provider.py per workflow.md Day 6.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReviewCreate(BaseModel):
    request_id: UUID
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None
    complaint_category: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    request_id: UUID
    reviewer_id: UUID
    rating: float
    comment: Optional[str]
    complaint_category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
