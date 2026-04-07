"""
Action Log Schemas

Pydantic schemas for Action Log CRUD operations.
Separated from crop_instance.py per workflow.md Day 6.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ActionLogCreate(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=100)
    effective_date: date
    category: str = "Operational"
    metadata_json: Optional[Dict[str, Any]] = {}
    notes: Optional[str] = None
    local_seq_no: Optional[int] = None
    device_timestamp: Optional[datetime] = None
    idempotency_key: Optional[str] = None


class ActionLogResponse(BaseModel):
    id: UUID
    crop_instance_id: UUID
    action_type: str
    effective_date: date
    category: str
    metadata_json: Dict[str, Any]
    notes: Optional[str]
    local_seq_no: Optional[int]
    server_timestamp: datetime
    applied_in_replay: str
    created_at: datetime

    class Config:
        from_attributes = True
