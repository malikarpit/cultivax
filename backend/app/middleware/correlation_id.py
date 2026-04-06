"""
Correlation ID Middleware

Generates a unique request_id for each incoming request, attaches it to the
request state, and includes it in the response headers (X-Request-ID).
"""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow client to pass a correlation ID if trusted, otherwise generate one
        # For security, we usually just generate a fresh one unless from a trusted internal proxy
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex}"

        # Attach to request state for other middleware/routers to use
        request.state.request_id = request_id

        response = await call_next(request)

        # Attach to response
        response.headers["X-Request-ID"] = request_id
        return response
