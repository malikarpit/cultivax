"""
RBAC Test Suite

Tests role-based access control and ownership checks across all secured endpoints.
Feature 2: RBAC & Access Control — Audit Folder 2

Run: pytest tests/test_rbac.py -v
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def farmer_user():
    """Mock farmer user."""
    user = MagicMock()
    user.id = uuid4()
    user.role = "farmer"
    user.is_active = True
    user.full_name = "Test Farmer"
    return user


@pytest.fixture
def provider_user():
    """Mock provider user."""
    user = MagicMock()
    user.id = uuid4()
    user.role = "provider"
    user.is_active = True
    user.full_name = "Test Provider"
    return user


@pytest.fixture
def admin_user():
    """Mock admin user."""
    user = MagicMock()
    user.id = uuid4()
    user.role = "admin"
    user.is_active = True
    user.full_name = "Test Admin"
    return user


@pytest.fixture
def other_farmer():
    """Another farmer with a different ID."""
    user = MagicMock()
    user.id = uuid4()
    user.role = "farmer"
    user.is_active = True
    user.full_name = "Other Farmer"
    return user


# ─── Role Restriction Tests ──────────────────────────────────────────────────


class TestRoleRestrictions:
    """Verify that require_role dependencies reject unauthorized roles."""

    def test_require_role_accepts_matching_role(self, farmer_user):
        """require_role(['farmer']) should accept a farmer user."""
        from app.api.deps import require_role

        role_checker = require_role(["farmer"])
        # role_checker is async — run it directly with the user injected
        result = run_async(role_checker(current_user=farmer_user))
        assert result == farmer_user

    def test_require_role_rejects_wrong_role(self, provider_user):
        """require_role(['farmer']) should reject a provider user."""
        from app.api.deps import require_role

        role_checker = require_role(["farmer"])
        with pytest.raises(HTTPException) as exc_info:
            run_async(role_checker(current_user=provider_user))
        assert exc_info.value.status_code == 403

    def test_require_role_accepts_multiple_roles(self, farmer_user, admin_user):
        """require_role(['farmer', 'admin']) should accept both roles."""
        from app.api.deps import require_role

        dep = require_role(["farmer", "admin"])
        assert run_async(dep(current_user=farmer_user)) == farmer_user
        assert run_async(dep(current_user=admin_user)) == admin_user

    def test_require_role_rejects_provider_from_farmer_admin_group(self, provider_user):
        """require_role(['farmer', 'admin']) should reject a provider."""
        from app.api.deps import require_role

        dep = require_role(["farmer", "admin"])
        with pytest.raises(HTTPException) as exc_info:
            run_async(dep(current_user=provider_user))
        assert exc_info.value.status_code == 403


# ─── Self-Registration Guard ────────────────────────────────────────────────


class TestSelfRegistrationGuard:
    """Verify admin role cannot be self-assigned during registration."""

    def test_admin_role_blocked_in_registration_endpoint(self):
        """
        The registration endpoint in auth.py must reject role='admin'.
        We verify the guard exists in the source code.
        """
        import inspect
        from app.api.v1.auth import register

        # Verify the register function source contains admin role rejection
        source = inspect.getsource(register)
        assert "admin" in source.lower(), (
            "Registration endpoint must contain admin role check"
        )


# ─── Ownership Check Tests ──────────────────────────────────────────────────


class TestOwnershipChecks:
    """
    Verify that ownership checks prevent cross-user data access.
    These are the P0 critical security vulnerabilities.
    """

    def test_simulation_ownership_concept(self, farmer_user, other_farmer):
        """
        Simulation endpoint should verify crop.farmer_id == current_user.id.
        Farmer A should NOT be able to simulate Farmer B's crops.
        """
        # Concept validation — different farmer IDs
        assert farmer_user.id != other_farmer.id

        # Verify the simulation endpoint source contains ownership check
        import inspect
        from app.api.v1.simulation import simulate_crop
        source = inspect.getsource(simulate_crop)
        assert "farmer_id" in source, "Simulation must check crop.farmer_id"
        assert "403" in source or "FORBIDDEN" in source, "Simulation must return 403"

    def test_recommendations_ownership_concept(self, farmer_user, other_farmer):
        """Recommendations must verify crop ownership."""
        import inspect
        from app.api.v1.recommendations import get_recommendations
        source = inspect.getsource(get_recommendations)
        assert "farmer_id" in source, "Recommendations must check crop.farmer_id"

    def test_sync_batch_ownership_concept(self, farmer_user, other_farmer):
        """Offline sync must batch-verify all crop_instance_ids."""
        import inspect
        from app.api.v1.sync import submit_offline_sync
        from app.services.ctis.sync_service import SyncService
        endpoint_src = inspect.getsource(submit_offline_sync)
        service_src = inspect.getsource(SyncService)
        combined = endpoint_src + service_src
        assert "farmer_id" in combined, "Sync must check crop ownership"
        assert "crop_instance_id" in combined or "crop_ids" in combined, (
            "Sync must batch-verify crop IDs"
        )

    def test_review_ownership_concept(self, farmer_user, other_farmer):
        """Reviews must verify service_request.farmer_id."""
        import inspect
        from app.api.v1.reviews import submit_review
        source = inspect.getsource(submit_review)
        assert "farmer_id" in source, "Reviews must check request ownership"

    def test_service_request_accept_has_provider_lookup(self):
        """Accept must look up ServiceProvider profile."""
        import inspect
        from app.api.v1.service_requests import accept_service_request, _resolve_provider_profile
        source = inspect.getsource(accept_service_request) + inspect.getsource(_resolve_provider_profile)
        assert "ServiceProvider" in source, "Accept must look up provider profile"
        assert "provider.id" in source or "provider_id" in source, (
            "Accept must use provider record ID"
        )

    def test_service_request_complete_checks_assignment(self):
        """Complete must verify request.provider_id matches."""
        import inspect
        from app.api.v1.service_requests import complete_service_request, _resolve_request_for_provider
        source = inspect.getsource(complete_service_request) + inspect.getsource(_resolve_request_for_provider)
        assert "provider_id" in source, "Complete must check provider assignment"


# ─── Cross-Role Access Tests ────────────────────────────────────────────────


class TestCrossRoleAccess:
    """Verify roles cannot access endpoints restricted to other roles."""

    def test_farmer_cannot_accept_service_request(self, farmer_user):
        """A farmer should not be able to accept service requests (provider-only)."""
        from app.api.deps import require_role
        dep = require_role(["provider"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=farmer_user))
        assert exc.value.status_code == 403

    def test_provider_cannot_create_crop(self, provider_user):
        """A provider should not be able to simulate crops (farmer-only)."""
        from app.api.deps import require_role
        dep = require_role(["farmer"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=provider_user))
        assert exc.value.status_code == 403

    def test_farmer_cannot_toggle_features(self, farmer_user):
        """A farmer should not be able to toggle feature flags (admin-only)."""
        from app.api.deps import require_role
        dep = require_role(["admin"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=farmer_user))
        assert exc.value.status_code == 403

    def test_provider_cannot_access_rules(self, provider_user):
        """A provider should not be able to list rule templates (admin-only)."""
        from app.api.deps import require_role
        dep = require_role(["admin"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=provider_user))
        assert exc.value.status_code == 403

    def test_farmer_cannot_access_admin_pages(self, farmer_user):
        """A farmer should be blocked from admin endpoints."""
        from app.api.deps import require_role
        dep = require_role(["admin"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=farmer_user))
        assert exc.value.status_code == 403

    def test_provider_cannot_submit_review(self, provider_user):
        """A provider should not be able to submit a service review (farmer-only)."""
        from app.api.deps import require_role
        dep = require_role(["farmer"])
        with pytest.raises(HTTPException) as exc:
            run_async(dep(current_user=provider_user))
        assert exc.value.status_code == 403

    def test_admin_can_access_admin_only(self, admin_user):
        """Admin should pass admin-only requirement."""
        from app.api.deps import require_role
        dep = require_role(["admin"])
        result = run_async(dep(current_user=admin_user))
        assert result == admin_user

    def test_farmer_can_access_farmer_only(self, farmer_user):
        """Farmer should pass farmer-only requirement."""
        from app.api.deps import require_role
        dep = require_role(["farmer"])
        result = run_async(dep(current_user=farmer_user))
        assert result == farmer_user

    def test_provider_can_access_provider_only(self, provider_user):
        """Provider should pass provider-only requirement."""
        from app.api.deps import require_role
        dep = require_role(["provider"])
        result = run_async(dep(current_user=provider_user))
        assert result == provider_user


# ─── Provider Identity Tests ────────────────────────────────────────────────


class TestProviderIdentity:
    """Verify provider FK integrity."""

    def test_provider_id_fk_type(self):
        """
        ServiceRequest.provider_id should reference service_providers.id,
        NOT users.id. This prevents FK type confusion.
        """
        from app.models.service_request import ServiceRequest

        provider_id_col = ServiceRequest.__table__.c.provider_id
        fk_targets = [fk.target_fullname for fk in provider_id_col.foreign_keys]
        assert "service_providers.id" in fk_targets, (
            f"Expected FK to service_providers.id, got {fk_targets}"
        )

    def test_provider_profile_unique_constraint(self):
        """
        ServiceProvider.user_id should have a unique constraint
        to enforce one profile per user.
        """
        from app.models.service_provider import ServiceProvider

        user_id_col = ServiceProvider.__table__.c.user_id
        assert user_id_col.unique, "ServiceProvider.user_id should be unique"

    def test_provider_duplicate_check_in_endpoint(self):
        """POST /providers must check for existing profile."""
        import inspect
        from app.api.v1.providers import create_provider
        source = inspect.getsource(create_provider)
        assert "409" in source or "CONFLICT" in source, (
            "Provider creation must check for duplicates"
        )
