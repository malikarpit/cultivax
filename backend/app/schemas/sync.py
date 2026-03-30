"""
Offline Sync Schemas

Pydantic models for the offline sync request/response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class ActionTypeEnum(str, Enum):
    IRRIGATION = "irrigation"
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    FUNGICIDE = "fungicide"
    HERBICIDE = "herbicide"
    PRUNING = "pruning"
    THINNING = "thinning"
    TRANSPLANTING = "transplanting"
    HARVESTING = "harvesting"
    MONITORING = "monitoring"
    SOIL_AMENDMENT = "soil_amendment"
    DISEASE_MANAGEMENT = "disease_management"
    PEST_MANAGEMENT = "pest_management"
    WEEDING = "weeding"
    MULCHING = "mulching"
    STAKING = "staking"
    DEFOLIATION = "defoliation"
    SEED_TREATMENT = "seed_treatment"
    OBSERVATION = "observation"


class OfflineAction(BaseModel):
    """Single offline-queued action."""
    crop_instance_id: str
    action_type: str
    action_effective_date: str  # ISO format
    local_seq_no: int = Field(..., ge=0, le=999999)
    metadata: Optional[dict] = None
    notes: Optional[str] = None

    @field_validator("crop_instance_id")
    @classmethod
    def validate_crop_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("crop_instance_id is required")
        return v.strip()

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[dict]) -> dict:
        return v or {}


class OfflineSyncRequest(BaseModel):
    """Offline sync batch request."""
    device_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    actions: List[OfflineAction] = Field(..., min_length=1, max_length=500)


# ── Response detail models ──

class SyncedActionDetail(BaseModel):
    action_id: str
    crop_id: str
    action_type: str
    action_effective_date: str
    local_seq_no: int
    status: str


class FailedActionDetail(BaseModel):
    action_index: int
    local_seq_no: int
    crop_id: Optional[str] = None
    action_type: Optional[str] = None
    error: str
    status: str


class DuplicateActionDetail(BaseModel):
    action_index: int
    action_id: str
    reason: str
    original_sync_time: str


class AnomalyDetail(BaseModel):
    action_index: int
    local_seq_no: int
    reason: str
    severity: str


class OfflineSyncResponse(BaseModel):
    """Full response from offline sync."""
    synced: int
    failed: int
    warnings: int
    duplicates: int
    synced_actions: List[SyncedActionDetail]
    failed_actions: List[FailedActionDetail]
    duplicate_actions: List[DuplicateActionDetail]
    anomalies: List[AnomalyDetail]
    device_id: str
    session_id: str
    sync_timestamp: str
