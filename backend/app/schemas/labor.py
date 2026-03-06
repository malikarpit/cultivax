"""
Labor Schemas

Pydantic schemas for Labor resource CRUD operations.
MSDD Section 2.6.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class LaborCreate(BaseModel):
    labor_type: str = Field(..., min_length=1)
    description: Optional[str] = None
    available_units: int = Field(1, ge=1)
    daily_rate: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    region: str = Field(..., min_length=1)
    sub_region: Optional[str] = None


class LaborResponse(BaseModel):
    id: UUID
    provider_id: UUID
    labor_type: str
    description: Optional[str]
    available_units: int
    daily_rate: Optional[float]
    hourly_rate: Optional[float]
    region: str
    sub_region: Optional[str]
    is_available: bool
    is_flagged: bool
    created_at: datetime

    class Config:
        from_attributes = True
