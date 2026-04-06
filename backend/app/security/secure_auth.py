"""
Secure Authentication with HTTPOnly Cookies

Enhanced authentication system using HTTPOnly cookies instead of localStorage
to prevent XSS token theft. Implements 2026 security best practices.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from jose import JWTError

from app.config import settings
from app.security.auth import (create_access_token, create_refresh_token,
                               verify_token)

# Cookie names
ACCESS_TOKEN_COOKIE = "cultivax_access_token"
REFRESH_TOKEN_COOKIE = "cultivax_refresh_token"


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """
    Set HTTPOnly authentication cookies.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    is_production = settings.APP_ENV == "production"

    # Access token cookie (short-lived, 1 hour)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=is_production,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Refresh token cookie (long-lived, 7 days)
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth/refresh",  # Only sent to refresh endpoint
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear authentication cookies on logout.

    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/v1/auth/refresh")


def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extract access token from HTTPOnly cookie.

    Args:
        request: FastAPI Request object

    Returns:
        Access token string or None if not present
    """
    return request.cookies.get(ACCESS_TOKEN_COOKIE)


def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extract refresh token from HTTPOnly cookie.

    Args:
        request: FastAPI Request object

    Returns:
        Refresh token string or None if not present
    """
    return request.cookies.get(REFRESH_TOKEN_COOKIE)


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract token from request - supports both cookie and header auth.

    Priority:
    1. HTTPOnly cookie (preferred)
    2. Authorization header (backward compatibility)

    Args:
        request: FastAPI Request object

    Returns:
        Token string or None
    """
    # Try cookie first (more secure)
    token = get_token_from_cookie(request)
    if token:
        return token

    # Fall back to Authorization header for backward compatibility
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    return None
