"""
W8/W9/W10 — Phase 5 Platform Scale & Extensibility Tests

Covers:
  - Analytics Service and API (FR-35, NFR-15, OR-12/13)
  - User Reporting (OR-14, OR-15)
  - Configuration/Extensibility (FR-38)
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
import json

from app.models.user_report import UserReport
from app.models.region_config import RegionConfig

# ===========================================================================
# Analytics API Tests (W8)
# ===========================================================================

class TestAnalyticsOverview:
    def test_overview_admin_only(self, client, auth_headers):
        # auth_headers is usually a farmer depending on conftest
        # Try fetching with standard headers (assume farmer)
        resp = client.get("/api/v1/analytics/overview", headers=auth_headers)
        assert resp.status_code in (401, 403)
        
    def test_overview_success(self, client, admin_headers):
        resp = client.get("/api/v1/analytics/overview", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "users" in data
        assert "crops" in data
        assert "alerts" in data
        assert "computed_at" in data

    def test_activity_timeline(self, client, admin_headers):
        resp = client.get("/api/v1/analytics/activity?days=7", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "timeline" in data
        assert data["days"] == 7

    def test_crop_distribution(self, client, admin_headers):
        resp = client.get("/api/v1/analytics/crops/distribution", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "by_type" in data
        assert "by_state" in data
        assert "by_season" in data

    def test_region_demand(self, client, admin_headers):
        resp = client.get("/api/v1/analytics/regions/demand", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "regions" in data


# ===========================================================================
# User Reporting Tests (W9)
# ===========================================================================

class TestUserReporting:
    def test_file_report_success(self, client, auth_headers):
        target_id = str(uuid4())
        resp = client.post(
            "/api/v1/reports",
            headers=auth_headers,
            json={
                "reported_id": target_id,
                "category": "fraud",
                "description": "Fake listing"
            }
        )
        assert resp.status_code == 201
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert data["status"] == "open"
        assert data["category"] == "fraud"
        assert "id" in data

    def test_file_report_invalid_category(self, client, auth_headers):
        target_id = str(uuid4())
        resp = client.post(
            "/api/v1/reports",
            headers=auth_headers,
            json={
                "reported_id": target_id,
                "category": "not_a_valid_category_xyz",
            }
        )
        assert resp.status_code == 422

    def test_my_reports_list(self, client, auth_headers):
        resp = client.get("/api/v1/reports/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_admin_list_reports(self, client, admin_headers):
        resp = client.get("/api/v1/admin/reports", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "items" in data

    def test_admin_review_report(self, client, auth_headers, admin_headers):
        # Create report as user
        post_resp = client.post(
            "/api/v1/reports",
            headers=auth_headers,
            json={
                "reported_id": str(uuid4()),
                "category": "abuse",
            }
        )
        assert post_resp.status_code == 201
        report_id = (post_resp.json()["data"] if "data" in post_resp.json() else post_resp.json())["id"]

        # Review report as admin
        rev_resp = client.patch(
            f"/api/v1/admin/reports/{report_id}/review",
            headers=admin_headers,
            json={"review_notes": "Looked into it"}
        )
        assert rev_resp.status_code == 200
        data = rev_resp.json()["data"] if "data" in rev_resp.json() else rev_resp.json()
        assert data["status"] == "reviewed"


# ===========================================================================
# Extensibility/Config Tests (W10)
# ===========================================================================

class TestConfigRegions:
    def test_create_region(self, client, admin_headers):
        # Create unique region name to avoid DB collision with other test runs
        rname = "NewRegion_" + str(uuid4())[:8]
        resp = client.post(
             "/api/v1/config/regions",
             headers=admin_headers,
             json={
                 "region_name": rname,
                 "is_active": True,
                 "parameters": {"supported_crops": ["wheat"]}
             }
        )
        assert resp.status_code == 201
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert data["region_name"] == rname
        assert data["parameters"]["supported_crops"] == ["wheat"]

    def test_list_regions_public(self, client):
        resp = client.get("/api/v1/config/regions")
        assert resp.status_code == 200
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_update_region(self, client, admin_headers):
        rname = "UpdateRegion_" + str(uuid4())[:8]
        create_resp = client.post(
             "/api/v1/config/regions",
             headers=admin_headers,
             json={
                 "region_name": rname,
                 "is_active": True,
                 "parameters": {}
             }
        )
        assert create_resp.status_code == 201
        region_id = (create_resp.json()["data"] if "data" in create_resp.json() else create_resp.json())["id"]

        # Update
        update_resp = client.put(
             f"/api/v1/config/regions/{region_id}",
             headers=admin_headers,
             json={
                 "region_name": rname,
                 "is_active": False,
                 "parameters": {"test": 123}
             }
        )
        assert update_resp.status_code == 200
        data = update_resp.json()["data"] if "data" in update_resp.json() else update_resp.json()
        assert data["is_active"] is False
        assert data["parameters"]["test"] == 123
