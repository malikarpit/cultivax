import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.orm import Session
from datetime import datetime
import io

from app.models.crop_instance import CropInstance
from app.models.land_parcel import LandParcel
from app.models.media_file import MediaFile
from tests.conftest import unwrap

pytestmark = pytest.mark.asyncio

async def setup_farmer_and_crop(db: Session, farmer_user, settings):
    # Setup land parcel
    parcel = LandParcel(
        id=uuid4(),
        farmer_id=farmer_user.id,
        parcel_name="Media Test Parcel",
        region="Punjab",
        land_area=2.5,
    )
    db.add(parcel)
    db.flush()
    
    # Setup crop
    from datetime import date, timedelta
    crop = CropInstance(
        id=uuid4(),
        land_parcel_id=parcel.id,
        farmer_id=farmer_user.id,
        crop_type="wheat",
        variety="HD-2967",
        sowing_date=date.today() - timedelta(days=30),
        state="Active",
        region="Punjab",
        land_area=2.5,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop

async def test_upload_media_success(async_client: AsyncClient, farmer_token: str, db: Session, farmer_user, settings):
    crop = await setup_farmer_and_crop(db, farmer_user, settings)
    
    headers = {"Authorization": f"Bearer {farmer_token}"}
    
    # Mock JPEG file
    file_bytes = b'\xff\xd8\xff' + b'fake_image_content'
    files = {"file": ("test_img.jpg", io.BytesIO(file_bytes), "image/jpeg")}
    data = {"source_channel": "web"}
    
    response = await async_client.post(
        f"/api/v1/crops/{crop.id}/media", headers=headers, files=files, data=data
    )
    
    assert response.status_code == 200
    res_data = unwrap(response)
    assert "media_id" in res_data
    assert res_data["analysis_status"] == "pending"
    
    # Verify in DB
    media = db.query(MediaFile).filter(MediaFile.id == res_data["media_id"]).first()
    assert media is not None
    assert media.mime_type == "image/jpeg"
    assert media.source_channel == "web"
    assert media.file_size_bytes == len(file_bytes)

async def test_upload_media_invalid_magic_bytes(async_client: AsyncClient, farmer_token: str, db: Session, farmer_user, settings):
    crop = await setup_farmer_and_crop(db, farmer_user, settings)
    headers = {"Authorization": f"Bearer {farmer_token}"}
    
    # Mock malicious file claiming to be JPEG but no magic bytes
    file_bytes = b'MZfake_exe_content'
    files = {"file": ("malicious.jpg", io.BytesIO(file_bytes), "image/jpeg")}
    
    response = await async_client.post(
        f"/api/v1/crops/{crop.id}/media", headers=headers, files=files, data={"source_channel": "web"}
    )
    
    assert response.status_code == 400
    assert "magic bytes" in response.text.lower()

async def test_duplicate_upload_is_handled(async_client: AsyncClient, farmer_token: str, db: Session, farmer_user, settings):
    crop = await setup_farmer_and_crop(db, farmer_user, settings)
    headers = {"Authorization": f"Bearer {farmer_token}"}
    file_bytes = b'\xff\xd8\xff' + b'duplicate_image'
    
    # First upload
    response1 = await async_client.post(
        f"/api/v1/crops/{crop.id}/media", headers=headers,
        files={"file": ("img1.jpg", io.BytesIO(file_bytes), "image/jpeg")}
    )
    assert response1.status_code == 200
    id1 = unwrap(response1)["media_id"]
    
    # Second upload of same exact content
    response2 = await async_client.post(
        f"/api/v1/crops/{crop.id}/media", headers=headers,
        files={"file": ("img2.jpg", io.BytesIO(file_bytes), "image/jpeg")}
    )
    assert response2.status_code == 200
    id2 = unwrap(response2)["media_id"]
    
    # Expected: The API detected duplicate and returned existing record ID
    assert id1 == id2

async def test_list_and_get_media(async_client: AsyncClient, farmer_token: str, db: Session, farmer_user, settings):
    crop = await setup_farmer_and_crop(db, farmer_user, settings)
    headers = {"Authorization": f"Bearer {farmer_token}"}
    
    # Create manual media
    media = MediaFile(
        id=uuid4(),
        crop_instance_id=crop.id,
        uploaded_by=farmer_user.id,
        file_type="image",
        storage_path="local/path/media.jpg",
        original_filename="manual.jpg",
        mime_type="image/jpeg",
        analysis_status="analyzed",
        image_quality_score=0.9,
    )
    db.add(media)
    db.commit()
    
    # Test List
    res_list = await async_client.get(f"/api/v1/crops/{crop.id}/media", headers=headers)
    assert res_list.status_code == 200
    assert res_list.status_code == 200
    data = unwrap(res_list)
    assert len(data) == 1
    assert data[0]["media_id"] == str(media.id)
    
    # Test Detail
    res_get = await async_client.get(f"/api/v1/media/{media.id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.status_code == 200
    detail = unwrap(res_get)
    assert detail["image_quality_score"] == 0.9
    assert detail["analysis_status"] == "analyzed"
    assert "download_url" in detail

async def test_delete_media(async_client: AsyncClient, farmer_token: str, db: Session, farmer_user, settings):
    crop = await setup_farmer_and_crop(db, farmer_user, settings)
    headers = {"Authorization": f"Bearer {farmer_token}"}
    
    media = MediaFile(
        id=uuid4(),
        crop_instance_id=crop.id,
        uploaded_by=farmer_user.id,
        file_type="image",
        storage_path="local/path/todelete.jpg",
        original_filename="del.jpg",
    )
    db.add(media)
    db.commit()
    
    # Delete
    res_del = await async_client.delete(f"/api/v1/media/{media.id}", headers=headers)
    assert res_del.status_code == 200
    
    # Verify soft-delete
    db.refresh(media)
    assert media.deleted_at is not None
    
    # Try fetching (should be 404)
    res_get = await async_client.get(f"/api/v1/media/{media.id}", headers=headers)
    assert res_get.status_code == 404
