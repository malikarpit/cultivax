"""
Media Upload Service

Handles file uploads for crop instance media (images, videos).
Stores locally for now, will integrate with Google Cloud Storage later (Day 28).

MSDD 4.6 — 3-month retention policy with scheduled deletion.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from sqlalchemy.orm import Session  # type: ignore

from app.models.media_file import MediaFile  # type: ignore
from app.models.crop_instance import CropInstance  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPLOAD_DIR = os.environ.get("MEDIA_UPLOAD_DIR", "uploads/media")
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {
    "image": {"jpg", "jpeg", "png", "webp", "gif"},
    "video": {"mp4", "mov", "avi", "mkv"},
}
RETENTION_DAYS = 90  # 3-month retention per MSDD 4.6


class UploadResult:
    """Result of a media upload operation."""

    def __init__(
        self,
        media_id: str,
        file_path: str,
        file_type: str,
        file_size: int,
        scheduled_deletion_at: datetime,
    ):
        self.media_id = media_id
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size
        self.scheduled_deletion_at = scheduled_deletion_at

    def to_dict(self) -> dict:
        return {
            "media_id": self.media_id,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "scheduled_deletion_at": self.scheduled_deletion_at.isoformat(),
        }


class UploadService:
    """
    Handles media file uploads for crop instances.

    Features:
    - File type validation (image/video)
    - Size limit enforcement
    - Local storage (Cloud Storage integration in Day 28)
    - Scheduled deletion tracking (MSDD 4.6)
    - Analysis status initialization
    """

    def __init__(self, db: Session):
        self.db = db

    def upload_media(
        self,
        crop_instance_id: str,
        farmer_id: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a media file for a crop instance.

        Args:
            crop_instance_id: The crop this media belongs to
            farmer_id: The uploading farmer
            filename: Original filename
            content: File content bytes
            content_type: MIME type (auto-detected from extension if not provided)

        Returns:
            UploadResult with upload details

        Raises:
            ValueError: If file type not allowed or size exceeded
            PermissionError: If crop not found or not owned by farmer
        """

        # Verify crop ownership
        crop = (
            self.db.query(CropInstance)
            .filter(
                CropInstance.id == crop_instance_id,
                CropInstance.farmer_id == farmer_id,
                CropInstance.is_deleted == False,
            )
            .first()
        )

        if not crop:
            raise PermissionError("Crop not found or not owned by you")

        # Validate file
        ext = self._get_extension(filename)
        file_type = self._classify_file(ext)
        self._validate_size(content)

        # Generate unique filename
        media_id = str(uuid.uuid4())
        stored_filename = f"{media_id}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, str(crop_instance_id), stored_filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write file to local storage
        with open(file_path, "wb") as f:
            f.write(content)

        # Scheduled deletion (MSDD 4.6 — 3-month retention)
        scheduled_deletion = datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)

        # Create DB record
        media_record = MediaFile(
            id=uuid.UUID(media_id),
            crop_instance_id=crop_instance_id,
            file_type=file_type,
            file_path=file_path,
            file_size=len(content),
            original_filename=filename,
            mime_type=content_type or f"{file_type}/{ext}",
            analysis_status="Pending",
            scheduled_deletion_at=scheduled_deletion,
        )
        self.db.add(media_record)
        self.db.commit()

        logger.info(
            f"Media uploaded: {media_id} ({file_type}/{ext}, "
            f"{len(content)} bytes) for crop {crop_instance_id}"
        )

        return UploadResult(
            media_id=media_id,
            file_path=file_path,
            file_type=file_type,
            file_size=len(content),
            scheduled_deletion_at=scheduled_deletion,
        )

    def _get_extension(self, filename: str) -> str:
        """Extract and validate file extension."""
        if "." not in filename:
            raise ValueError("Filename must have an extension")
        ext = filename.rsplit(".", 1)[-1].lower()
        all_allowed = set()
        for exts in ALLOWED_EXTENSIONS.values():
            all_allowed.update(exts)
        if ext not in all_allowed:
            raise ValueError(
                f"File extension '.{ext}' not allowed. "
                f"Allowed: {sorted(all_allowed)}"
            )
        return ext

    def _classify_file(self, ext: str) -> str:
        """Classify file as image or video."""
        for file_type, extensions in ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return "unknown"

    def _validate_size(self, content: bytes):
        """Enforce file size limits."""
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File size ({size_mb:.1f}MB) exceeds maximum "
                f"allowed size ({MAX_FILE_SIZE_MB}MB)"
            )
