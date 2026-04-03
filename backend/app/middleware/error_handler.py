"""
Global Error Handler Middleware

Catches all unhandled exceptions and returns structured JSON responses.
Critically: converts HTTPExceptions to JSON responses instead of re-raising,
which would break the BaseHTTPMiddleware call_next stream.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns structured error responses."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except (StarletteHTTPException, FastAPIHTTPException) as e:
            # Convert HTTP exceptions to JSON response — do NOT re-raise,
            # as that breaks the BaseHTTPMiddleware response stream.
            request_id = getattr(request.state, "request_id", "unknown")
            detail = e.detail if isinstance(e.detail, str) else str(e.detail)
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": detail,
                    "details": [{"message": detail}],
                    "request_id": request_id
                },
            )
        except ValueError as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "error": "Validation Error",
                    "details": [{"message": str(e)}],
                    "request_id": request_id
                },
            )
        except PermissionError as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(f"Permission denied: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "error": "Forbidden",
                    "details": [{"message": str(e)}],
                    "request_id": request_id
                },
            )
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"Unhandled error: {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "Internal Server Error",
                    "details": [{"message": "An unexpected error occurred"}],
                    "request_id": request_id
                },
            )

