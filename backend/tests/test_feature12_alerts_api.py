"""
Feature 12 tests: alerts and notifications API behavior.
"""

import asyncio
from datetime import date, timedelta, datetime, timezone
from uuid import UUID, uuid4

from app.models.alert import Alert
from app.models.user import User
from app.security.auth import create_access_token
from app.services.cron import run_scheduled_tasks
from tests.conftest import unwrap


def _create_user(db, role: str = "farmer") -> User:
    user = User(
        id=uuid4(),
        full_name=f"Feature12 {role.title()}",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"feature12-{role}-{uuid4().hex[:8]}@test.com",
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
    sowing = date.today() - timedelta(days=20)
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


def _seed_alert(db, user_id: UUID, crop_id: UUID, *, severity: str, urgency: str, alert_type: str = "stress_alert", expires_offset_hours: int = 24) -> Alert:
    alert = Alert(
        user_id=user_id,
        crop_instance_id=crop_id,
        alert_type=alert_type,
        severity=severity,
        urgency_level=urgency,
        message=f"{severity} alert",
        details={"source": "test"},
        source_event_id=uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_offset_hours),
        is_acknowledged=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def test_feature12_get_alerts_returns_full_contract(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = UUID(_create_crop(client, headers))

    _seed_alert(db, farmer.id, crop_id, severity="high", urgency="High")

    resp = client.get("/api/v1/alerts/?unacknowledged_only=true", headers=headers)
    assert resp.status_code == 200, resp.text
    payload = unwrap(resp)
    assert len(payload) >= 1

    alert = payload[0]
    assert "id" in alert
    assert "user_id" in alert
    assert "crop_instance_id" in alert
    assert "urgency_level" in alert
    assert "details" in alert
    assert "source_event_id" in alert
    assert "expires_at" in alert


def test_feature12_alert_filters_and_pagination(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = UUID(_create_crop(client, headers))

    _seed_alert(db, farmer.id, crop_id, severity="critical", urgency="Critical", alert_type="weather_alert")
    _seed_alert(db, farmer.id, crop_id, severity="high", urgency="High", alert_type="stress_alert")
    _seed_alert(db, farmer.id, crop_id, severity="medium", urgency="Medium", alert_type="risk_alert")

    filter_resp = client.get(
        "/api/v1/alerts/?unacknowledged_only=true&severity=critical",
        headers=headers,
    )
    assert filter_resp.status_code == 200, filter_resp.text
    filtered = unwrap(filter_resp)
    assert len(filtered) == 1
    assert filtered[0]["severity"] == "critical"

    page_resp = client.get(
        "/api/v1/alerts/?unacknowledged_only=true&skip=0&limit=2",
        headers=headers,
    )
    assert page_resp.status_code == 200, page_resp.text
    assert len(unwrap(page_resp)) == 2


def test_feature12_acknowledge_and_bulk_acknowledge(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = UUID(_create_crop(client, headers))

    alert1 = _seed_alert(db, farmer.id, crop_id, severity="high", urgency="High")
    alert2 = _seed_alert(db, farmer.id, crop_id, severity="medium", urgency="Medium")

    ack_one = client.put(f"/api/v1/alerts/{alert1.id}/acknowledge", headers=headers)
    assert ack_one.status_code == 200, ack_one.text
    assert unwrap(ack_one)["is_acknowledged"] is True

    bulk = client.post(
        "/api/v1/alerts/acknowledge-bulk",
        json={"alert_ids": [str(alert2.id)]},
        headers=headers,
    )
    assert bulk.status_code == 200, bulk.text
    assert unwrap(bulk)["acknowledged_count"] == 1


def test_feature12_cron_alert_cleanup(client, db):
    farmer = _create_user(db, role="farmer")
    headers = _headers_for(farmer)
    crop_id = UUID(_create_crop(client, headers))

    old_expired = _seed_alert(
        db,
        farmer.id,
        crop_id,
        severity="low",
        urgency="Low",
        expires_offset_hours=-2,
    )

    result = asyncio.run(run_scheduled_tasks(db, cadence="hourly", force=True))
    tasks = result.get("tasks", result)
    assert "alert_cleanup" in tasks
    assert tasks["alert_cleanup"]["status"] == "ok"
    assert tasks["alert_cleanup"]["alerts_cleaned"] >= 1

    refreshed = db.query(Alert).filter(Alert.id == old_expired.id).first()
    assert refreshed.is_deleted is True
