"""
Service Request Schemas

Pydantic schemas for Service Request lifecycle.
Separated from service_provider.py per workflow.md Day 6.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ServiceRequestCreate(BaseModel):
    provider_id: UUID
    service_type: str
    crop_instance_id: Optional[UUID] = None
    description: Optional[str] = None
    region: Optional[str] = None
    urgency: Optional[str] = None
    preferred_date: Optional[datetime] = None
    agreed_price: Optional[float] = None


class ServiceRequestResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    provider_id: UUID
    service_type: str
    crop_instance_id: Optional[UUID]
    region: Optional[str]
    urgency: Optional[str]
    status: str
    preferred_date: Optional[datetime]
    completed_at: Optional[datetime]
    provider_acknowledged_at: Optional[datetime]
    agreed_price: Optional[float]
    final_price: Optional[float]
    created_at: datetime
    can_accept: Optional[bool] = False
    can_decline: Optional[bool] = False
    can_start: Optional[bool] = False
    can_complete: Optional[bool] = False
    can_cancel: Optional[bool] = False
    has_reviewed: Optional[bool] = False

    class Config:
        from_attributes = True
