"""
Request Logging Middleware

Logs method, path, duration, status, request_id, and safe user identity.
Redacts secrets such as authorization headers or tokens.
"""

import logging
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def _extract_identity(self, request: Request) -> str:
        """
        Extract basic user identity safely (without mutating state)
        for logging purposes.
        """
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Lightweight extraction, without full verification
                # to not block log creation or duplicate auth effort unnecessarily,
                # though usually middleware has access to token.
                # For safety, we just log "authenticated".
                # If we need exact user_id, we can parse JWT without verification
                # or wait until route handling. Since this is middleware, we'll try to extract.
                import jwt

                token = auth_header.split(" ", 1)[1]
                unverified = jwt.decode(token, options={"verify_signature": False})
                return f"user:{unverified.get('sub', 'unknown')}"
            except Exception:
                pass

        # Try cookie parsing? No, let's keep it simple.
        client_ip = request.client.host if request.client else "0.0.0.0"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next):
        # Skip noisy endpoints
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        identity = self._extract_identity(request)

        # Log request start (optional, can be noisy, but good for debugging)
        logger.debug(
            f"Request started: id={request_id} method={request.method} path={request.url.path} by={identity}"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: id={request_id} method={request.method} "
                f"path={request.url.path} status={response.status_code} "
                f"duration={duration_ms:.2f}ms by={identity}"
            )
            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: id={request_id} method={request.method} "
                f"path={request.url.path} error={type(exc).__name__} "
                f"duration={duration_ms:.2f}ms by={identity}",
                exc_info=True,
            )
            raise
