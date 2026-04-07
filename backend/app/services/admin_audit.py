import copy
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminAuditLog

logger = logging.getLogger(__name__)

# Core list of explicit actions strictly requiring `.reason` justification
DESTRUCTIVE_ACTIONS = {
    "provider_suspend",
    "provider_deactivate",
    "user_deactivate",
    "user_role_change",
    "activate_ml_model",
    "deactivate_ml_model",
    "rule_deprecate",
    "dead_letter_bulk_retry",
}

# Values that must be scrubbed natively from before/after payloads tracking changes
SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "secret",
    "private_key",
    "access_token",
}


def strip_sensitive_payloads(
    payload: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Sanitize strict sensitive secrets from JSON payloads preventing database exposure."""
    if not payload:
        return payload

    sanitized = copy.deepcopy(payload)

    def _redact(data: Any):
        if isinstance(data, dict):
            for k, v in data.items():
                if any(sk in k.lower() for sk in SENSITIVE_KEYS):
                    data[k] = "[REDACTED]"
                else:
                    _redact(v)
        elif isinstance(data, list):
            for item in data:
                _redact(item)

    _redact(sanitized)
    return sanitized


def create_audit_entry(
    db: Session,
    admin_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | str,
    reason: Optional[str] = None,
    before_value: Optional[Dict[str, Any]] = None,
    after_value: Optional[Dict[str, Any]] = None,
) -> AdminAuditLog:
    """
    Constructs a formalized AdminAuditLog ensuring compliance constraints dynamically.
    Fails aggressively if an operation requires a `.reason` and it isn't supplied.
    """

    # 1. Enforce Destructive Validations
    if action in DESTRUCTIVE_ACTIONS and not reason:
        logger.error(
            f"Audit compliance rejected: Action '{action}' strictly requires a reason."
        )
        raise HTTPException(
            status_code=400,
            detail=f"Action '{action}' requires explicit operational reasoning.",
        )

    # 2. Sanitize and structure the footprint tracking bounds
    audit = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=(
            entity_id if isinstance(entity_id, UUID) else str(entity_id)
        ),  # Some systems may pass Strings
        before_value=strip_sensitive_payloads(before_value),
        after_value=strip_sensitive_payloads(after_value),
        reason=reason,
    )

    db.add(audit)
    db.commit()
    return audit
