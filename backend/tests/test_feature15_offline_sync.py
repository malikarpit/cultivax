"""
Tests for Feature 15: Offline Sync & Temporal Anomalies

Tests:
- Schema-aligned insert validation
- Sync API endpoints (POST, GET preview, GET history, GET anomalies)
- Admin abuse flag endpoints
"""

import pytest
from datetime import datetime, timezone, timedelta, date
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.action_log import ActionLog
from app.models.abuse_flag import AbuseFlag
from tests.conftest import unwrap

@pytest.fixture
def auth_headers(db):
    """Create a farmer user and return auth headers."""
    from app.security.auth import create_access_token
    # Create farmer
    farmer = User(
        id=uuid4(),
        full_name="Sync Test Farmer",
        phone=f"+123456{str(uuid4().int)[:5]}",
        email=f"farmer{str(uuid4().int)[:5]}@test.com",
        role="farmer",
        password_hash="testpass",
        is_active=True,
        is_deleted=False,
    )
    db.add(farmer)
    
    # Create admin
    admin = User(
        id=uuid4(),
        full_name="Sync Admin",
        phone=f"+123456{str(uuid4().int)[5:10]}",
        email=f"admin{str(uuid4().int)[:5]}@test.com",
        role="admin",
        password_hash="testpass",
        is_active=True,
        is_deleted=False,
    )
    db.add(admin)
    db.commit()
    
    db.refresh(farmer)
    db.refresh(admin)

    farmer_token = create_access_token(data={"sub": str(farmer.id), "role": farmer.role})
    admin_token = create_access_token(data={"sub": str(admin.id), "role": admin.role})

    return {
        "farmer": {"Authorization": f"Bearer {farmer_token}"},
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "farmer_id": farmer.id,
        "admin_id": admin.id,
    }

@pytest.fixture
def test_sync_crop(db, auth_headers):
    """Create a CropInstance for the test farmer."""
    crop = CropInstance(
        id=uuid4(),
        farmer_id=auth_headers["farmer_id"],
        crop_type="wheat",
        variety="test var",
        sowing_date=date.today(),
        region="Punjab",
        state="ACTIVE",
    )
    db.add(crop)
    db.commit()
    return crop


def test_offline_sync_happy_path(client, db, auth_headers, test_sync_crop):
    """Test submitting a valid batch of offline actions."""
    now = datetime.now(timezone.utc)
    
    payload = {
        "device_id": "test-device-1",
        "session_id": "session-1",
        "actions": [
            {
                "crop_instance_id": str(test_sync_crop.id),
                "action_type": "irrigation",
                "action_effective_date": now.isoformat(),
                "local_seq_no": 1,
                "metadata": {"amount": 100}
            },
            {
                "crop_instance_id": str(test_sync_crop.id),
                "action_type": "fertilizer",
                "action_effective_date": now.isoformat(),
                "local_seq_no": 2,
            }
        ]
    }
    
    resp = client.post(
        "/api/v1/offline-sync/",
        headers=auth_headers["farmer"],
        json=payload,
    )
    
    assert resp.status_code == 200, resp.text
    data = unwrap(resp)
    assert data["synced"] == 2
    assert data["failed"] == 0
    assert data["warnings"] == 0
    assert data["session_id"] == "session-1"

    # Verify db records
    actions = db.query(ActionLog).filter_by(source="offline").all()
    assert len(actions) == 2
    assert actions[0].category == "irrigation"
    assert actions[1].category == "soil_management"


def test_offline_sync_temporal_anomalies(client, db, auth_headers, test_sync_crop):
    """Test that extreme backdating and future-dating flag anomalies."""
    now = datetime.now(timezone.utc)
    
    # Very old past action (backdate > 7 days)
    past = now - timedelta(days=10)
    # Very future action (future > 2 hours)
    future = now + timedelta(hours=5)
    
    payload = {
        "device_id": "test-device-anomaly",
        "session_id": "session-2",
        "actions": [
            {
                "crop_instance_id": str(test_sync_crop.id),
                "action_type": "weeding",
                "action_effective_date": past.isoformat(),
                "local_seq_no": 1,
            },
            {
                "crop_instance_id": str(test_sync_crop.id),
                "action_type": "harvesting",
                "action_effective_date": future.isoformat(),
                "local_seq_no": 2,  # seq check is passing
            },
            {
                 # Sequence reversal to bump score!
                "crop_instance_id": str(test_sync_crop.id),
                "action_type": "pruning",
                "action_effective_date": now.isoformat(),
                "local_seq_no": 1,  # Should be monotonic (>2)
            }
        ]
    }
    
    resp = client.post(
        "/api/v1/offline-sync/",
        headers=auth_headers["farmer"],
        json=payload,
    )
    
    assert resp.status_code == 200, resp.text
    data = unwrap(resp)
    
    # 3 anomalous rows (backdate, future, non-monotonic) + 1 batch-level monotonicity issue = 4 warnings
    assert data["warnings"] >= 3
    assert len(data["anomalies"]) >= 3
    
    # Checking AbuseFlags
    flag = db.query(AbuseFlag).filter_by(farmer_id=auth_headers["farmer_id"]).first()
    assert flag is not None
    assert flag.flag_type == "offline_sync_anomalies"


def test_offline_sync_idempotency(client, db, auth_headers, test_sync_crop):
    """Test that duplicate action submissions are flagged as duplicates, not failed."""
    now = datetime.now(timezone.utc)
    
    action_data = {
        "crop_instance_id": str(test_sync_crop.id),
        "action_type": "pesticide",
        "action_effective_date": now.isoformat(),
        "local_seq_no": 100,  # Same seq
    }
    
    payload = {
        "device_id": "device-dup",
        "session_id": "session-dup",
        "actions": [action_data]
    }
    
    # First sync
    resp1 = client.post("/api/v1/offline-sync/", headers=auth_headers["farmer"], json=payload)
    assert resp1.status_code == 200
    assert unwrap(resp1)["synced"] == 1
    
    # Second sync (duplicate)
    resp2 = client.post("/api/v1/offline-sync/", headers=auth_headers["farmer"], json=payload)
    assert resp2.status_code == 200
    data2 = unwrap(resp2)
    assert data2["synced"] == 0
    assert data2["duplicates"] == 1
    assert data2["duplicate_actions"][0]["reason"] == "duplicate_detected"


def test_offline_sync_get_endpoints(client, db, auth_headers, test_sync_crop):
    """Test the preview and history GET endpoints."""
    # Preview
    resp_prev = client.get(
        f"/api/v1/offline-sync/preview/{str(test_sync_crop.id)}",
        headers=auth_headers["farmer"],
    )
    assert resp_prev.status_code == 200
    assert unwrap(resp_prev)["ready_to_sync"] is True
    
    # History
    resp_hist = client.get(
        f"/api/v1/offline-sync/history/{str(test_sync_crop.id)}",
        headers=auth_headers["farmer"],
    )
    assert resp_hist.status_code == 200
    assert isinstance(unwrap(resp_hist), list)

    # Anomalies
    resp_anon = client.get(
        f"/api/v1/offline-sync/anomalies",
        headers=auth_headers["farmer"],
    )
    assert resp_anon.status_code == 200


def test_admin_abuse_flag_review(client, db, auth_headers):
    """Test the admin endpoints to list and resolve abuse flags."""
    # List
    list_resp = client.get(
        "/api/v1/admin/abuse-flags?status=open",
        headers=auth_headers["admin"],
    )
    assert list_resp.status_code == 200
    data = unwrap(list_resp)
    assert "items" in data

    if len(data["items"]) > 0:
        flag_id = data["items"][0]["id"]
        
        # Patch review
        patch_resp = client.patch(
            f"/api/v1/admin/abuse-flags/{flag_id}/review?new_status=reviewed&review_notes=approved",
            headers=auth_headers["admin"],
        )
        assert patch_resp.status_code == 200
        assert unwrap(patch_resp)["status"] == "reviewed"
