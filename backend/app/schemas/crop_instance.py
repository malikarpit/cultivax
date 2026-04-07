"""
CTIS Schemas

Pydantic schemas for Crop Instance, Action Log, and Yield Record.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# === Crop Instance Schemas ===


class CropInstanceCreate(BaseModel):
    crop_type: str = Field(..., min_length=1, max_length=100)
    variety: Optional[str] = None
    sowing_date: date
    region: str = Field(..., min_length=1, max_length=100)
    sub_region: Optional[str] = None
    land_area: Optional[float] = Field(None, gt=0)
    land_parcel_id: Optional[UUID] = None
    rule_template_id: Optional[UUID] = None
    metadata_extra: Optional[Dict[str, Any]] = {}


class CropInstanceUpdate(BaseModel):
    variety: Optional[str] = None
    land_area: Optional[float] = Field(None, gt=0)
    land_parcel_id: Optional[UUID] = None
    sub_region: Optional[str] = None
    metadata_extra: Optional[Dict[str, Any]] = None


class SowingDateUpdate(BaseModel):
    new_sowing_date: date


class CropInstanceResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    crop_type: str
    variety: Optional[str]
    sowing_date: date
    state: str
    stage: Optional[str]
    current_day_number: int
    stress_score: float
    risk_index: float
    seasonal_window_category: Optional[str]
    land_area: Optional[float]
    land_parcel_id: Optional[UUID]
    region: str
    sub_region: Optional[str]
    rule_template_id: Optional[UUID]
    rule_template_version: Optional[int]
    stage_offset_days: int
    max_allowed_drift: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CropListFilter(BaseModel):
    state: Optional[str] = None
    crop_type: Optional[str] = None
    region: Optional[str] = None
    include_archived: bool = False


# === Action Log Schemas ===


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
    action_subtype: Optional[str] = None
    action_impact_type: Optional[str] = None
    source: Optional[str] = None
    is_override: bool = False
    rule_version_at_action: Optional[str] = None
    is_orphaned: bool = False
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

    @classmethod
    def from_action(cls, action: Any) -> "ActionLogResponse":
        metadata = action.metadata_json or {}
        return cls(
            id=action.id,
            crop_instance_id=action.crop_instance_id,
            action_type=action.action_type,
            action_subtype=action.action_subtype,
            action_impact_type=action.action_impact_type,
            source=action.source,
            is_override=action.is_override,
            rule_version_at_action=action.rule_version_at_action,
            is_orphaned=action.is_orphaned,
            effective_date=action.effective_date,
            category=action.category,
            metadata_json=metadata,
            notes=action.notes,
            local_seq_no=action.local_seq_no,
            server_timestamp=action.server_timestamp,
            applied_in_replay=action.applied_in_replay,
            created_at=action.created_at,
        )


class ActionLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    has_more: bool
    actions: List[ActionLogResponse]


# === Yield Record Schemas ===


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
