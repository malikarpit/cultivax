"""
Media Upload API Endpoint

POST /crops/{id}/media — upload image/video for a crop instance.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, UploadFile)
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.config import settings
from app.events.handlers import emit_upload_event
from app.models.crop_instance import CropInstance
from app.models.media_file import MediaFile
from app.models.user import User
from app.schemas.media import (MediaConfirmUploadRequest,
                               MediaConfirmUploadResponse, MediaDetailResponse,
                               MediaListResponse, MediaRequestUploadRequest,
                               MediaRequestUploadResponse, MediaUploadResponse)
from app.services.media.upload_service import CloudStorageClient, UploadService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Media"])


@router.post("/media/request-upload", response_model=MediaRequestUploadResponse)
async def request_media_upload(
    data: MediaRequestUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role(["farmer"])),
):
    """
    Request a signed URL upload session (docs compatibility endpoint).

    Works with GCS-backed storage. For local storage environments, clients should
    use multipart upload at POST /api/v1/crops/{crop_id}/media.
    """
    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == data.crop_instance_id,
            CropInstance.farmer_id == current_user.id,
            CropInstance.is_deleted == False,
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=400,
            detail="Signed URL upload is unavailable in local storage mode. Use /api/v1/crops/{crop_id}/media.",
        )

    file_type = (data.file_type or "image").lower()
    if file_type not in {"image", "video"}:
        raise HTTPException(
            status_code=422, detail="file_type must be one of: image, video"
        )

    default_ext = "jpg" if file_type == "image" else "mp4"
    content_type = "image/jpeg" if file_type == "image" else "video/mp4"
    media_id = uuid4()
    destination_path = f"crops/{crop.id}/{media_id}.{default_ext}"
    storage_path = f"gs://{settings.GCS_BUCKET_NAME}/{destination_path}"

    upload_url = CloudStorageClient.generate_upload_signed_url(
        blob_path=destination_path,
        content_type=content_type,
    )

    media = MediaFile(
        id=media_id,
        crop_instance_id=crop.id,
        uploaded_by=current_user.id,
        file_type=file_type,
        original_filename=f"{media_id}.{default_ext}",
        storage_path=storage_path,
        mime_type=content_type,
        analysis_status="pending",
        source_channel="api",
    )
    db.add(media)
    db.commit()

    return MediaRequestUploadResponse(upload_url=upload_url, media_id=media_id)


@router.post("/media/confirm-upload", response_model=MediaConfirmUploadResponse)
async def confirm_media_upload(
    data: MediaConfirmUploadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm signed upload completion and enqueue analysis.
    """
    media = (
        db.query(MediaFile)
        .join(CropInstance)
        .filter(
            MediaFile.id == data.media_id,
            CropInstance.farmer_id == current_user.id,
            MediaFile.deleted_at == None,
        )
        .first()
    )
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.analysis_status = "pending"
    db.commit()

    background_tasks.add_task(emit_upload_event, str(media.id))
    return MediaConfirmUploadResponse(media_id=media.id, status="queued")


@router.post("/crops/{crop_id}/media", response_model=MediaUploadResponse)
async def upload_media(
    crop_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_channel: str = Form("web"),
    geo_verified: bool = Form(False),
    capture_lat: Optional[float] = Form(None),
    capture_lng: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role(["farmer"])),
):
    """
    Upload a media file (image/video) for a crop instance.
    Validates file sizes, magic-bytes MIME types, performs SHA-256 deduplication.
    """
    try:
        content = await file.read()
        service = UploadService(db)
        result = service.upload_media(
            crop_instance_id=str(crop_id),
            farmer_id=str(current_user.id),
            filename=file.filename or "upload.bin",
            content=content,
            content_type=file.content_type,
            source_channel=source_channel,
            geo_verified=geo_verified,
            capture_lat=capture_lat,
            capture_lng=capture_lng,
        )

        # Enqueue analysis job if not duplicate
        if not result.is_duplicate:
            # We defer analysis background task here without passing the Request DB session
            background_tasks.add_task(emit_upload_event, result.media_id)

        return MediaUploadResponse(
            media_id=result.media_id,
            analysis_status=(
                "pending"
                if not result.is_duplicate
                else getattr(result, "analysis_status", "pending")
            ),
            preview_url=f"/api/v1/media/{result.media_id}/download",
            uploaded_at=datetime.utcnow(),
        )
    except PermissionError as e:
        logger.warning(f"Permission error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/crops/{crop_id}/media", response_model=List[MediaListResponse])
async def list_crop_media(
    crop_id: UUID,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List paginated media for crop with optional filters."""
    crop = (
        db.query(CropInstance)
        .filter(CropInstance.id == crop_id, CropInstance.farmer_id == current_user.id)
        .first()
    )
    if not crop:
        raise HTTPException(status_code=403, detail="Crop not found or not owned")

    query = db.query(MediaFile).filter(
        MediaFile.crop_instance_id == crop_id, MediaFile.deleted_at == None
    )

    if status:
        query = query.filter(MediaFile.analysis_status == status)

    items = (
        query.order_by(MediaFile.created_at.desc()).offset(offset).limit(limit).all()
    )
    return items


@router.get("/media/{media_id}", response_model=MediaDetailResponse)
async def get_media_detail(
    media_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed media info with analysis results."""
    media = (
        db.query(MediaFile)
        .join(CropInstance)
        .filter(
            MediaFile.id == media_id,
            CropInstance.farmer_id == current_user.id,
            MediaFile.deleted_at == None,
        )
        .first()
    )

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    detail = MediaDetailResponse.model_validate(media)
    detail.download_url = f"/api/v1/media/{media.id}/download"
    return detail


@router.get("/media/{media_id}/download")
async def download_media(
    media_id: UUID,
    variant: str = "full",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download media via safe signed URL or stream local mock file."""
    media = (
        db.query(MediaFile)
        .join(CropInstance)
        .filter(
            MediaFile.id == media_id,
            CropInstance.farmer_id == current_user.id,
            MediaFile.deleted_at == None,
        )
        .first()
    )

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    service = UploadService(db)
    download_url = service.get_download_url(str(media_id))

    if media.storage_path.startswith("gs://"):
        return RedirectResponse(url=download_url)
    else:
        # local streaming
        return FileResponse(media.storage_path, media_type=media.mime_type)


@router.delete("/media/{media_id}")
async def delete_media(
    media_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete media."""
    media = (
        db.query(MediaFile)
        .join(CropInstance)
        .filter(
            MediaFile.id == media_id,
            CropInstance.farmer_id == current_user.id,
            MediaFile.deleted_at == None,
        )
        .first()
    )

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.deleted_at = datetime.utcnow()
    db.commit()

    logger.info(f"Media deleted: {media_id}")
    return {"success": True, "message": "Media deleted"}
