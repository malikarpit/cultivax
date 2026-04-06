"""
Distributed Idempotency Middleware

Checks for Idempotency-Key header on mutating requests.
Uses Redis (with in-memory fallback) to deduplicate requests cluster-wide.
Caches and reuses the original response payload up to a TTL expiry.

Additions:
- Idempotency-Key format validation (UUID4 or 32-64 hex chars)
- Mandatory enforcement on configurable high-stakes paths (FX-0010)
- Idempotency-Replay: true response header on cache hits
- Security event logging for format violations
"""

import json
import logging
import re
import time
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL = 3600 * 24  # 24 hours

# Valid Idempotency-Key formats:
# - UUID4: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
# - 32-64 hex chars (no dashes)
_VALID_KEY_PATTERN = re.compile(
    r"^(?:"
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"  # UUID4
    r"|"
    r"[0-9a-f]{32,64}"  # 32-64 lowercase hex
    r")$",
    re.IGNORECASE,
)

# Paths exempted from mandatory enforcement even if they're POST/PUT/PATCH
# (Meta sends WhatsApp webhooks without Idempotency-Key)
_IDEMPOTENCY_EXEMPT_PATHS = frozenset(
    {
        "/api/v1/whatsapp/webhook",
        "/api/v1/security/csp-report",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/request-otp",
        "/api/v1/auth/verify-otp",
        "/api/v1/auth/refresh",
    }
)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class DistributedIdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
        self._memory_store = {}

        if REDIS_AVAILABLE:
            redis_url = getattr(settings, "REDIS_URL", None)
            if redis_url:
                try:
                    self.redis_client = redis.from_url(
                        redis_url, encoding="utf-8", decode_responses=True
                    )
                    logger.info("Distributed idempotency initialized with Redis")
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis for idempotency: {e}")

    async def _get_cache(self, key: str) -> Optional[dict]:
        if self.redis_client:
            try:
                data = await self.redis_client.get(f"idem:{key}")
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return None
        else:
            entry = self._memory_store.get(key)
            if entry and entry["expires"] > time.time():
                return entry["data"]
            return None

    async def _set_cache(self, key: str, data: dict):
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"idem:{key}",
                    IDEMPOTENCY_TTL,
                    json.dumps(data),
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            self._memory_store[key] = {
                "expires": time.time() + IDEMPOTENCY_TTL,
                "data": data,
            }

    async def _delete_cache(self, key: str):
        if self.redis_client:
            try:
                await self.redis_client.delete(f"idem:{key}")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        elif key in self._memory_store:
            del self._memory_store[key]

    def _is_required_path(self, path: str) -> bool:
        """Check if this path requires a mandatory Idempotency-Key."""
        if path in _IDEMPOTENCY_EXEMPT_PATHS:
            return False
        for required_prefix in settings.idempotency_required_paths:
            if path.startswith(required_prefix.split("{")[0]):  # strip path params
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        # Only mutating methods are candidates
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        import os

        if os.environ.get("TESTING") == "1":
            return await call_next(request)

        path = request.url.path
        idempotency_key = request.headers.get("Idempotency-Key")

        # --- 2.6: Mandatory enforcement ---
        if idempotency_key is None and self._is_required_path(path):
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"Missing Idempotency-Key on required path {path}",
                extra={"request_id": request_id, "path": path},
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "error": "Missing Idempotency-Key",
                    "details": [
                        {
                            "message": (
                                f"The Idempotency-Key header is required for {request.method} {path}. "
                                "Generate a UUID4 and include it as 'Idempotency-Key: <uuid4>'. "
                                "Reuse the same key to safely retry without duplicate side-effects."
                            )
                        }
                    ],
                    "request_id": request_id,
                },
            )

        # If no key provided on optional paths, proceed normally
        if not idempotency_key:
            return await call_next(request)

        # --- 2.5a: Format validation ---
        if not _VALID_KEY_PATTERN.match(idempotency_key):
            from app.security.events import log_security_event

            request_id = getattr(request.state, "request_id", "unknown")
            log_security_event(
                "INVALID_IDEMPOTENCY_KEY",
                f"key={idempotency_key[:64]!r} does not match UUID4 or 32-64 hex pattern",
                request_id,
                path,
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "error": "Invalid Idempotency-Key Format",
                    "details": [
                        {
                            "message": (
                                "Idempotency-Key must be a UUID4 "
                                "(e.g. 550e8400-e29b-41d4-a716-446655440000) "
                                "or a 32-64 character lowercase hex string."
                            )
                        }
                    ],
                    "request_id": request_id,
                },
            )

        # --- Cache lookup ---
        cached = await self._get_cache(idempotency_key)
        if cached:
            if cached.get("status") == "processing":
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "success": False,
                        "error": "Concurrent Request Processing",
                    },
                )

            logger.info(f"Idempotency cache hit for {idempotency_key}")
            # 2.5b: Add replay indicator header
            return Response(
                content=cached.get("body", "").encode("utf-8"),
                status_code=cached.get("status_code", 200),
                media_type=cached.get("media_type", "application/json"),
                headers={"Idempotency-Replay": "true"},
            )

        # Mark as processing (prevents concurrent duplicate requests)
        await self._set_cache(idempotency_key, {"status": "processing"})

        try:
            response = await call_next(request)

            if 200 <= response.status_code < 300:
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk

                async def _stream():
                    yield body_bytes

                response.body_iterator = _stream()

                try:
                    body_str = body_bytes.decode("utf-8")
                    await self._set_cache(
                        idempotency_key,
                        {
                            "status": "completed",
                            "status_code": response.status_code,
                            "media_type": response.media_type,
                            "body": body_str,
                        },
                    )
                except UnicodeDecodeError:
                    # Don't cache binary responses
                    await self._delete_cache(idempotency_key)
            else:
                await self._delete_cache(idempotency_key)

            return response

        except Exception:
            await self._delete_cache(idempotency_key)
            raise
