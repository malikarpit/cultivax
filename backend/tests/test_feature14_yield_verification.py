from datetime import date, timedelta
from uuid import UUID, uuid4

from app.models.crop_instance import CropInstance
from app.models.user import User
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str) -> User:
    user = User(
        id=uuid4(),
        email=f"{role}-{uuid4().hex[:6]}@test.com",
        phone=f"+91{uuid4().int % 10**10:010d}",
        password_hash="hashed_test_password",
        role=role,
        full_name=f"Test {role.title()}",
        region="Punjab",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def _create_crop(client, headers: dict[str, str], db, state: str = "ReadyToHarvest") -> str:
    sowing = date.today() - timedelta(days=90)
    resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "variety": "HD-2967",
            "sowing_date": sowing.isoformat(),
            "region": "Punjab",
            "land_area": 4.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    crop_id = unwrap(resp)["id"]
    crop = db.query(CropInstance).filter(CropInstance.id == UUID(crop_id)).first()
    crop.state = state
    db.commit()
    return crop_id


def test_submit_yield_maps_extended_fields_and_returns_verification(client, db):
    farmer = _create_user(db, "farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers, db)

    resp = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={
            "yield_quantity_kg": 4800,
            "harvest_date": date.today().isoformat(),
            "quality_grade": "A",
            "moisture_content_pct": 11.5,
            "notes": "Strong grain fill",
        },
        headers=headers,
    )

    assert resp.status_code == 201, resp.text
    data = unwrap(resp)
    assert data["reported_yield"] == 4800
    assert data["quality_grade"] == "A"
    assert data["moisture_pct"] == 11.5
    assert data["notes"] == "Strong grain fill"
    assert "verification_metadata" in data
    assert isinstance(data["verification_metadata"], dict)


def test_submit_yield_requires_farmer_role(client, db):
    farmer = _create_user(db, "farmer")
    provider = _create_user(db, "provider")
    crop_id = _create_crop(client, _headers_for(farmer), db)

    resp = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={"reported_yield": 1000, "yield_unit": "kg"},
        headers=_headers_for(provider),
    )

    assert resp.status_code == 403


def test_duplicate_yield_submission_is_rejected(client, db):
    farmer = _create_user(db, "farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers, db)

    first = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={"reported_yield": 1000, "yield_unit": "kg"},
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={"reported_yield": 1200, "yield_unit": "kg"},
        headers=headers,
    )
    assert second.status_code == 409


def test_yield_history_endpoint_returns_records(client, db):
    farmer = _create_user(db, "farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers, db)

    submit = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={"reported_yield": 2300, "yield_unit": "kg"},
        headers=headers,
    )
    assert submit.status_code == 201, submit.text

    latest = client.get(f"/api/v1/crops/{crop_id}/yield", headers=headers)
    assert latest.status_code == 200
    assert unwrap(latest)["reported_yield"] == 2300

    history = client.get(f"/api/v1/crops/{crop_id}/yield/history", headers=headers)
    assert history.status_code == 200
    payload = unwrap(history)
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["reported_yield"] == 2300


def test_submit_yield_requires_ready_to_harvest_state(client, db):
    farmer = _create_user(db, "farmer")
    headers = _headers_for(farmer)
    crop_id = _create_crop(client, headers, db, state="Active")

    resp = client.post(
        f"/api/v1/crops/{crop_id}/yield",
        json={"reported_yield": 1500, "yield_unit": "kg"},
        headers=headers,
    )

    assert resp.status_code == 400
    body = resp.json()
    error_msg = body.get("detail", body.get("error", ""))
    assert "ReadyToHarvest" in error_msg or "ReadyToHarvest" in str(body)
