"""
Equipment Schemas

Pydantic schemas for Equipment CRUD operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class EquipmentType(str, Enum):
    TRACTOR = "tractor"
    HARVESTER = "harvester"
    SPRAYER = "sprayer"
    PLANTER = "planter"
    IRRIGATION = "irrigation"
    OTHER = "other"


class EquipmentCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class EquipmentBase(BaseModel):
    equipment_type: EquipmentType
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    hourly_rate: Optional[float] = Field(None, ge=0)
    daily_rate: Optional[float] = Field(None, ge=0)
    condition: EquipmentCondition = EquipmentCondition.GOOD
    is_available: bool = True


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    equipment_type: Optional[EquipmentType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    hourly_rate: Optional[float] = Field(None, ge=0)
    daily_rate: Optional[float] = Field(None, ge=0)
    condition: Optional[EquipmentCondition] = None


class EquipmentAvailabilityUpdate(BaseModel):
    is_available: bool


class EquipmentResponse(EquipmentBase):
    id: UUID
    provider_id: UUID
    is_flagged: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedEquipmentResponse(BaseModel):
    items: List[EquipmentResponse]
    total: int
    page: int
    per_page: int
