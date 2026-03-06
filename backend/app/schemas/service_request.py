"""
Service Request Schemas

Pydantic schemas for Service Request lifecycle.
Separated from service_provider.py per workflow.md Day 6.
"""

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ServiceRequestCreate(BaseModel):
    provider_id: UUID
    service_type: str
    crop_type: Optional[str] = None
    description: Optional[str] = None
    requested_date: Optional[datetime] = None
    agreed_price: Optional[float] = None


class ServiceRequestResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    provider_id: UUID
    service_type: str
    crop_type: Optional[str]
    status: str
    requested_date: Optional[datetime]
    completed_date: Optional[datetime]
    provider_acknowledged_at: Optional[datetime]
    agreed_price: Optional[float]
    final_price: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
