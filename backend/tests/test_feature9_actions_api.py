"""
Feature 9 tests: crop history and lifecycle timeline action APIs.
"""

from datetime import date, timedelta
from uuid import uuid4

from app.models.user import User
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str = "farmer") -> User:
    user = User(
        id=uuid4(),
        full_name=f"Feature9 {role.title()}",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"feature9-{role}-{uuid4().hex[:8]}@test.com",
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
    sowing = date.today() - timedelta(days=40)
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


def _log_action(client, crop_id: str, headers: dict, action_type: str, day_offset: int, key: str):
    effective = date.today() - timedelta(days=day_offset)
    resp = client.post(
        f"/api/v1/crops/{crop_id}/actions/",
        json={
            "action_type": action_type,
            "effective_date": effective.isoformat(),
            "category": "Operational",
            "metadata_json": {"reason": "feature9-test"},
            "notes": f"{action_type} action",
            "idempotency_key": key,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


def test_feature9_actions_list_returns_paginated_contract_and_aliases(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)

    crop_id = _create_crop(client, headers)

    _log_action(client, crop_id, headers, "irrigation", 20, "f9-irr")
    _log_action(client, crop_id, headers, "fertilizer", 10, "f9-fert")

    resp = client.get(
        f"/api/v1/crops/{crop_id}/actions/?page=1&page_size=1&sort=-effective_date",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    payload = unwrap(resp)
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["has_more"] is True
    assert len(payload["actions"]) == 1

    action = payload["actions"][0]
    assert action["action_type"] == "fertilizer"
    assert "effective_date" in action
    assert "metadata_json" in action
    assert "source" in action
    assert "action_impact_type" in action
    assert "applied_in_replay" in action


def test_feature9_actions_list_enforces_crop_ownership(client, db):
    owner = _create_user(db, role="farmer")
    stranger = _create_user(db, role="farmer")

    owner_headers = _headers_for(owner)
    stranger_headers = _headers_for(stranger)

    crop_id = _create_crop(client, owner_headers)

    resp = client.get(f"/api/v1/crops/{crop_id}/actions/", headers=stranger_headers)
    assert resp.status_code == 403
