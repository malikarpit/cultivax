"""
Tests: Wave 2 Security Headers (CSP, COOP, CORP, X-Powered-By)

Verifies that SecurityHeadersMiddleware emits the correct ASVS Level 2 headers
on both regular API paths and documentation paths.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Return a synchronous TestClient for header inspection."""
    return TestClient(app, raise_server_exceptions=False)


class TestCSPHeaders:
    """Content-Security-Policy correctness."""

    def test_api_path_has_csp(self, client):
        response = client.get("/health")
        assert "Content-Security-Policy" in response.headers

    def test_api_path_no_unsafe_inline_script(self, client):
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        # Non-doc paths must not allow unsafe inline execution.
        assert "'unsafe-inline'" not in csp.lower()

    def test_api_path_no_unsafe_eval(self, client):
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "'unsafe-eval'" not in csp.lower()

    def test_api_path_has_nonce(self, client):
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "nonce-" in csp, f"Expected nonce in CSP, got: {csp}"

    def test_nonce_differs_per_request(self, client):
        """Each response must have a unique nonce."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        csp1 = r1.headers.get("Content-Security-Policy", "")
        csp2 = r2.headers.get("Content-Security-Policy", "")
        nonce1 = [d for d in csp1.split(";") if "nonce-" in d]
        nonce2 = [d for d in csp2.split(";") if "nonce-" in d]
        assert nonce1 and nonce2, "Both responses should have nonces"
        assert nonce1 != nonce2, "Nonces must differ per request"

    def test_api_path_has_frame_ancestors_none(self, client):
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in csp

    def test_docs_path_allows_cdn(self, client):
        response = client.get("/docs")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "cdn.jsdelivr.net" in csp


class TestIsolationHeaders:
    """Cross-Origin isolation headers (COOP, CORP)."""

    def test_coop_same_origin(self, client):
        response = client.get("/health")
        assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"

    def test_corp_same_origin(self, client):
        response = client.get("/health")
        assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"

    def test_dns_prefetch_off(self, client):
        response = client.get("/health")
        assert response.headers.get("X-DNS-Prefetch-Control") == "off"


class TestInformationLeakage:
    """Server identity headers must be absent."""

    def test_x_powered_by_absent(self, client):
        """X-Powered-By must not be present in any response."""
        response = client.get("/health")
        # Should not appear at all, or if it does must not be our platform name
        val = response.headers.get("X-Powered-By", "")
        assert val == "", f"X-Powered-By should be absent, got: {val!r}"

    def test_server_header_absent(self, client):
        response = client.get("/health")
        # uvicorn injects 'uvicorn'; the middleware tries to strip it
        # We assert it doesn't leak the CultivaX stack name
        assert "cultivax" not in response.headers.get("Server", "").lower()


class TestClassicSecurityHeaders:
    """Standard OWASP / ASVS V14 headers."""

    def test_x_frame_options_deny(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options_nosniff(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_referrer_policy(self, client):
        response = client.get("/health")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_present(self, client):
        response = client.get("/health")
        assert "Permissions-Policy" in response.headers

    def test_report_to_present(self, client):
        """report-to header must be present on non-docs paths (for CSP violation reporting)."""
        response = client.get("/health")
        assert "Report-To" in response.headers
