from datetime import date, timedelta

from app.config import settings
from app.models.crop_instance import CropInstance
from app.services.event_dispatcher.mutation_guard import allow_ctis_mutation
from tests.conftest import unwrap


def _create_crop(client, auth_headers):
    sowing = date.today() - timedelta(days=45)
    resp = client.post(
        "/api/v1/crops/",
        json={
            "crop_type": "wheat",
            "sowing_date": sowing.isoformat(),
            "region": "Punjab",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return unwrap(resp)


def test_action_logging_works_with_mutation_guard_enabled(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "CTIS_MUTATION_GUARD_ENABLED", True)
    crop = _create_crop(client, auth_headers)

    action_resp = client.post(
        f"/api/v1/crops/{crop['id']}/actions/",
        json={
            "action_type": "irrigation",
            "effective_date": (date.today() - timedelta(days=30)).isoformat(),
            "idempotency_key": "guard-enabled-action-1",
        },
        headers=auth_headers,
    )
    assert action_resp.status_code == 201, action_resp.text


def test_modify_sowing_date_works_with_mutation_guard_enabled(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "CTIS_MUTATION_GUARD_ENABLED", True)
    crop = _create_crop(client, auth_headers)

    new_date = date.today() - timedelta(days=20)
    resp = client.put(
        f"/api/v1/crops/{crop['id']}/sowing-date",
        json={"new_sowing_date": new_date.isoformat()},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text


def test_admin_recovery_clear_works_with_mutation_guard_enabled(
    client,
    db,
    auth_headers,
    admin_headers,
    monkeypatch,
):
    monkeypatch.setattr(settings, "CTIS_MUTATION_GUARD_ENABLED", True)
    crop = _create_crop(client, auth_headers)

    crop_row = db.query(CropInstance).filter(CropInstance.id == crop["id"]).first()
    assert crop_row is not None

    with allow_ctis_mutation():
        crop_row.state = "RecoveryRequired"
        db.commit()

    resp = client.patch(
        f"/api/v1/crops/{crop['id']}/_admin/recovery/clear",
        params={"reason": "manual resolution"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    db.refresh(crop_row)
    assert crop_row.state == "Active"