"""
Yield Record Schemas

Pydantic schemas for Yield submission and response.
Separated from crop_instance.py per workflow.md Day 6.
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class YieldSubmission(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reported_yield: float = Field(..., gt=0)
    yield_unit: str = "kg/acre"
    harvest_date: Optional[date] = None
    quality_grade: Optional[str] = Field(default=None, max_length=10)
    moisture_pct: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Frontend compatibility: allow yield_quantity_kg from existing form payload.
    yield_quantity_kg: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, values: Any):
        if not isinstance(values, dict):
            return values
        if (
            values.get("reported_yield") is None
            and values.get("yield_quantity_kg") is not None
        ):
            values["reported_yield"] = values["yield_quantity_kg"]
        if (
            values.get("moisture_pct") is None
            and values.get("moisture_content_pct") is not None
        ):
            values["moisture_pct"] = values["moisture_content_pct"]
        return values


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
    verification_metadata: Optional[dict[str, Any]] = None
    quality_grade: Optional[str] = None
    moisture_pct: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
