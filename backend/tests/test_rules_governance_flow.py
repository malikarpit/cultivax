from datetime import date, timedelta
from uuid import uuid4

from app.models.user import User
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str, idx: int) -> User:
    user = User(
        id=uuid4(),
        full_name=f"Rules {role.title()} {idx}",
        phone=f"+91{(9300000000 + idx):010d}",
        email=f"rules-{role}-{idx}-{uuid4().hex[:6]}@test.com",
        password_hash="hashed_test_password",
        role=role,
        region="Punjab",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def _rule_payload(version_id: str, effective_from: date) -> dict:
    return {
        "crop_type": "wheat",
        "region": "Punjab",
        "version_id": version_id,
        "effective_from_date": effective_from.isoformat(),
        "stage_definitions": [
            {"name": "germination", "duration_days": 10, "start_day": 0},
            {"name": "vegetative", "duration_days": 20, "start_day": 10},
        ],
        "risk_parameters": {
            "stress_threshold": 0.7,
            "max_drift_days": 7,
            "water_threshold": 0.3,
        },
        "irrigation_windows": {"germination": {"day": 5}},
        "fertilizer_windows": {"vegetative": {"day": 15}},
        "harvest_windows": {},
        "drift_limits": {"Active": 7},
    }


def _create_validate_approve_rule(client, creator_headers, approver_headers, version_id: str, effective_from: date):
    create_resp = client.post(
        "/api/v1/rules/",
        json=_rule_payload(version_id, effective_from),
        headers=creator_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    rule_id = unwrap(create_resp)["id"]

    validate_resp = client.post(f"/api/v1/rules/{rule_id}/validate", headers=creator_headers)
    assert validate_resp.status_code == 200, validate_resp.text
    assert unwrap(validate_resp)["status"] == "validated"

    approve_resp = client.post(f"/api/v1/rules/{rule_id}/approve", headers=approver_headers)
    assert approve_resp.status_code == 200, approve_resp.text
    assert unwrap(approve_resp)["status"] == "active"

    return rule_id


def test_rule_lifecycle_create_validate_approve_deprecate(client, db):
    admin_creator = _create_user(db, "admin", 1)
    admin_approver = _create_user(db, "admin", 2)
    creator_headers = _headers_for(admin_creator)
    approver_headers = _headers_for(admin_approver)

    rule_id = _create_validate_approve_rule(
        client,
        creator_headers,
        approver_headers,
        version_id="1.0",
        effective_from=date.today() - timedelta(days=60),
    )

    deprecate_resp = client.post(
        f"/api/v1/rules/{rule_id}/deprecate",
        json={"reason": "superseded by new template"},
        headers=approver_headers,
    )
    assert deprecate_resp.status_code == 200, deprecate_resp.text
    assert unwrap(deprecate_resp)["status"] == "deprecated"


def test_old_crop_rule_template_remains_pinned_after_new_activation(client, db):
    admin_creator = _create_user(db, "admin", 11)
    admin_approver = _create_user(db, "admin", 12)
    farmer = _create_user(db, "farmer", 13)

    creator_headers = _headers_for(admin_creator)
    approver_headers = _headers_for(admin_approver)
    farmer_headers = _headers_for(farmer)

    v1_id = _create_validate_approve_rule(
        client,
        creator_headers,
        approver_headers,
        version_id="1.0",
        effective_from=date.today() - timedelta(days=120),
    )

    existing_crop_resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "sowing_date": (date.today() - timedelta(days=60)).isoformat(),
            "region": "Punjab",
        },
        headers=farmer_headers,
    )
    assert existing_crop_resp.status_code == 201, existing_crop_resp.text
    existing_crop = unwrap(existing_crop_resp)
    assert existing_crop["rule_template_id"] == v1_id

    v2_id = _create_validate_approve_rule(
        client,
        creator_headers,
        approver_headers,
        version_id="2.0",
        effective_from=date.today() - timedelta(days=10),
    )

    old_crop_get = client.get(f"/api/v1/crops/{existing_crop['id']}", headers=farmer_headers)
    assert old_crop_get.status_code == 200, old_crop_get.text
    old_crop = unwrap(old_crop_get)
    assert old_crop["rule_template_id"] == v1_id

    new_crop_resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "sowing_date": (date.today() - timedelta(days=5)).isoformat(),
            "region": "Punjab",
        },
        headers=farmer_headers,
    )
    assert new_crop_resp.status_code == 201, new_crop_resp.text
    new_crop = unwrap(new_crop_resp)
    assert new_crop["rule_template_id"] == v2_id
