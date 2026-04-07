"""
SOE Schemas

Schemas for Service Providers, Equipment, Service Requests, and Reviews.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# === Provider Schemas ===


class ProviderCreate(BaseModel):
    business_name: Optional[str] = None
    service_type: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    sub_region: Optional[str] = None
    service_radius_km: Optional[float] = None
    crop_specializations: List[str] = []
    description: Optional[str] = None


class ProviderUpdate(BaseModel):
    business_name: Optional[str] = None
    service_type: Optional[str] = None
    region: Optional[str] = None
    sub_region: Optional[str] = None
    service_radius_km: Optional[float] = None
    crop_specializations: Optional[List[str]] = None
    description: Optional[str] = None


class ProviderResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_name: Optional[str]
    service_type: str
    region: str
    sub_region: Optional[str]
    service_radius_km: Optional[float]
    crop_specializations: List[str]
    trust_score: float
    is_verified: bool
    is_suspended: bool
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderRankedResponse(ProviderResponse):
    ranking_score: float
    fairness_boosted: bool = False
    ranking_flags: List[str] = []
    distance_km: Optional[float] = None
    ranking_meta: Dict[str, Any] = {}


class PaginatedRankedResponse(BaseModel):
    items: List[ProviderRankedResponse]
    total: int
    page: int
    limit: int


class ProviderFilter(BaseModel):
    region: Optional[str] = None
    crop_type: Optional[str] = None
    service_type: Optional[str] = None
    is_verified: Optional[bool] = None


# === Service Request Schemas ===


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


# === Review Schemas ===


class ReviewCreate(BaseModel):
    request_id: UUID
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None
    complaint_category: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    request_id: UUID
    reviewer_id: UUID
    rating: float
    comment: Optional[str]
    complaint_category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
