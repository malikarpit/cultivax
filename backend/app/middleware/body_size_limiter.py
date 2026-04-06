"""
Body Size Limiter Middleware

Enforces a maximum request body size limit to prevent resource exhaustion/DoS.
Rejects oversized payloads with 413 Payload Too Large.

Implementation: Pure ASGI middleware (not BaseHTTPMiddleware) to avoid
corrupting the request stream in a stacked middleware chain.
"""

import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class BodySizeLimiterMiddleware:
    """
    Pure ASGI middleware that enforces request body size limits.

    Checks Content-Length header for fast rejection. For chunked/streaming
    requests, wraps the receive channel to count bytes without consuming them.
    """

    def __init__(self, app: ASGIApp, max_upload_size: int = 5 * 1024 * 1024):
        self.app = app
        self.max_upload_size = max_upload_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        if method not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        # Check Content-Length header for fast rejection
        headers = dict(
            (k.lower(), v)
            for k, v in (
                (h[0].decode("latin-1"), h[1].decode("latin-1"))
                for h in scope.get("headers", [])
            )
        )
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_upload_size:
                    logger.warning(
                        f"Payload too large: Content-Length {content_length} > {self.max_upload_size}"
                    )
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": "Payload Too Large",
                            "details": [
                                {
                                    "message": f"Request body exceeds {self.max_upload_size // (1024*1024)}MB limit."
                                }
                            ],
                        },
                    )
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass

        # Wrap receive to count bytes for chunked/streaming requests
        received_bytes = 0

        async def counting_receive():
            nonlocal received_bytes
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"")
                received_bytes += len(body)
                if received_bytes > self.max_upload_size:
                    raise ValueError(
                        f"Request body exceeds {self.max_upload_size // (1024*1024)}MB limit."
                    )
            return message

        try:
            await self.app(scope, counting_receive, send)
        except ValueError as e:
            if "Request body exceeds" in str(e):
                logger.warning(f"Chunked payload too large: {received_bytes} bytes")
                response = JSONResponse(
                    status_code=413,
                    content={
                        "success": False,
                        "error": "Payload Too Large",
                        "details": [{"message": str(e)}],
                    },
                )
                await response(scope, receive, send)
            else:
                raise
