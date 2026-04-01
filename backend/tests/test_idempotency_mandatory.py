"""
Tests: Wave 2 Idempotency — Mandatory Enforcement + Format Validation

Tests the middleware logic in isolation using direct mock request objects,
since the full HTTP test stack sets TESTING=1 which disables the middleware
for all other tests.
"""

import pytest
import uuid
import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

# Import the pattern and helpers directly for unit testing
from app.middleware.idempotency import _VALID_KEY_PATTERN, _IDEMPOTENCY_EXEMPT_PATHS, DistributedIdempotencyMiddleware


class TestIdempotencyKeyPattern:
    """Unit tests for the Idempotency-Key format regex."""

    def test_valid_uuid4_accepted(self):
        key = str(uuid.uuid4())
        assert _VALID_KEY_PATTERN.match(key), f"UUID4 {key!r} should match"

    def test_valid_uuid4_uppercase_accepted(self):
        key = str(uuid.uuid4()).upper()
        assert _VALID_KEY_PATTERN.match(key)

    def test_valid_32_hex_accepted(self):
        key = uuid.uuid4().hex  # 32-char lowercase hex
        assert _VALID_KEY_PATTERN.match(key)

    def test_valid_64_hex_accepted(self):
        key = uuid.uuid4().hex + uuid.uuid4().hex  # 64-char hex
        assert _VALID_KEY_PATTERN.match(key)

    def test_invalid_short_key_rejected(self):
        assert not _VALID_KEY_PATTERN.match("abc123")

    def test_invalid_special_chars_rejected(self):
        assert not _VALID_KEY_PATTERN.match("not-a-valid-key!!!")

    def test_invalid_non_hex_rejected(self):
        assert not _VALID_KEY_PATTERN.match("gggggggggggggggggggggggggggggggg")

    def test_invalid_too_long_rejected(self):
        # 65+ chars — above the 64 limit
        key = "a" * 65
        assert not _VALID_KEY_PATTERN.match(key)

    def test_uuid_wrong_version_rejected(self):
        # UUID1 — version digit should be 4
        import uuid as _uuid
        uuid1_key = str(_uuid.uuid1())
        # UUID1 has version '1', pattern requires '4' — should fail
        assert not _VALID_KEY_PATTERN.match(uuid1_key)

    def test_empty_string_rejected(self):
        assert not _VALID_KEY_PATTERN.match("")


class TestIdempotencyExemptPaths:
    """Verify the exemption list is correct."""

    def test_whatsapp_webhook_is_exempt(self):
        assert "/api/v1/whatsapp/webhook" in _IDEMPOTENCY_EXEMPT_PATHS

    def test_csp_report_is_exempt(self):
        assert "/api/v1/security/csp-report" in _IDEMPOTENCY_EXEMPT_PATHS

    def test_auth_login_is_exempt(self):
        assert "/api/v1/auth/login" in _IDEMPOTENCY_EXEMPT_PATHS

    def test_service_requests_not_exempt(self):
        assert "/api/v1/service-requests" not in _IDEMPOTENCY_EXEMPT_PATHS

    def test_reviews_not_exempt(self):
        assert "/api/v1/reviews" not in _IDEMPOTENCY_EXEMPT_PATHS


class TestIdempotencyRequiredPaths:
    """Verify _is_required_path logic."""

    def test_service_requests_is_required(self):
        from unittest.mock import MagicMock
        app_mock = MagicMock()
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.redis_client = None
        middleware._memory_store = {}
        assert middleware._is_required_path("/api/v1/service-requests")

    def test_reviews_is_required(self):
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.redis_client = None
        middleware._memory_store = {}
        assert middleware._is_required_path("/api/v1/reviews")

    def test_whatsapp_webhook_is_not_required(self):
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.redis_client = None
        middleware._memory_store = {}
        assert not middleware._is_required_path("/api/v1/whatsapp/webhook")

    def test_auth_login_is_not_required(self):
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.redis_client = None
        middleware._memory_store = {}
        assert not middleware._is_required_path("/api/v1/auth/login")

    def test_health_is_not_required(self):
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.redis_client = None
        middleware._memory_store = {}
        assert not middleware._is_required_path("/health")


@pytest.mark.asyncio
class TestIdempotencyDispatch:
    """Integration-level middleware dispatch tests using mock ASGI."""

    def _make_middleware(self):
        app_mock = MagicMock()
        middleware = DistributedIdempotencyMiddleware.__new__(DistributedIdempotencyMiddleware)
        middleware.app = app_mock
        middleware.redis_client = None
        middleware._memory_store = {}
        return middleware

    def _make_request(self, method="POST", path="/api/v1/service-requests", headers=None):
        request = MagicMock()
        request.method = method
        request.url.path = path
        request.headers = headers or {}
        request.state = MagicMock()
        request.state.request_id = "test-req-id"
        return request

    async def test_missing_key_on_required_path_returns_422(self):
        middleware = self._make_middleware()
        request = self._make_request(headers={})

        call_next = AsyncMock()
        import os
        with patch.dict(os.environ, {"TESTING": ""}):
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 422
        body = json.loads(response.body)
        assert "Idempotency-Key" in str(body)
        call_next.assert_not_called()

    async def test_invalid_key_format_returns_422(self):
        middleware = self._make_middleware()
        request = self._make_request(headers={"Idempotency-Key": "bad-key!!!"})

        call_next = AsyncMock()
        import os
        with patch.dict(os.environ, {"TESTING": ""}):
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 422
        body = json.loads(response.body)
        assert "format" in str(body).lower() or "Idempotency-Key" in str(body)
        call_next.assert_not_called()

    async def test_valid_uuid4_key_proceeds_to_handler(self):
        middleware = self._make_middleware()
        request = self._make_request(headers={"Idempotency-Key": str(uuid.uuid4())})

        mock_response = MagicMock()
        mock_response.status_code = 201

        async def fake_body_iter():
            yield b'{"success": true}'

        mock_response.body_iterator = fake_body_iter()
        mock_response.media_type = "application/json"
        call_next = AsyncMock(return_value=mock_response)

        import os
        with patch.dict(os.environ, {"TESTING": ""}):
            response = await middleware.dispatch(request, call_next)

        call_next.assert_called_once()

    async def test_exempt_path_no_key_passes_through(self):
        """WhatsApp webhook path passes through even with no key."""
        middleware = self._make_middleware()
        request = self._make_request(method="POST", path="/api/v1/whatsapp/webhook", headers={})

        call_next = AsyncMock()
        import os
        with patch.dict(os.environ, {"TESTING": ""}):
            response = await middleware.dispatch(request, call_next)

        call_next.assert_called_once()
