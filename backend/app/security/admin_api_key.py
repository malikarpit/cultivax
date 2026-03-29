"""
Admin API Key Authentication

Request signing and API key authentication for admin endpoints.
Provides enhanced security with rotating API keys and request signatures.
"""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


class AdminAPIKey:
    """
    Admin API Key with rotation support.

    API keys are signed using HMAC-SHA256 for integrity verification.
    """

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate a new API key and its hash.

        Returns:
            (api_key, api_key_hash) - Store only the hash in database
        """
        # Generate 32-byte random key
        api_key = f"cultivax_admin_{secrets.token_urlsafe(32)}"

        # Hash for storage
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        return api_key, api_key_hash

    @staticmethod
    def verify_api_key(api_key: str, api_key_hash: str) -> bool:
        """
        Verify an API key against its hash.

        Args:
            api_key: API key to verify
            api_key_hash: Stored hash

        Returns:
            True if valid
        """
        computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return hmac.compare_digest(computed_hash, api_key_hash)

    @staticmethod
    def sign_request(
        method: str,
        path: str,
        body: str,
        timestamp: int,
        api_secret: str,
    ) -> str:
        """
        Generate HMAC signature for a request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (empty string for GET)
            timestamp: Unix timestamp
            api_secret: Secret key for signing

        Returns:
            HMAC-SHA256 signature (hex)
        """
        # Construct message to sign
        message = f"{method}\n{path}\n{body}\n{timestamp}"

        # Generate HMAC signature
        signature = hmac.new(
            api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    @staticmethod
    def verify_request_signature(
        request: Request,
        body: str,
        signature: str,
        timestamp: int,
        api_secret: str,
        max_age_seconds: int = 300,  # 5 minutes
    ) -> Tuple[bool, str]:
        """
        Verify request signature.

        Args:
            request: FastAPI request
            body: Request body
            signature: Provided signature
            timestamp: Request timestamp
            api_secret: Secret key for verification
            max_age_seconds: Maximum request age

        Returns:
            (is_valid, error_message)
        """
        # Check timestamp freshness (prevent replay attacks)
        current_time = int(time.time())
        age = current_time - timestamp

        if age > max_age_seconds:
            return False, f"Request too old: {age}s (max: {max_age_seconds}s)"

        if age < -60:  # Allow 1 minute clock skew
            return False, "Request timestamp is in the future"

        # Compute expected signature
        expected_signature = AdminAPIKey.sign_request(
            method=request.method,
            path=str(request.url.path),
            body=body,
            timestamp=timestamp,
            api_secret=api_secret,
        )

        # Constant-time comparison
        if not hmac.compare_digest(signature, expected_signature):
            return False, "Invalid signature"

        return True, ""


async def require_admin_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[int] = Header(None),
) -> bool:
    """
    Dependency to require admin API key authentication.

    Supports two modes:
    1. Simple API key (for basic admin endpoints)
    2. Signed requests (for critical admin operations)

    Args:
        request: FastAPI request
        x_api_key: API key header
        x_signature: Request signature header (optional)
        x_timestamp: Request timestamp header (required with signature)

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    # Check for API key
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key format
    if not x_api_key.startswith("cultivax_admin_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    # TODO: Verify against database
    # For now, use a simple check (in production, store hashed keys in database)
    # This is a placeholder - implement proper DB lookup
    configured_key = getattr(settings, "ADMIN_API_KEY", None)
    if not configured_key:
        logger.warning("ADMIN_API_KEY not configured - admin endpoints unprotected!")
        # In development, allow without key if not configured
        if settings.APP_ENV != "production":
            return True
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key not configured",
        )

    # Simple comparison (should use hash comparison in production)
    if not hmac.compare_digest(x_api_key, configured_key):
        logger.warning(f"Invalid API key attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # If signature provided, verify it
    if x_signature:
        if not x_timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Timestamp required with X-Signature",
            )

        # Get request body
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""

        is_valid, error = AdminAPIKey.verify_request_signature(
            request=request,
            body=body_str,
            signature=x_signature,
            timestamp=x_timestamp,
            api_secret=settings.SECRET_KEY,
        )

        if not is_valid:
            logger.warning(
                f"Invalid request signature from {request.client.host}: {error}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid request signature: {error}",
            )

        logger.info(f"Authenticated admin request with signature from {request.client.host}")

    return True
