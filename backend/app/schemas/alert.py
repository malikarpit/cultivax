"""
Alert Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AlertResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    crop_instance_id: Optional[UUID]
    alert_type: str
    severity: str
    urgency_level: Optional[str]
    message: str
    details: Optional[dict]
    source_event_id: Optional[UUID]
    expires_at: Optional[datetime]
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    acknowledged: bool = True


class BulkAcknowledgeRequest(BaseModel):
    alert_ids: list[UUID]


class BulkAcknowledgeResponse(BaseModel):
    acknowledged_count: int
