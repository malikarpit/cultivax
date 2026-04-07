from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MediaUploadRequest(BaseModel):
    """Upload request metadata."""

    source_channel: str = Field(default="web")  # web, mobile, api
    capture_lat: Optional[float] = None
    capture_lng: Optional[float] = None


class MediaUploadResponse(BaseModel):
    """Upload response (minimal, opaque)."""

    media_id: str
    analysis_status: str  # pending
    preview_url: (
        str  # GET /api/v1/media/{media_id}/download?variant=preview (if available)
    )
    uploaded_at: datetime


from uuid import UUID


class MediaRequestUploadRequest(BaseModel):
    """Request a signed upload URL for media ingestion."""

    crop_instance_id: UUID
    file_type: str = Field(default="image")  # image | video


class MediaRequestUploadResponse(BaseModel):
    """Signed-upload bootstrap response."""

    upload_url: str
    media_id: UUID


class MediaConfirmUploadRequest(BaseModel):
    """Confirm that direct upload has completed."""

    media_id: UUID


class MediaConfirmUploadResponse(BaseModel):
    """Confirmation response after upload is queued for analysis."""

    media_id: UUID
    status: str


class MediaDetailResponse(BaseModel):
    """Detailed media info with analysis."""

    media_id: UUID = Field(validation_alias="id")
    crop_instance_id: UUID
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    analysis_status: str
    image_quality_score: Optional[float] = None
    pest_probability: Optional[float] = None
    stress_probability: Optional[float] = None
    confidence_score: Optional[float] = None
    is_quarantined: bool = False
    created_at: datetime
    download_url: Optional[str] = None  # Signed URL or token-based access

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    """List item."""

    media_id: UUID = Field(validation_alias="id")
    analysis_status: str
    image_quality_score: Optional[float]
    pest_probability: Optional[float]
    stress_probability: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
