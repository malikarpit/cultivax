"""
Anonymisation Service — NFR-18 / NFR-19

Provides deterministic, auditable PII scrubbing utilities:
  - anonymize_user()          — overwrite a User's PII with synthetic values
  - anonymize_ml_dataset()    — scrub field-level PII from a data dict
  - mask_phone()              — mask all but last 4 digits
  - mask_email()              — mask local part of email
  - redact_payload()          — scrub sensitive keys from a JSON-serializable dict

Design: anonymisation is idempotent — calling twice on the same record is safe.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

# Keys universally treated as PII in payload dicts
PII_KEYS = frozenset(
    {
        "full_name",
        "name",
        "phone",
        "email",
        "address",
        "password",
        "password_hash",
        "ip_address",
        "user_agent",
        "bank_account",
        "aadhaar",
        "pan",
    }
)

# Sentinel that signals a field has already been anonymised
_ANON_SENTINEL = "[REDACTED]"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def mask_phone(phone: str) -> str:
    """Replace all but the last 4 digits of a phone number."""
    if not phone or len(phone) < 4:
        return _ANON_SENTINEL
    return "****" + phone[-4:]


def mask_email(email: str) -> str:
    """Replace the local part of an email with a hash prefix."""
    if not email or "@" not in email:
        return _ANON_SENTINEL
    local, domain = email.split("@", 1)
    hashed = hashlib.sha256(local.encode()).hexdigest()[:8]
    return f"anon_{hashed}@{domain}"


def redact_payload(
    payload: dict[str, Any], extra_keys: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """
    Recursively redact PII keys from a payload dict.

    Keys in PII_KEYS (or extra_keys) are replaced with '[REDACTED]'.
    Safe for JSON-serialisable dicts.
    """
    redact_set = PII_KEYS | extra_keys
    result: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in redact_set:
            result[k] = _ANON_SENTINEL
        elif isinstance(v, dict):
            result[k] = redact_payload(v, extra_keys)
        elif isinstance(v, list):
            result[k] = [
                redact_payload(item, extra_keys) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


def anonymize_ml_dataset(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Scrub PII from a list of ML training records.

    Each record has phone/email/name fields replaced with masked values.
    Preserves all agronomic features (crop_type, soil_ph, etc.) needed for training.
    """
    scrubbed = []
    for record in records:
        clean = {}
        for k, v in record.items():
            if k.lower() in PII_KEYS:
                clean[k] = _ANON_SENTINEL
            elif k.lower() == "phone" and isinstance(v, str):
                clean[k] = mask_phone(v)
            elif k.lower() == "email" and isinstance(v, str):
                clean[k] = mask_email(v)
            else:
                clean[k] = v
        scrubbed.append(clean)
    return scrubbed


def anonymize_user(db: Session, user: Any, reason: str = "") -> None:
    """
    Overwrite a User model's PII with synthetic values and soft-delete.

    This is idempotent — safe to call multiple times.
    Requires the caller to commit the session after this call.
    """
    uid_short = str(user.id)[:8]
    now = datetime.now(timezone.utc)

    # Overwrite PII in-place
    user.full_name = f"Deleted User {uid_short}"
    user.phone = f"+00{uid_short}"
    user.email = f"deleted_{uid_short}@cultivax.invalid"
    user.password_hash = "[DELETED]"
    user.is_active = False

    # Soft-delete
    user.is_deleted = True
    user.deleted_at = now

    db.add(user)
    db.commit()
