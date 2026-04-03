"""Feature 13 tests: simulation API validation and response contract."""

from datetime import date, timedelta
from uuid import UUID, uuid4

from app.models.crop_instance import CropInstance
from app.models.user import User
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str = "farmer") -> User:
    user = User(
        id=uuid4(),
        full_name=f"Feature13 {role.title()}",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"feature13-{role}-{uuid4().hex[:8]}@test.com",
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
    sowing = date.today() - timedelta(days=25)
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


def test_feature13_simulation_requires_auth(client, db):
    farmer = _create_user(db, role="farmer")
    crop_id = _create_crop(client, _headers_for(farmer))

    resp = client.post(
        f"/api/v1/crops/{crop_id}/simulate",
        json={"hypothetical_actions": [{"action_type": "irrigation"}]},
    )
    assert resp.status_code == 401


def test_feature13_simulation_rejects_invalid_action_type(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)

    resp = client.post(
        f"/api/v1/crops/{crop_id}/simulate",
        json={"hypothetical_actions": [{"action_type": "not_supported"}]},
        headers=headers,
    )
    assert resp.status_code == 422


def test_feature13_simulation_rejects_empty_actions(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)

    resp = client.post(
        f"/api/v1/crops/{crop_id}/simulate",
        json={"hypothetical_actions": []},
        headers=headers,
    )
    assert resp.status_code == 422


def test_feature13_simulation_rejects_closed_crop(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)

    crop = db.query(CropInstance).filter(CropInstance.id == UUID(crop_id)).first()
    crop.state = "Closed"
    db.commit()

    resp = client.post(
        f"/api/v1/crops/{crop_id}/simulate",
        json={"hypothetical_actions": [{"action_type": "irrigation"}]},
        headers=headers,
    )
    assert resp.status_code == 409


def test_feature13_simulation_returns_full_contract(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers)

    resp = client.post(
        f"/api/v1/crops/{crop_id}/simulate",
        json={
            "hypothetical_actions": [
                {"action_type": "irrigation", "action_date": (date.today() + timedelta(days=3)).isoformat()},
                {"action_type": "fertilizer", "action_date": (date.today() + timedelta(days=10)).isoformat()},
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    payload = unwrap(resp)
    assert "current_state" in payload
    assert "projected_state" in payload
    assert "deltas" in payload
    assert "action_breakdowns" in payload
    assert "state_transitions" in payload
    assert "warnings" in payload

    # Backward-compatible fields are still present for existing frontend usage.
    assert "projected_stress" in payload
    assert "projected_risk" in payload
    assert "projected_day_number" in payload
    assert "projected_stage" in payload
