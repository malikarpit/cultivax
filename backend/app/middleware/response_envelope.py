import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """
    Wraps API responses in a universal { success, data, meta } envelope.
    Skips docs, redoc, openapi.json, and internal health checks if appropriately needed.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Skip wrapping for docs, direct files, or non-JSON responses
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return response

        # Don't wrap if not application/json
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        # We need to extract the response body to wrap it
        body_iterator = response.body_iterator

        body_bytes = b""
        async for chunk in body_iterator:
            if isinstance(chunk, bytes):
                body_bytes += chunk
            elif isinstance(chunk, str):
                body_bytes += chunk.encode("utf-8")

        try:
            original_data = json.loads(body_bytes.decode("utf-8"))

            # If already enveloped or it's an error detail, skip enveloping
            if isinstance(original_data, dict) and (
                "detail" in original_data or "success" in original_data
            ):
                wrapped_body = body_bytes
            else:
                success = 200 <= response.status_code < 400
                enveloped_data = {
                    "success": success,
                    "data": original_data,
                    "meta": {"path": request.url.path},
                }
                wrapped_body = json.dumps(enveloped_data).encode("utf-8")

            # Create new response
            new_response = Response(
                content=wrapped_body,
                status_code=response.status_code,
                media_type="application/json",
            )

            # Reconstruct raw_headers explicitly to preserve multiple set-cookie headers
            new_raw_headers = []
            for k, v in response.raw_headers:
                if k.lower() == b"content-length":
                    new_raw_headers.append(
                        (b"content-length", str(len(wrapped_body)).encode("latin-1"))
                    )
                else:
                    new_raw_headers.append((k, v))
            new_response.raw_headers = new_raw_headers

            return new_response
        except Exception:
            # On parsing failure, return as is
            fallback_res = Response(
                content=body_bytes,
                status_code=response.status_code,
                media_type=content_type,
            )
            fallback_res.raw_headers = response.raw_headers
            return fallback_res
