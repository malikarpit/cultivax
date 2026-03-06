"""
Equipment Schemas

Pydantic schemas for Equipment CRUD operations.
Separated from service_provider.py per workflow.md Day 6.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class EquipmentCreate(BaseModel):
    equipment_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    daily_rate: Optional[float] = Field(None, ge=0)
    condition: str = "good"


class EquipmentResponse(BaseModel):
    id: UUID
    provider_id: UUID
    equipment_type: str
    name: str
    description: Optional[str]
    is_available: bool
    hourly_rate: Optional[float]
    daily_rate: Optional[float]
    condition: str
    created_at: datetime

    class Config:
        from_attributes = True
