"""
Media File Model

Stores uploaded media file metadata.
TDD Section 2.7.1. Scheduled deletion after 3 months (MSDD 11.12).
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class MediaFile(BaseModel):
    __tablename__ = "media_files"

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
    # pending | processing | completed | failed

    # Extracted features (after ML analysis)
    extracted_features = Column(JSONB, default=dict)
    stress_probability = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Video-specific
    frame_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Retention (MSDD 11.12)
    scheduled_deletion_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<MediaFile {self.file_type} [{self.analysis_status}]>"
