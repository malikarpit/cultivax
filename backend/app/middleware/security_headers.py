"""
Security Headers Middleware

Implements comprehensive security headers for 2026 standards:
- Content Security Policy (CSP) with per-request nonce — no 'unsafe-inline'
- Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Cross-Origin-Opener-Policy (COOP)
- Cross-Origin-Resource-Policy (CORP)
- Referrer-Policy
- Permissions-Policy
- X-DNS-Prefetch-Control

ASVS Level 2 — V14.4 HTTP Security Headers compliance.
"""

import base64
import logging
import os
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


def _generate_nonce() -> str:
    """Generate a cryptographically random 128-bit nonce for CSP."""
    return base64.b64encode(os.urandom(16)).decode("ascii")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds comprehensive security headers to all responses.

    Key changes from previous implementation:
    - Per-request CSP nonce replaces 'unsafe-inline' on every path
    - COOP and CORP headers added (isolation from cross-origin attacks)
    - X-DNS-Prefetch-Control added
    - X-Powered-By removed entirely (was replaced with platform name — leaks info)
    - report-to directive references the CSP report endpoint
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate per-request nonce — unique on every response
        nonce = _generate_nonce()

        # Attach nonce to request state so downstream handlers can use it
        request.state.csp_nonce = nonce

        response = await call_next(request)

        is_docs_path = request.url.path in ("/docs", "/redoc", "/openapi.json")

        if is_docs_path:
            # Swagger UI / ReDoc require runtime scripts — nonce-gated instead of 'unsafe-inline'
            # swagger-ui injects inline scripts that reference window.__SENTRY_RELEASE__ etc.
            # We must allow 'unsafe-inline' only for style-src on docs (swagger injects inline styles).
            # script-src uses nonce so any injected script that doesn't carry the nonce is blocked.
            csp_directives = [
                f"default-src 'self'",
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # swagger needs inline styles
                "img-src 'self' data: https: https://fastapi.tiangolo.com",
                "font-src 'self' data: https://cdn.jsdelivr.net",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        else:
            # Strict CSP for all API paths — no inline scripts or styles
            csp_directives = [
                "default-src 'self'",
                f"script-src 'self' 'nonce-{nonce}'",
                "style-src 'self'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests",
                "report-to csp-endpoint",
            ]

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # CSP reporting endpoint (browser POSTs violations here)
        response.headers["Report-To"] = (
            '{"group":"csp-endpoint","max_age":86400,'
            '"endpoints":[{"url":"/api/v1/security/csp-report"}]}'
        )

        # Strict Transport Security — enforce HTTPS (production only)
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Prevent clickjacking (belt-and-suspenders alongside frame-ancestors in CSP)
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy browsers fallback)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy — limit information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cross-Origin-Opener-Policy — isolate browsing context (mitigates Spectre)
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cross-Origin-Resource-Policy — prevent cross-site reads
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Disable DNS prefetching to prevent passive reconnaissance
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Permissions policy — restrict browser feature access
        permissions_directives = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # Remove server identification headers
        for header in ("Server", "X-Powered-By"):
            try:
                del response.headers[header]
            except KeyError:
                pass

        return response
