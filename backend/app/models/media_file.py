"""
Media File Model

Stores uploaded media file metadata.
TDD Section 2.7.1. Scheduled deletion after 3 months (MSDD 11.12).
"""

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index,
                        Integer, String, UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


class MediaFile(BaseModel):
    __tablename__ = "media_files"
    __table_args__ = (
        UniqueConstraint(
            "crop_instance_id", "checksum_sha256", name="uq_media_checksum_per_crop"
        ),
        Index("ix_media_crop_created", "crop_instance_id", "created_at", "deleted_at"),
        Index("ix_media_status", "analysis_status", "deleted_at"),
    )

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Uploader
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # File info
    file_type = Column(String(20), nullable=False)  # image | video | voice
    original_filename = Column(String(500), nullable=True)
    storage_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Processing status
    analysis_status = Column(String(20), default="pending", nullable=False)
    # pending | processing | analyzed | completed | failed

    # Ingest metadata (NEW)
    checksum_sha256 = Column(String(64), index=True, nullable=True)  # SHA-256 hex
    source_channel = Column(String(20), default="web")  # web, mobile, api
    capture_lat = Column(Float, nullable=True)
    capture_lng = Column(Float, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    is_quarantined = Column(Boolean, default=False)

    # Extracted features (after ML analysis)
    extracted_features = Column(JSONB, default=dict)
    stress_probability = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Additional media intelligence fields (TDD 2.7.1, Media Enh 2/6/7)
    image_quality_score = Column(Float, nullable=True)  # Blur/brightness validated
    pest_probability = Column(Float, nullable=True)  # Separate pest detection
    analysis_source = Column(String(20), nullable=True)  # backend | edge
    geo_verified = Column(
        Boolean, default=False, nullable=False
    )  # EXIF spatial validation

    # Video-specific
    frame_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Retention (MSDD 11.12)
    scheduled_deletion_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<MediaFile {self.file_type} [{self.analysis_status}]>"
