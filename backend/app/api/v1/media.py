"""
Media Upload API Endpoint

POST /crops/{id}/media — upload image/video for a crop instance.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from uuid import UUID

from app.api.deps import get_db, get_current_user  # type: ignore
from app.models.user import User  # type: ignore
from app.services.media.upload_service import UploadService  # type: ignore

router = APIRouter(prefix="/crops", tags=["Media"])


@router.post("/{crop_id}/media")
async def upload_media(
    crop_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a media file (image/video) for a crop instance.

    - Max file size: 50MB
    - Allowed: jpg, jpeg, png, webp, gif, mp4, mov, avi, mkv
    - Files are scheduled for deletion after 90 days (MSDD 4.6)
    - Analysis status set to 'Pending' for ML processing
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
        )
        return {
            "message": "Media uploaded successfully",
            "data": result.to_dict(),
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
