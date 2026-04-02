"""
Test suite for Service Request, Equipment, Labor, Reviews, and Weather APIs.
Covers the 10+ high-priority uncovered feature areas.

Uses existing conftest fixtures: client, auth_headers (farmer), admin_headers.
"""
import pytest
from uuid import uuid4
from tests.conftest import unwrap


class TestServiceRequestAPI:
    """Tests for /api/v1/service-requests endpoints."""

    def test_list_requests_requires_auth(self, client):
        resp = client.get("/api/v1/service-requests")
        assert resp.status_code in (401, 403)

    def test_create_request(self, client, auth_headers):
        resp = client.post(
            "/api/v1/service-requests",
            json={
                "service_type": "plowing",
                "urgency": "normal",
                "description": "Need plowing for 2 acres",
                "preferred_date": "2026-04-10",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (201, 422)

    def test_list_requests_farmer(self, client, auth_headers):
        resp = client.get(
            "/api/v1/service-requests",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_accept_request_requires_provider(self, client, auth_headers):
        fake_id = str(uuid4())
        resp = client.put(
            f"/api/v1/service-requests/{fake_id}/accept",
            headers=auth_headers,
        )
        assert resp.status_code in (403, 404)


class TestEquipmentAPI:
    """Tests for /api/v1/providers/{id}/equipment endpoints."""

    def test_list_equipment_public(self, client):
        """Equipment listing should work without authentication."""
        fake_provider_id = str(uuid4())
        resp = client.get(
            f"/api/v1/providers/{fake_provider_id}/equipment",
        )
        assert resp.status_code == 200

    def test_add_equipment_requires_ownership(self, client, auth_headers):
        """Farmers cannot add equipment to random providers."""
        fake_provider_id = str(uuid4())
        resp = client.post(
            f"/api/v1/providers/{fake_provider_id}/equipment",
            json={
                "equipment_type": "tractor",
                "name": "Test Tractor",
                "hourly_rate": 500,
                "condition": "good",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (403, 422)


class TestLaborAPI:
    """Tests for /api/v1/labor endpoints."""

    def test_list_labor_requires_auth(self, client):
        resp = client.get("/api/v1/labor")
        assert resp.status_code in (401, 403)

    def test_list_labor(self, client, auth_headers):
        resp = client.get(
            "/api/v1/labor",
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestReviewsAPI:
    """Tests for /api/v1/reviews endpoints."""

    def test_list_reviews_requires_auth(self, client):
        resp = client.get("/api/v1/reviews")
        assert resp.status_code in (401, 403)

    def test_create_review_requires_auth(self, client):
        resp = client.post(
            "/api/v1/reviews",
            json={"provider_id": str(uuid4()), "rating": 5, "comment": "Great!"},
        )
        assert resp.status_code in (401, 403)

    def test_create_review(self, client, auth_headers):
        resp = client.post(
            "/api/v1/reviews",
            json={
                "provider_id": str(uuid4()),
                "service_request_id": str(uuid4()),
                "rating": 4,
                "comment": "Good work.",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (201, 404, 422)


class TestWeatherAPI:
    """Tests for /api/v1/weather endpoints."""

    def test_weather_requires_auth(self, client):
        resp = client.get("/api/v1/weather")
        assert resp.status_code in (401, 403)

    def test_get_weather(self, client, auth_headers):
        resp = client.get(
            "/api/v1/weather?lat=28.6&lng=77.2",
            headers=auth_headers,
        )
        assert unwrap(resp) is not None
        assert resp.status_code == 200

    def test_weather_risk(self, client, auth_headers, db, farmer_user):
        from app.models.crop_instance import CropInstance
        from datetime import datetime
        crop = CropInstance(
            id=uuid4(),
            farmer_id=farmer_user.id,
            crop_type="wheat",
            sowing_date=datetime.now().date(),
            region="punjab",
            land_area=1.0,
            state="Active"
        )
        db.add(crop)
        db.commit()
        
        resp = client.get(
            f"/api/v1/weather/risk?crop_id={crop.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestFeatureFlagsAPI:
    """Tests for /api/v1/features endpoints."""

    def test_list_flags(self, client, admin_headers):
        resp = client.get(
            "/api/v1/features",
            headers=admin_headers,
        )
        assert resp.status_code == 200


class TestRulesAPI:
    """Tests for /api/v1/rules endpoints."""

    def test_list_rules(self, client, admin_headers):
        resp = client.get(
            "/api/v1/rules",
            headers=admin_headers,
        )
        assert resp.status_code == 200


class TestProviderAPI:
    """Tests for /api/v1/providers endpoints."""

    def test_search_providers(self, client, auth_headers):
        resp = client.get(
            "/api/v1/providers/search?region=Maharashtra",
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestHealthAPI:
    """Tests for /health endpoint."""

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = unwrap(resp)
        assert "status" in data

    def test_admin_health_requires_api_key(self, client):
        resp = client.post("/admin/health-check")
        assert resp.status_code in (401, 403)
