"""
Consent Enforcement Guard — NFR-19, FR-25

FastAPI dependency that verifies the calling user has granted consent
for a specific data-processing purpose before allowing access.

Usage:
    @router.get("/protected", dependencies=[Depends(require_consent("analytics"))])
    async def protected_endpoint(...): ...

Consent purposes are defined in app.models.user_consent.CONSENT_PURPOSES.
"""

import logging
from functools import lru_cache

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_consent import UserConsent

logger = logging.getLogger(__name__)


def require_consent(purpose: str):
    """
    Returns a FastAPI dependency that enforces user consent for *purpose*.

    Raises 403 if the user has not granted consent.
    """

    async def _check_consent(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        consent = (
            db.query(UserConsent)
            .filter(
                UserConsent.user_id == current_user.id,
                UserConsent.purpose == purpose,
                UserConsent.granted == True,
                UserConsent.is_deleted == False,
            )
            .first()
        )
        if not consent:
            logger.info(
                f"Consent check failed: user={current_user.id} purpose={purpose}"
            )
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Consent required for '{purpose}'. "
                    f"Grant consent via POST /api/v1/consent/me/{purpose}"
                ),
            )
        return consent

    return _check_consent


def check_contact_sharing_consent(
    sender_id,
    recipient_id,
    db: Session,
) -> bool:
    """
    FR-25: Verify mutual consent for contact detail sharing.
    Both parties must have granted 'contact_sharing' consent.
    Returns True if both have consented, False otherwise.
    """
    consents = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id.in_([sender_id, recipient_id]),
            UserConsent.purpose == "contact_sharing",
            UserConsent.granted == True,
            UserConsent.is_deleted == False,
        )
        .all()
    )
    consented_users = {c.user_id for c in consents}
    return sender_id in consented_users and recipient_id in consented_users
