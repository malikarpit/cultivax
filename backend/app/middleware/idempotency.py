"""
Idempotency Middleware

Checks for Idempotency-Key header on mutating requests (POST/PUT/PATCH).
Rejects duplicate requests that have already been processed.
MSDD Section 8.13.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# In-memory store for development. In production, use Redis or DB.
_idempotency_store: dict = {}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Deduplicates mutating requests using Idempotency-Key header.
    
    If a POST/PUT/PATCH request includes an Idempotency-Key header:
    - First request: processes normally and stores the key
    - Duplicate request: returns 409 Conflict
    
    Non-mutating methods (GET, DELETE, OPTIONS) are passed through.
    """

    async def dispatch(self, request: Request, call_next):
        # Only check mutating methods
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            # No key provided — process normally
            return await call_next(request)

        # Check if already processed
        if idempotency_key in _idempotency_store:
            logger.info(f"Duplicate request detected: Idempotency-Key={idempotency_key}")
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "error": "Duplicate Request",
                    "details": [{
                        "message": f"Request with Idempotency-Key '{idempotency_key}' has already been processed"
                    }],
                },
            )

        # Process request and store key
        response = await call_next(request)

        # Only store if request was successful (2xx)
        if 200 <= response.status_code < 300:
            _idempotency_store[idempotency_key] = True
            logger.debug(f"Stored Idempotency-Key: {idempotency_key}")

        return response
