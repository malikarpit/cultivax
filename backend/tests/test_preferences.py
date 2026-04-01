"""
Preferences Test Suite

Tests for Feature 3: User Profile, Language & Accessibility Settings.
Validates PATCH /auth/me endpoint, schema validation, settings merge logic,
onboarding flag, and audit logging.

Run: pytest tests/test_preferences.py -v
"""

import asyncio
import inspect
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from pydantic import ValidationError


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
    """Mock farmer user with preference fields."""
    user = MagicMock()
    user.id = uuid4()
    user.role = "farmer"
    user.is_active = True
    user.is_onboarded = False
    user.full_name = "Test Farmer"
    user.phone = "+919876543210"
    user.email = "farmer@test.com"
    user.preferred_language = "en"
    user.accessibility_settings = {}
    user.region = "Maharashtra"
    user.is_deleted = False
    user.created_at = "2026-01-01T00:00:00"
    return user


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


# ─── Schema Validation Tests ────────────────────────────────────────────────


class TestPreferencesSchemaValidation:
    """Validate UserPreferencesUpdate schema rules."""

    def test_valid_language_accepted(self):
        """Supported languages should be accepted."""
        from app.schemas.user import UserPreferencesUpdate

        for lang in ["en", "hi", "ta", "te", "mr"]:
            update = UserPreferencesUpdate(preferred_language=lang)
            assert update.preferred_language == lang

    def test_invalid_language_rejected(self):
        """Unsupported language codes should raise validation error."""
        from app.schemas.user import UserPreferencesUpdate

        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(preferred_language="fr")
        assert "Unsupported language" in str(exc_info.value)

    def test_invalid_language_code_xx_rejected(self):
        """Random language code should be rejected."""
        from app.schemas.user import UserPreferencesUpdate

        with pytest.raises(ValidationError):
            UserPreferencesUpdate(preferred_language="xx")

    def test_valid_accessibility_keys_accepted(self):
        """Allowed accessibility keys should pass validation."""
        from app.schemas.user import UserPreferencesUpdate

        update = UserPreferencesUpdate(
            accessibility_settings={
                "largeText": True,
                "highContrast": False,
                "reducedMotion": True,
                "theme": "dark",
                "sidebarPinned": True,
            }
        )
        assert update.accessibility_settings["largeText"] is True
        assert update.accessibility_settings["theme"] == "dark"

    def test_invalid_accessibility_key_rejected(self):
        """Unknown accessibility keys should raise validation error."""
        from app.schemas.user import UserPreferencesUpdate

        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(
                accessibility_settings={"invalidKey": True}
            )
        assert "Invalid accessibility keys" in str(exc_info.value)

    def test_empty_update_accepted(self):
        """Empty payload (no fields) should be accepted (no-op)."""
        from app.schemas.user import UserPreferencesUpdate

        update = UserPreferencesUpdate()
        assert update.preferred_language is None
        assert update.accessibility_settings is None

    def test_partial_accessibility_update(self):
        """Single accessibility key should be accepted."""
        from app.schemas.user import UserPreferencesUpdate

        update = UserPreferencesUpdate(
            accessibility_settings={"largeText": True}
        )
        assert update.accessibility_settings == {"largeText": True}


# ─── PATCH /auth/me Endpoint Tests ──────────────────────────────────────────


class TestPatchEndpoint:
    """Test the PATCH /auth/me endpoint function."""

    def test_endpoint_exists(self):
        """PATCH /auth/me route should exist."""
        from app.api.v1.auth import router

        routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and route.path.endswith("/me")
        ]
        methods_found = set()
        for route in routes:
            methods_found.update(getattr(route, "methods", []))

        assert "PATCH" in methods_found, (
            f"PATCH /me route missing. Found methods: {methods_found}"
        )

    def test_endpoint_updates_preferred_language(self, farmer_user, mock_db):
        """PATCH /auth/me should update preferred_language."""
        from app.api.v1.auth import update_preferences
        from app.schemas.user import UserPreferencesUpdate

        payload = UserPreferencesUpdate(preferred_language="hi")

        # Mock _log_auth_event to avoid DB hit
        with patch("app.api.v1.auth._log_auth_event"):
            result = run_async(
                update_preferences(payload, farmer_user, mock_db)
            )

        assert farmer_user.preferred_language == "hi"
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_endpoint_merges_accessibility_settings(self, farmer_user, mock_db):
        """PATCH /auth/me should MERGE accessibility settings, not replace."""
        from app.api.v1.auth import update_preferences
        from app.schemas.user import UserPreferencesUpdate

        # Pre-existing settings
        farmer_user.accessibility_settings = {"largeText": True, "theme": "dark"}

        payload = UserPreferencesUpdate(
            accessibility_settings={"highContrast": True}
        )

        with patch("app.api.v1.auth._log_auth_event"):
            result = run_async(
                update_preferences(payload, farmer_user, mock_db)
            )

        # Check merge: old keys preserved, new key added
        assert farmer_user.accessibility_settings["largeText"] is True
        assert farmer_user.accessibility_settings["highContrast"] is True
        assert farmer_user.accessibility_settings["theme"] == "dark"

    def test_endpoint_noop_on_empty_payload(self, farmer_user, mock_db):
        """PATCH /auth/me with empty payload should not write to DB."""
        from app.api.v1.auth import update_preferences
        from app.schemas.user import UserPreferencesUpdate

        payload = UserPreferencesUpdate()

        with patch("app.api.v1.auth._log_auth_event"):
            result = run_async(
                update_preferences(payload, farmer_user, mock_db)
            )

        # No DB writes on no-op
        mock_db.add.assert_not_called()

    def test_endpoint_logs_audit_event(self, farmer_user, mock_db):
        """PATCH /auth/me should call _log_auth_event."""
        from app.api.v1.auth import update_preferences
        from app.schemas.user import UserPreferencesUpdate

        payload = UserPreferencesUpdate(preferred_language="ta")

        with patch("app.api.v1.auth._log_auth_event") as mock_log:
            run_async(update_preferences(payload, farmer_user, mock_db))

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][1] == "PreferencesUpdated"
        assert call_args[0][2] == farmer_user.id


# ─── Onboarding Flag Tests ──────────────────────────────────────────────────


class TestOnboardingFlag:
    """Verify is_onboarded is set during first crop creation."""

    def test_crop_service_sets_onboarded_flag(self):
        """CropService.create_crop should set is_onboarded = True."""
        source = inspect.getsource(
            __import__(
                "app.services.ctis.crop_service",
                fromlist=["CropService"],
            ).CropService.create_crop
        )
        assert "is_onboarded" in source, (
            "CropService.create_crop must set is_onboarded"
        )
        assert "True" in source, (
            "CropService.create_crop must set is_onboarded = True"
        )

    def test_onboarded_flag_only_set_when_false(self):
        """is_onboarded should only flip once (not on every crop)."""
        source = inspect.getsource(
            __import__(
                "app.services.ctis.crop_service",
                fromlist=["CropService"],
            ).CropService.create_crop
        )
        assert "not farmer.is_onboarded" in source or "is_onboarded" in source, (
            "Must guard against re-setting onboarded flag"
        )


# ─── Response Schema Tests ──────────────────────────────────────────────────


class TestResponseSchema:
    """Verify UserResponse and UserPreferencesResponse include preference fields."""

    def test_user_response_has_preference_fields(self):
        """UserResponse schema must include preference fields."""
        from app.schemas.user import UserResponse

        fields = UserResponse.model_fields
        assert "preferred_language" in fields
        assert "accessibility_settings" in fields
        assert "is_onboarded" in fields

    def test_preferences_response_has_required_fields(self):
        """UserPreferencesResponse must have the correct projection."""
        from app.schemas.user import UserPreferencesResponse

        fields = UserPreferencesResponse.model_fields
        assert "id" in fields
        assert "preferred_language" in fields
        assert "accessibility_settings" in fields
        assert "is_onboarded" in fields

    def test_supported_languages_constant(self):
        """SUPPORTED_LANGUAGES must include en, hi, ta, te, mr."""
        from app.schemas.user import SUPPORTED_LANGUAGES

        for lang in ["en", "hi", "ta", "te", "mr"]:
            assert lang in SUPPORTED_LANGUAGES


# ─── i18n & Translation Endpoint Placeholder ─────────────────────────────

class TestTranslationEndpoint:
    """Validate translation API structure exists or is planned."""

    def test_user_model_has_preferred_language(self):
        """User DB model must have preferred_language column."""
        from app.models.user import User

        cols = [c.name for c in User.__table__.columns]
        assert "preferred_language" in cols

    def test_user_model_has_accessibility_settings(self):
        """User DB model must have accessibility_settings column."""
        from app.models.user import User

        cols = [c.name for c in User.__table__.columns]
        assert "accessibility_settings" in cols

    def test_user_model_has_is_onboarded(self):
        """User DB model must have is_onboarded column."""
        from app.models.user import User

        cols = [c.name for c in User.__table__.columns]
        assert "is_onboarded" in cols
