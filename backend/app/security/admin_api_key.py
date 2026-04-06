"""
Admin API Key Authentication

Request signing and API key authentication for admin endpoints.
Provides enhanced security with rotating API keys and request signatures.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import Header, HTTPException, Request, status

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
            api_secret.encode(), message.encode(), hashlib.sha256
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


@dataclass(frozen=True)
class _KeyRecord:
    key_id: str
    sha256_hash: str
    source: str


def _normalize_iso_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_valid_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def _parse_key_hash(raw_hash: str) -> str:
    candidate = (raw_hash or "").strip().lower()
    if candidate.startswith("sha256:"):
        candidate = candidate[len("sha256:") :]
    return candidate


def _build_keyring_from_json(raw_json: str) -> List[_KeyRecord]:
    """
    Parse ADMIN_API_KEYS_JSON and return active keys in their validity window.
    """
    now = datetime.now(timezone.utc)
    try:
        parsed = json.loads(raw_json)
    except Exception as exc:
        raise ValueError(f"ADMIN_API_KEYS_JSON is invalid JSON: {exc}") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("keys", [])
    if not isinstance(parsed, list):
        raise ValueError(
            "ADMIN_API_KEYS_JSON must be an array or object with `keys` array"
        )

    keyring: List[_KeyRecord] = []
    for idx, item in enumerate(parsed):
        if not isinstance(item, dict):
            logger.warning("Skipping non-object admin key entry at index %s", idx)
            continue

        active = bool(item.get("active", True))
        if not active:
            continue

        not_before = _normalize_iso_datetime(item.get("not_before"))
        not_after = _normalize_iso_datetime(item.get("not_after"))
        if not_before and now < not_before:
            continue
        if not_after and now > not_after:
            continue

        key_id = str(item.get("key_id") or item.get("id") or f"key-{idx+1}")
        key_hash = _parse_key_hash(str(item.get("sha256") or item.get("hash") or ""))
        if not _is_valid_sha256_hex(key_hash):
            logger.warning(
                "Skipping admin key '%s' due invalid SHA-256 hash format", key_id
            )
            continue

        keyring.append(
            _KeyRecord(key_id=key_id, sha256_hash=key_hash, source="keyring")
        )

    return keyring


def _resolve_active_admin_keys() -> List[_KeyRecord]:
    """
    Resolve configured admin keys from keyring JSON or single-key fallback.
    """
    raw_ring = (getattr(settings, "ADMIN_API_KEYS_JSON", "") or "").strip()
    if raw_ring:
        return _build_keyring_from_json(raw_ring)

    configured_key = (getattr(settings, "ADMIN_API_KEY", None) or "").strip()
    if not configured_key:
        return []

    parsed_hash = _parse_key_hash(configured_key)
    if configured_key.startswith("sha256:"):
        if not _is_valid_sha256_hex(parsed_hash):
            raise ValueError(
                "ADMIN_API_KEY hash is malformed; expected sha256:<64-hex>"
            )
        return [
            _KeyRecord(
                key_id="legacy-single", sha256_hash=parsed_hash, source="single-hash"
            )
        ]

    # Fail closed for plaintext key in production.
    if settings.APP_ENV == "production":
        raise ValueError(
            "Plaintext ADMIN_API_KEY is forbidden in production. "
            "Use sha256:<hash> or ADMIN_API_KEYS_JSON."
        )

    # Compatibility fallback for local/dev only.
    logger.warning(
        "Using plaintext ADMIN_API_KEY fallback in non-production. "
        "Prefer sha256:<hash> or ADMIN_API_KEYS_JSON."
    )
    fallback_hash = hashlib.sha256(configured_key.encode()).hexdigest()
    return [
        _KeyRecord(
            key_id="legacy-plaintext-dev",
            sha256_hash=fallback_hash,
            source="single-plaintext",
        )
    ]


async def require_admin_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_api_key_id: Optional[str] = Header(None, alias="X-API-Key-Id"),
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
    # When called directly in tests, FastAPI Header defaults may pass HeaderInfo objects.
    if not isinstance(x_api_key, str):
        x_api_key = None
    if not isinstance(x_api_key_id, str):
        x_api_key_id = None
    if not isinstance(x_signature, str):
        x_signature = None

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

    # Resolve active keyring from config (fail-closed on invalid/missing config).
    try:
        keyring = _resolve_active_admin_keys()
    except ValueError as exc:
        logger.error("Admin key configuration invalid: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is misconfigured. Contact your system administrator.",
        ) from exc

    if not keyring:
        logger.error(
            "No active admin API keys available — all admin requests rejected (fail-closed)."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured. Contact your system administrator.",
        )

    scoped_keyring = keyring
    if x_api_key_id:
        scoped_keyring = [
            k for k in keyring if hmac.compare_digest(k.key_id, x_api_key_id)
        ]
        if not scoped_keyring:
            logger.warning(
                "Unknown admin key id '%s' from %s",
                x_api_key_id,
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key id",
            )

    candidate_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    matched_key: Optional[_KeyRecord] = None
    for key in scoped_keyring:
        if hmac.compare_digest(candidate_hash, key.sha256_hash):
            matched_key = key
            break

    if not matched_key:
        logger.warning(
            f"Invalid admin API key attempt from "
            f"{request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    request.state.admin_key_id = matched_key.key_id
    request.state.admin_key_source = matched_key.source

    # If signature provided, verify it
    require_signature = bool(getattr(settings, "ADMIN_REQUIRE_API_SIGNATURE", False))
    if (
        require_signature
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and not x_signature
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Signature is required for admin mutating requests",
        )

    if x_signature:
        if not x_timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Timestamp required with X-Signature",
            )

        # Get request body
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""

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

        logger.info(
            "Authenticated admin request with signature from %s (key_id=%s)",
            request.client.host if request.client else "unknown",
            matched_key.key_id,
        )

    return True
