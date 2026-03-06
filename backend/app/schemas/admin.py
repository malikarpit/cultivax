"""
Admin Schemas

Schemas for admin-facing API responses.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class AdminAuditResponse(BaseModel):
    id: UUID
    admin_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    before_value: Optional[Dict[str, Any]]
    after_value: Optional[Dict[str, Any]]
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RoleUpdateRequest(BaseModel):
    role: str  # farmer | provider | admin
