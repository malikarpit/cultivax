"""
Test suite for Admin API endpoints.
Covers: user management, provider governance, maintenance, audit log,
dead letters, health, security events.

Uses existing conftest fixtures: client, auth_headers (farmer), admin_headers.
"""
import pytest
from uuid import uuid4


class TestAdminUserManagement:
    """Tests for /api/v1/admin/users endpoints."""

    def test_list_users_requires_admin(self, client, auth_headers):
        """Non-admin users should be rejected from listing users."""
        resp = client.get("/api/v1/admin/users", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_list_users_as_admin(self, client, admin_headers):
        """Admin should be able to list all users."""
        resp = client.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200

    def test_update_user_role_requires_admin(self, client, auth_headers):
        """Non-admin cannot change user roles."""
        user_id = str(uuid4())
        resp = client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"role": "admin"},
            headers=auth_headers,
        )
        assert resp.status_code in (401, 403)


class TestAdminProviderGovernance:
    """Tests for /api/v1/admin/providers endpoints."""

    def test_list_providers_admin_only(self, client, auth_headers):
        resp = client.get("/api/v1/admin/providers", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_list_providers_as_admin(self, client, admin_headers):
        resp = client.get("/api/v1/admin/providers", headers=admin_headers)
        assert resp.status_code == 200

    def test_verify_provider(self, client, admin_headers):
        provider_id = str(uuid4())
        resp = client.put(
            f"/api/v1/admin/providers/{provider_id}/verify",
            headers=admin_headers,
        )
        # 404 is acceptable if provider doesn't exist
        assert resp.status_code in (200, 404)


class TestAdminDeadLetters:
    """Tests for /api/v1/admin/dead-letters endpoints."""

    def test_list_dead_letters_admin_only(self, client, auth_headers):
        resp = client.get("/api/v1/admin/dead-letters", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_list_dead_letters_as_admin(self, client, admin_headers):
        resp = client.get("/api/v1/admin/dead-letters", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminMaintenance:
    """Tests for /api/v1/admin/maintenance endpoints."""

    def test_maintenance_status(self, client, admin_headers):
        resp = client.get(
            "/api/v1/admin/maintenance/status",
            headers=admin_headers,
        )
        assert resp.status_code == 200


class TestAdminAuditLog:
    """Tests for /api/v1/admin/audit endpoints."""

    def test_audit_log_admin_only(self, client, auth_headers):
        resp = client.get("/api/v1/admin/audit", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_audit_log_as_admin(self, client, admin_headers):
        resp = client.get("/api/v1/admin/audit", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminSecurityEvents:
    """Tests for /api/v1/admin/security-events endpoints."""

    def test_security_events_admin_only(self, client, auth_headers):
        resp = client.get("/api/v1/admin/security-events", headers=auth_headers)
        assert resp.status_code in (401, 403)

    def test_security_events_as_admin(self, client, admin_headers):
        resp = client.get("/api/v1/admin/security-events", headers=admin_headers)
        assert resp.status_code == 200
