"""
Admin Schemas

Schemas for admin-facing API responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


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
