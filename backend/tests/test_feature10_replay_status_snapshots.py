"""
Feature 10 tests: replay status, snapshots APIs, and admin recovery operations.
"""

from datetime import date, timedelta
from uuid import UUID, uuid4

from app.models.user import User
from app.models.crop_instance import CropInstance
from app.models.snapshot import CropInstanceSnapshot
from app.models.event_log import EventLog
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str = "farmer") -> User:
    user = User(
        id=uuid4(),
        full_name=f"Feature10 {role.title()}",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"feature10-{role}-{uuid4().hex[:8]}@test.com",
        password_hash="hashed_test_password",
        role=role,
        region="Punjab",
        preferred_language="en",
        accessibility_settings={},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def _create_crop(client, headers: dict) -> str:
    sowing = date.today() - timedelta(days=30)
    resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "variety": "HD-2967",
            "sowing_date": sowing.isoformat(),
            "region": "Punjab",
            "land_area": 2.2,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return unwrap(resp)["id"]


def test_feature10_replay_status_endpoint(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)

    status_resp = client.get(f"/api/v1/crops/{crop_id}/replay/status", headers=headers)
    assert status_resp.status_code == 200, status_resp.text

    payload = unwrap(status_resp)
    assert payload["crop_id"] == crop_id
    assert payload["status"] in ("idle", "blocked")
    assert "snapshot_count" in payload
    assert "actions_replayed_since_last_snapshot" in payload


def test_feature10_snapshots_list_and_detail_endpoints(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)
    crop_uuid = UUID(crop_id)

    crop = db.query(CropInstance).filter(CropInstance.id == crop_uuid).first()
    snapshot = CropInstanceSnapshot(
        crop_instance_id=crop.id,
        snapshot_data={
            "stress_score": 11.5,
            "risk_index": 0.22,
            "stage": "vegetative",
            "chain_hash": "abc123",
        },
        action_count_at_snapshot=3,
        snapshot_version=1,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    list_resp = client.get(f"/api/v1/crops/{crop_id}/snapshots?page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    list_payload = unwrap(list_resp)
    assert list_payload["total"] >= 1
    assert len(list_payload["snapshots"]) >= 1

    detail_resp = client.get(
        f"/api/v1/crops/{crop_id}/snapshots/{snapshot.id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = unwrap(detail_resp)
    assert detail["crop_id"] == crop_id
    assert detail["action_index"] == 3
    assert detail["snapshot_data"]["chain_hash"] == "abc123"


def test_feature10_admin_recovery_clear_and_retry(client, db):
    farmer = _create_user(db, role="farmer")
    admin = _create_user(db, role="admin")
    farmer_headers = _headers_for(farmer)
    admin_headers = _headers_for(admin)

    crop_id = _create_crop(client, farmer_headers)
    crop_uuid = UUID(crop_id)
    crop = db.query(CropInstance).filter(CropInstance.id == crop_uuid).first()
    crop.state = "RecoveryRequired"
    db.commit()

    # Non-admin blocked
    forbidden_resp = client.patch(
        f"/api/v1/crops/{crop_id}/_admin/recovery/clear?reason=test-clear",
        headers=farmer_headers,
    )
    assert forbidden_resp.status_code == 403

    clear_resp = client.patch(
        f"/api/v1/crops/{crop_id}/_admin/recovery/clear?reason=test-clear",
        headers=admin_headers,
    )
    assert clear_resp.status_code == 200, clear_resp.text
    assert unwrap(clear_resp)["status"] == "recovery_cleared"

    # Put it back in recovery and verify retry endpoint clears and replays
    crop = db.query(CropInstance).filter(CropInstance.id == crop_uuid).first()
    crop.state = "RecoveryRequired"
    db.commit()

    retry_resp = client.patch(
        f"/api/v1/crops/{crop_id}/_admin/recovery/retry",
        headers=admin_headers,
    )
    assert retry_resp.status_code == 200, retry_resp.text
    assert unwrap(retry_resp)["status"] == "retry_completed"


def test_feature10_replay_history_endpoint(client, db):
    farmer = _create_user(db, role="farmer")
    admin = _create_user(db, role="admin")
    other_farmer = _create_user(db, role="farmer")

    farmer_headers = _headers_for(farmer)
    admin_headers = _headers_for(admin)
    other_headers = _headers_for(other_farmer)

    crop_id = _create_crop(client, farmer_headers)
    crop_uuid = UUID(crop_id)

    for i, event_type in enumerate(["ReplayTriggered", "ReplayFailed", "RecoveryCleared"]):
        payload = {"crop_instance_id": crop_id, "sequence": i}
        event = EventLog(
            event_type=event_type,
            entity_type="crop_instance",
            entity_id=crop_uuid,
            partition_key=crop_uuid,
            payload=payload,
            event_hash=f"feature10-history-{event_type}-{crop_id}-{i}",
            module_target="ctis",
        )
        db.add(event)
    db.commit()

    own_resp = client.get(f"/api/v1/crops/{crop_id}/replay/history?limit=10", headers=farmer_headers)
    assert own_resp.status_code == 200, own_resp.text
    own_payload = unwrap(own_resp)
    assert own_payload["crop_id"] == crop_id
    assert own_payload["total"] >= 3
    assert any(item["event_type"] == "ReplayFailed" for item in own_payload["history"])

    admin_resp = client.get(f"/api/v1/crops/{crop_id}/replay/history?limit=10", headers=admin_headers)
    assert admin_resp.status_code == 200, admin_resp.text

    other_resp = client.get(f"/api/v1/crops/{crop_id}/replay/history?limit=10", headers=other_headers)
    assert other_resp.status_code == 404
