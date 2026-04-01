"""
Feature 11 tests: recommendation generation lifecycle and status actions.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID, uuid4

from app.models.user import User
from app.models.crop_instance import CropInstance
from app.security.auth import create_access_token
from app.services.cron import run_scheduled_tasks
from tests.conftest import unwrap


def _create_user(db, role: str = "farmer") -> User:
    user = User(
        id=uuid4(),
        full_name=f"Feature11 {role.title()}",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"feature11-{role}-{uuid4().hex[:8]}@test.com",
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
    sowing = date.today() - timedelta(days=35)
    resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "variety": "HD-2967",
            "sowing_date": sowing.isoformat(),
            "region": "Punjab",
            "land_area": 2.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return unwrap(resp)["id"]


def _set_crop_at_risk(db, crop_id: str):
    crop = db.query(CropInstance).filter(CropInstance.id == UUID(crop_id)).first()
    crop.state = "AtRisk"
    crop.risk_index = 0.72
    db.commit()


def test_feature11_get_recommendations_on_demand_generates(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)
    _set_crop_at_risk(db, crop_id)

    resp = client.get(f"/api/v1/crops/{crop_id}/recommendations?on_demand=true", headers=headers)
    assert resp.status_code == 200, resp.text
    payload = unwrap(resp)
    assert len(payload) >= 1
    assert payload[0]["status"] == "active"


def test_feature11_dismiss_and_act_recommendation(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)
    _set_crop_at_risk(db, crop_id)

    recs = client.get(f"/api/v1/crops/{crop_id}/recommendations", headers=headers)
    assert recs.status_code == 200, recs.text
    rec_id = unwrap(recs)[0]["id"]

    dismiss_resp = client.patch(
        f"/api/v1/crops/{crop_id}/recommendations/{rec_id}/dismiss",
        json={"reason": "already completed"},
        headers=headers,
    )
    assert dismiss_resp.status_code == 200, dismiss_resp.text
    assert unwrap(dismiss_resp)["status"] == "dismissed"

    # Force regeneration and mark a fresh recommendation as acted.
    recs_after = client.get(f"/api/v1/crops/{crop_id}/recommendations?on_demand=true", headers=headers)
    fresh_rec_id = unwrap(recs_after)[0]["id"]

    act_resp = client.patch(
        f"/api/v1/crops/{crop_id}/recommendations/{fresh_rec_id}/act",
        json={"reason": "irrigation done"},
        headers=headers,
    )
    assert act_resp.status_code == 200, act_resp.text
    assert unwrap(act_resp)["status"] == "acted"


def test_feature11_recommendation_ownership_and_admin_access(client, db):
    owner = _create_user(db, role="farmer")
    stranger = _create_user(db, role="farmer")
    admin = _create_user(db, role="admin")

    owner_headers = _headers_for(owner)
    stranger_headers = _headers_for(stranger)
    admin_headers = _headers_for(admin)

    crop_id = _create_crop(client, owner_headers)
    _set_crop_at_risk(db, crop_id)

    owner_recs = client.get(f"/api/v1/crops/{crop_id}/recommendations", headers=owner_headers)
    assert owner_recs.status_code == 200, owner_recs.text
    rec_id = unwrap(owner_recs)[0]["id"]

    forbidden = client.patch(
        f"/api/v1/crops/{crop_id}/recommendations/{rec_id}/dismiss",
        json={"reason": "not-owner"},
        headers=stranger_headers,
    )
    assert forbidden.status_code == 403

    admin_read = client.get(f"/api/v1/crops/{crop_id}/recommendations", headers=admin_headers)
    assert admin_read.status_code == 200, admin_read.text


def test_feature11_cron_includes_recommendation_refresh(client, db):
    farmer = _create_user(db, role="farmer")
    crop_id = _create_crop(client, _headers_for(farmer))
    _set_crop_at_risk(db, crop_id)

    result = asyncio.run(run_scheduled_tasks(db, cadence="daily", force=True))
    tasks = result.get("tasks", result)
    assert "recommendations" in tasks
    assert tasks["recommendations"]["status"] == "ok"
    assert tasks["recommendations"]["crops_refreshed"] >= 1
