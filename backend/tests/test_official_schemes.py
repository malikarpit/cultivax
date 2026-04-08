"""
W3 — Official Schemes / Portal Redirect Tests — FR-31

Covers:
  - List schemes with region/crop_type filters
  - Redirect logged in audit trail for authenticated user
  - Admin can create scheme; farmer cannot
  - Admin can update scheme
  - Inactive schemes hidden from public listing
"""
import pytest
from uuid import uuid4
from datetime import date
from tests.conftest import unwrap


def _make_admin_headers(client, db):
    from app.models.user import User
    from app.security.auth import create_access_token
    admin = User(
        id=uuid4(), full_name="Scheme Admin", role="admin",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"scheme-admin-{uuid4().hex[:6]}@test.in",
        password_hash="hash", region="Punjab", is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id), 'role': 'admin'})}"}


def _seed_scheme(db, region="Punjab", crop_type="wheat", category="subsidy", is_active=True):
    from app.models.official_scheme import OfficialScheme
    s = OfficialScheme(
        id=uuid4(),
        name=f"Test Scheme {uuid4().hex[:4]}",
        description="A test government scheme",
        portal_url="https://gov.test/scheme",
        category=category,
        region=region,
        crop_type=crop_type,
        is_active=is_active,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


class TestSchemeListing:

    def test_list_schemes_returns_active_only(self, client, db):
        """Public scheme list must exclude inactive schemes."""
        active = _seed_scheme(db, region="Pradesh")
        inactive = _seed_scheme(db, region="Pradesh", is_active=False)

        resp = client.get("/api/v1/schemes?region=Pradesh")
        assert resp.status_code == 200
        data = unwrap(resp)
        items = data["items"]
        ids = [s["id"] for s in items]
        assert str(active.id) in ids
        assert str(inactive.id) not in ids

    def test_list_schemes_filters_by_region(self, client, db):
        """Region filter returns only matching schemes."""
        target = _seed_scheme(db, region="Haryana", crop_type="rice")
        other = _seed_scheme(db, region="Gujarat", crop_type="cotton")

        resp = client.get("/api/v1/schemes?region=Haryana")
        assert resp.status_code == 200
        ids = [s["id"] for s in unwrap(resp)["items"]]
        assert str(target.id) in ids
        assert str(other.id) not in ids

    def test_list_schemes_filters_by_category(self, client, db):
        """Category filter returns only matching schemes."""
        _seed_scheme(db, category="insurance")
        _seed_scheme(db, category="advisory")

        resp = client.get("/api/v1/schemes?category=insurance")
        assert resp.status_code == 200
        items = unwrap(resp)["items"]
        for item in items:
            assert item["category"] == "insurance"

    def test_get_scheme_detail(self, client, db):
        """GET /schemes/{id} returns full scheme detail."""
        scheme = _seed_scheme(db, region="Punjab")
        resp = client.get(f"/api/v1/schemes/{scheme.id}")
        assert resp.status_code == 200
        data = unwrap(resp)
        assert data["id"] == str(scheme.id)
        assert "portal_url" in data

    def test_get_inactive_scheme_returns_404(self, client, db):
        """Inactive schemes return 404 on detail view."""
        scheme = _seed_scheme(db, is_active=False)
        resp = client.get(f"/api/v1/schemes/{scheme.id}")
        assert resp.status_code == 404


class TestSchemeRedirect:

    def test_redirect_logged_for_authenticated_user(self, client, auth_headers, db):
        """POST /schemes/{id}/redirect logs redirect and returns portal_url."""
        from app.models.scheme_redirect_log import SchemeRedirectLog
        scheme = _seed_scheme(db)

        resp = client.post(f"/api/v1/schemes/{scheme.id}/redirect", headers=auth_headers)
        assert resp.status_code == 200
        data = unwrap(resp)
        assert data["redirect_url"] == scheme.portal_url

        log = db.query(SchemeRedirectLog).filter(
            SchemeRedirectLog.scheme_id == scheme.id
        ).first()
        assert log is not None
        assert log.redirect_url == scheme.portal_url

    def test_redirect_to_inactive_scheme_returns_404(self, client, auth_headers, db):
        """Cannot redirect to inactive scheme."""
        scheme = _seed_scheme(db, is_active=False)
        resp = client.post(f"/api/v1/schemes/{scheme.id}/redirect", headers=auth_headers)
        assert resp.status_code == 404


class TestSchemeAdminManagement:

    def test_admin_can_create_scheme(self, client, db):
        """Admin can POST /schemes to create a new scheme."""
        admin_headers = _make_admin_headers(client, db)
        resp = client.post(
            "/api/v1/schemes",
            json={
                "name": "PM-KISAN Portal",
                "portal_url": "https://pmkisan.gov.in",
                "category": "subsidy",
                "region": "Punjab",
                "crop_type": "wheat",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = unwrap(resp)
        assert "id" in data

    def test_farmer_cannot_create_scheme(self, client, auth_headers):
        """Farmer role cannot create schemes."""
        resp = client.post(
            "/api/v1/schemes",
            json={
                "name": "Fake Scheme",
                "portal_url": "https://example.com",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (401, 403)

    def test_admin_can_update_scheme(self, client, db):
        """Admin can PUT /schemes/{id} to update scheme fields."""
        admin_headers = _make_admin_headers(client, db)
        scheme = _seed_scheme(db)

        resp = client.put(
            f"/api/v1/schemes/{scheme.id}",
            json={"name": "Updated Name", "is_active": False},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = unwrap(resp)
        assert data["is_active"] is False
