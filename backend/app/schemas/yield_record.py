"""
Yield Record Schemas

Pydantic schemas for Yield submission and response.
Separated from crop_instance.py per workflow.md Day 6.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class YieldSubmission(BaseModel):
    reported_yield: float = Field(..., gt=0)
    yield_unit: str = "kg/acre"
    harvest_date: Optional[date] = None


class YieldResponse(BaseModel):
    id: UUID
    crop_instance_id: UUID
    reported_yield: float
    yield_unit: str
    harvest_date: Optional[date]
    ml_yield_value: Optional[float]
    biological_cap: Optional[float]
    bio_cap_applied: bool
    yield_verification_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
