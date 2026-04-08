"""
W4 — Dispute Resolution Tests — FR-33

Covers:
  - Farmer opens dispute, gets SLA deadline set
  - Farmer sees own disputes, not others'
  - Invalid category rejected
  - Admin assigns dispute → status=investigating
  - Admin resolves dispute with notes → status=resolved
  - Admin dismisses dispute with reason → status=dismissed
  - Admin overdue filter returns cases past SLA
  - Non-admin cannot access admin dispute queue
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta, datetime, timezone
from tests.conftest import unwrap
from sqlalchemy import text


def _make_admin(db):
    from app.models.user import User
    from app.security.auth import create_access_token
    admin = User(
        id=uuid4(), full_name="Dispute Admin", role="admin",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"dispute-admin-{uuid4().hex[:6]}@test.in",
        password_hash="hash", region="Punjab", is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id), 'role': 'admin'})}"}
    return admin, headers


def _make_second_farmer(db):
    from app.models.user import User
    from app.security.auth import create_access_token
    u = User(
        id=uuid4(), full_name="Other Farmer", role="farmer",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"farmer2-{uuid4().hex[:6]}@test.in",
        password_hash="hash", region="Punjab", is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, {"Authorization": f"Bearer {create_access_token({'sub': str(u.id), 'role': 'farmer'})}"}


def _open_dispute(client, headers, respondent_id, category="quality"):
    return client.post(
        "/api/v1/disputes",
        json={"respondent_id": str(respondent_id), "category": category, "description": "Test dispute"},
        headers=headers,
    )


class TestDisputeLifecycle:

    def test_farmer_opens_dispute_with_sla(self, client, auth_headers, db):
        """FR-33: opening a dispute must set status=open and sla_deadline."""
        resp = _open_dispute(client, auth_headers, uuid4())
        assert resp.status_code == 201
        data = unwrap(resp)
        assert data["status"] == "open"
        assert data.get("sla_deadline") is not None

    def test_invalid_category_rejected(self, client, auth_headers):
        """FR-33: invalid dispute category must return 422."""
        resp = _open_dispute(client, auth_headers, uuid4(), category="illegal_category")
        assert resp.status_code == 422

    def test_farmer_lists_own_disputes(self, client, auth_headers, db):
        """FR-33: farmer can see disputes they filed."""
        _open_dispute(client, auth_headers, uuid4())
        resp = client.get("/api/v1/disputes", headers=auth_headers)
        assert resp.status_code == 200
        assert unwrap(resp)["total"] >= 1

    def test_farmer_does_not_see_other_farmers_disputes(self, client, auth_headers, db):
        """FR-33: farmer only sees their own disputes."""
        _open_dispute(client, auth_headers, uuid4())
        _farmer2, farmer2_headers = _make_second_farmer(db)
        resp = client.get("/api/v1/disputes", headers=farmer2_headers)
        assert resp.status_code == 200
        assert unwrap(resp)["total"] == 0


class TestDisputeAdminManagement:

    def test_admin_assigns_dispute(self, client, auth_headers, db):
        """FR-33: admin assigns dispute → status becomes investigating."""
        admin, admin_headers = _make_admin(db)
        admin2, _ = _make_admin(db)

        case_id = unwrap(_open_dispute(client, auth_headers, uuid4()))["id"]

        resp = client.patch(
            f"/api/v1/admin/disputes/{case_id}/assign",
            json={"assignee_id": str(admin2.id)},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = unwrap(resp)
        assert data["status"] == "investigating"
        assert data["assigned_to"] == str(admin2.id)

    def test_admin_resolves_dispute(self, client, auth_headers, db):
        """FR-33: admin resolves dispute → status=resolved with notes."""
        _, admin_headers = _make_admin(db)
        case_id = unwrap(_open_dispute(client, auth_headers, uuid4()))["id"]

        resp = client.patch(
            f"/api/v1/admin/disputes/{case_id}/resolve",
            json={"resolution_notes": "Refund issued to farmer."},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert unwrap(resp)["status"] == "resolved"

    def test_admin_dismisses_dispute(self, client, auth_headers, db):
        """FR-33: admin dismisses dispute → status=dismissed."""
        _, admin_headers = _make_admin(db)
        case_id = unwrap(_open_dispute(client, auth_headers, uuid4()))["id"]

        resp = client.patch(
            f"/api/v1/admin/disputes/{case_id}/dismiss",
            json={"reason": "Insufficient evidence"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert unwrap(resp)["status"] == "dismissed"

    def test_farmer_cannot_access_admin_dispute_queue(self, client, auth_headers):
        """FR-33: farmer role must be rejected from admin dispute queue."""
        resp = client.get("/api/v1/admin/disputes", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_admin_dispute_queue_lists_all(self, client, auth_headers, db):
        """FR-33: admin sees all disputes regardless of reporter."""
        _, admin_headers = _make_admin(db)
        farmer2, farmer2_headers = _make_second_farmer(db)

        _open_dispute(client, auth_headers, uuid4())
        _open_dispute(client, farmer2_headers, uuid4())

        resp = client.get("/api/v1/admin/disputes", headers=admin_headers)
        assert resp.status_code == 200
        assert unwrap(resp)["total"] >= 2

    def test_overdue_filter_returns_sla_exceeded_cases(self, client, auth_headers, db):
        """FR-33: ?overdue_only=true returns only open cases past SLA deadline."""
        _, admin_headers = _make_admin(db)
        case_id = unwrap(_open_dispute(client, auth_headers, uuid4()))["id"]

        db.execute(
            text("UPDATE dispute_cases SET sla_deadline = NOW() - INTERVAL '2 hours' WHERE id = :case_id"),
            {"case_id": case_id},
        )
        db.commit()

        resp = client.get("/api/v1/admin/disputes?overdue_only=true", headers=admin_headers)
        assert resp.status_code == 200
        data = unwrap(resp)
        ids = [d["id"] for d in data["items"]]
        assert case_id in ids
        for d in data["items"]:
            assert d["overdue"] is True

    def test_non_existent_dispute_returns_404(self, client, db):
        """FR-33: resolving a non-existent dispute returns 404."""
        _, admin_headers = _make_admin(db)
        resp = client.patch(
            f"/api/v1/admin/disputes/{uuid4()}/resolve",
            json={"resolution_notes": "ghost"},
            headers=admin_headers,
        )
        assert resp.status_code == 404
