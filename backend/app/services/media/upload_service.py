"""
Media Upload Service — Google Cloud Storage Integration

Day 28: Upgraded from local-only to GCS + local fallback.
Uses google-cloud-storage SDK for cloud uploads with signed URLs.
Falls back to local file storage when GCS_BUCKET_NAME is not set.

MSDD 4.6 — 3-month retention policy with scheduled deletion.
"""

import hashlib
import logging
import mimetypes
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session  # type: ignore

from app.config import settings  # type: ignore
from app.models.crop_instance import CropInstance  # type: ignore
from app.models.media_file import MediaFile  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ✅ Whitelist MIME types with magic-byte validation
ALLOWED_MIMES = {
    "image/jpeg": [b"\xff\xd8\xff"],  # JPEG magic bytes
    "image/png": [b"\x89PNG"],  # PNG magic bytes
    "image/webp": [b"RIFF", b"WEBP"],  # WebP magic bytes
    "image/gif": [b"GIF8"],  # GIF magic bytes
}

MAX_FILE_SIZE_MB = 10  # Reduced to 10MB default for images
MAX_VIDEO_SIZE_MB = 50
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
        signed_url: Optional[str] = None,
        storage_backend: str = "local",
    ):
        self.media_id = media_id
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size
        self.scheduled_deletion_at = scheduled_deletion_at
        self.signed_url = signed_url
        self.storage_backend = storage_backend
        self.is_duplicate = False

    def to_dict(self) -> dict:
        result = {
            "media_id": self.media_id,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "scheduled_deletion_at": self.scheduled_deletion_at.isoformat(),
            "storage_backend": self.storage_backend,
            "is_duplicate": self.is_duplicate,
        }
        if self.signed_url:
            result["download_url"] = self.signed_url
        return result


class CloudStorageClient:
    """
    Google Cloud Storage client wrapper.

    Provides upload and signed URL generation.
    Lazily initializes the GCS client only when needed.
    """

    _client = None
    _bucket = None

    @classmethod
    def _init_client(cls):
        """Lazily initialize GCS client and bucket reference."""
        if cls._client is None:
            try:
                from google.cloud import storage  # type: ignore

                cls._client = storage.Client()
                cls._bucket = cls._client.bucket(settings.GCS_BUCKET_NAME)
                logger.info(
                    f"GCS client initialized for bucket: {settings.GCS_BUCKET_NAME}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise

    @classmethod
    def upload_blob(
        cls, destination_path: str, content: bytes, content_type: str
    ) -> str:
        """
        Upload content to GCS bucket.

        Args:
            destination_path: Path within the bucket (e.g., "crops/{id}/{filename}")
            content: File content bytes
            content_type: MIME type

        Returns:
            The GCS URI (gs://bucket/path)
        """
        cls._init_client()
        blob = cls._bucket.blob(destination_path)
        blob.upload_from_string(content, content_type=content_type)

        gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{destination_path}"
        logger.info(f"Uploaded to GCS: {gcs_uri} ({len(content)} bytes)")
        return gcs_uri

    @classmethod
    def generate_signed_url(
        cls, blob_path: str, expiry_minutes: Optional[int] = None
    ) -> str:
        """
        Generate a signed URL for downloading a blob.

        Args:
            blob_path: Path within the bucket
            expiry_minutes: URL expiry in minutes (default from config)

        Returns:
            Signed download URL
        """
        cls._init_client()
        expiry = expiry_minutes or settings.GCS_SIGNED_URL_EXPIRY_MINUTES
        blob = cls._bucket.blob(blob_path)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiry),
            method="GET",
        )
        return url

    @classmethod
    def generate_upload_signed_url(
        cls,
        blob_path: str,
        content_type: str,
        expiry_minutes: Optional[int] = None,
    ) -> str:
        """
        Generate a signed URL for direct upload (PUT) to a blob.
        """
        cls._init_client()
        expiry = expiry_minutes or settings.GCS_SIGNED_URL_EXPIRY_MINUTES
        blob = cls._bucket.blob(blob_path)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiry),
            method="PUT",
            content_type=content_type,
        )

    @classmethod
    def delete_blob(cls, blob_path: str) -> bool:
        """Delete a blob from GCS. Returns True if deleted."""
        cls._init_client()
        blob = cls._bucket.blob(blob_path)
        if blob.exists():
            blob.delete()
            logger.info(f"Deleted GCS blob: {blob_path}")
            return True
        return False


class UploadService:
    """
    Handles media file uploads for crop instances.

    Features:
    - File type validation (image/video)
    - Size limit enforcement
    - Google Cloud Storage with signed URLs (when configured)
    - Local storage fallback (when GCS not configured)
    - Scheduled deletion tracking (MSDD 4.6)
    - Analysis status initialization
    """

    def __init__(self, db: Session):
        self.db = db
        self.use_gcs = bool(settings.GCS_BUCKET_NAME)

    def upload_media(
        self,
        crop_instance_id: str,
        farmer_id: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
        source_channel: str = "web",
        geo_verified: bool = False,
        capture_lat: Optional[float] = None,
        capture_lng: Optional[float] = None,
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
            UploadResult with upload details and optional signed URL

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

        # ✅ 1. Validate file size and MIME type / extension
        ext = self._get_extension(filename)
        file_type = self._classify_file(ext)
        guessed_mime = (
            mimetypes.guess_type(filename)[0] or content_type or f"{file_type}/{ext}"
        )

        self._validate_size(content, file_type)
        self._validate_magic_bytes(content, guessed_mime)

        # ✅ 2. Compute checksum for dedup
        checksum = hashlib.sha256(content).hexdigest()

        # Check for duplicate
        existing = (
            self.db.query(MediaFile)
            .filter(
                MediaFile.crop_instance_id == crop_instance_id,
                MediaFile.checksum_sha256 == checksum,
                MediaFile.deleted_at == None,
            )
            .first()
        )

        if existing:
            logger.info(
                f"Duplicate media detected: crop={crop_instance_id}, "
                f"checksum={checksum}, existing_id={existing.id}"
            )
            # Create a mock UploadResult for existing
            result = UploadResult(
                media_id=str(existing.id),
                file_path=existing.storage_path,
                file_type=existing.file_type,
                file_size=existing.file_size_bytes or len(content),
                scheduled_deletion_at=existing.scheduled_deletion_at
                or (datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)),
                signed_url=self.get_download_url(str(existing.id)),
            )
            result.is_duplicate = True
            return result

        # Generate unique filename
        media_id = str(uuid.uuid4())
        stored_filename = f"{media_id}.{ext}"
        mime = guessed_mime

        # Choose storage backend
        if self.use_gcs:
            storage_path, signed_url, backend = self._upload_to_gcs(
                crop_instance_id, stored_filename, content, mime
            )
        else:
            storage_path, signed_url, backend = self._upload_to_local(
                crop_instance_id, stored_filename, content
            )

        # Scheduled deletion (MSDD 4.6 — 3-month retention)
        scheduled_deletion = datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)

        # Create DB record
        media_record = MediaFile(
            id=uuid.UUID(media_id),
            crop_instance_id=crop_instance_id,
            uploaded_by=farmer_id,
            file_type=file_type,
            storage_path=storage_path,
            file_size_bytes=len(content),
            original_filename=filename,
            mime_type=mime,
            checksum_sha256=checksum,
            source_channel=source_channel,
            capture_lat=capture_lat,
            capture_lng=capture_lng,
            geo_verified=geo_verified,
            analysis_status="pending",
            scheduled_deletion_at=scheduled_deletion,
        )
        self.db.add(media_record)
        self.db.commit()

        logger.info(
            f"Media uploaded: {media_id} ({file_type}/{ext}, "
            f"{len(content)} bytes, backend={backend}) for crop {crop_instance_id}"
        )

        return UploadResult(
            media_id=media_id,
            file_path=storage_path,
            file_type=file_type,
            file_size=len(content),
            scheduled_deletion_at=scheduled_deletion,
            signed_url=signed_url,
            storage_backend=backend,
        )

    def get_download_url(self, media_id: str) -> Optional[str]:
        """
        Get a signed download URL for a media file.

        Returns signed URL for GCS files, or local path for local files.
        """
        media = (
            self.db.query(MediaFile)
            .filter(MediaFile.id == media_id, MediaFile.is_deleted == False)
            .first()
        )
        if not media:
            return None

        if self.use_gcs and media.storage_path.startswith("gs://"):
            # Extract blob path from gs://bucket/path
            blob_path = media.storage_path.split(
                f"gs://{settings.GCS_BUCKET_NAME}/", 1
            )[-1]
            return CloudStorageClient.generate_signed_url(blob_path)
        else:
            return media.storage_path

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _upload_to_gcs(
        self, crop_instance_id: str, filename: str, content: bytes, mime: str
    ) -> tuple:
        """Upload to Google Cloud Storage. Returns (path, signed_url, backend)."""
        blob_path = f"crops/{crop_instance_id}/media/{filename}"
        gcs_uri = CloudStorageClient.upload_blob(blob_path, content, mime)
        signed_url = CloudStorageClient.generate_signed_url(blob_path)
        return gcs_uri, signed_url, "gcs"

    def _upload_to_local(
        self, crop_instance_id: str, filename: str, content: bytes
    ) -> tuple:
        """Upload to local filesystem. Returns (path, None, backend)."""
        upload_dir = settings.MEDIA_UPLOAD_DIR
        file_path = os.path.join(upload_dir, str(crop_instance_id), filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path, None, "local"

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

    def _validate_magic_bytes(self, content: bytes, mime_type: str):
        """Verify file magic bytes matches claimed MIME type."""
        # Check only if we know the magic bytes (e.g. for images)
        if mime_type in ALLOWED_MIMES:
            magic_prefix = content[:16]
            expected_magics = ALLOWED_MIMES[mime_type]
            if not any(magic_prefix.startswith(m) for m in expected_magics):
                raise ValueError(
                    f"File magic bytes do not match claimed type {mime_type}. Possible polyglot/corrupted file."
                )

    def _validate_size(self, content: bytes, file_type: str):
        """Enforce file size limits."""
        size_mb = len(content) / (1024 * 1024)
        max_size = MAX_FILE_SIZE_MB if file_type == "image" else MAX_VIDEO_SIZE_MB
        if size_mb > max_size:
            raise ValueError(
                f"File size ({size_mb:.1f}MB) exceeds maximum "
                f"allowed size ({max_size}MB)"
            )
