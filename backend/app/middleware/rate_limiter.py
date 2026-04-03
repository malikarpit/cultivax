"""
Rate Limiting Middleware

Per-role rate limiting using sliding window counters.
MSDD Section 8.12 — Abuse Prevention.

Limits (per minute, configurable in Settings):
  farmer:   60 req/min
  provider: 100 req/min
  admin:    200 req/min
  default:  30 req/min (unauthenticated)
"""

import time
import logging
import os
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Sliding window: key → (request_count, window_start_timestamp)
_rate_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

WINDOW_SECONDS = 60.0  # 1-minute sliding window


def _get_limit_for_role(role: str) -> int:
    """Get the rate limit for a given user role."""
    limits = {
        "farmer": settings.RATE_LIMIT_FARMER,
        "provider": settings.RATE_LIMIT_PROVIDER,
        "admin": settings.RATE_LIMIT_ADMIN,
    }
    return limits.get(role, settings.RATE_LIMIT_DEFAULT)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-role rate limiting middleware (MSDD 8.12).

    Extracts the user's role from the JWT token (if present) and applies
    role-specific request limits per sliding window.

    If no token is present, the client IP is used as the rate limiting key
    with the default (lowest) rate limit.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting in test environment
        if os.environ.get("TESTING") == "1":
            return await call_next(request)

        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Determine rate limiting key and limit
        key, limit = self._extract_key_and_limit(request)

        now = time.time()
        count, window_start = _rate_store[key]

        # Reset window if expired
        if now - window_start > WINDOW_SECONDS:
            count = 0
            window_start = now

        count += 1
        _rate_store[key] = (count, window_start)

        if count > limit:
            remaining_seconds = int(WINDOW_SECONDS - (now - window_start))
            logger.warning(
                f"Rate limit exceeded for key={key} "
                f"({count}/{limit} req/min)"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate Limit Exceeded",
                    "details": [{
                        "message": f"Too many requests. Limit: {limit}/min. Retry after {remaining_seconds}s."
                    }],
                },
                headers={"Retry-After": str(remaining_seconds)},
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))

        return response

    def _extract_key_and_limit(self, request: Request) -> tuple:
        """
        Extract the rate-limiting key and applicable limit.
        Uses JWT sub+role if authenticated, else client IP.
        """
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            try:
                from app.security.auth import verify_token

                token = auth_header.split(" ", 1)[1]
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub", "unknown")
                    role = payload.get("role", "farmer")
                    return f"user:{user_id}", _get_limit_for_role(role)
            except Exception:
                pass  # Fall through to IP-based limiting

        # Unauthenticated: use client IP
        client_ip = request.client.host if request.client else "0.0.0.0"
        return f"ip:{client_ip}", settings.RATE_LIMIT_DEFAULT
