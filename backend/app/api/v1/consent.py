"""
Consent Management API — NFR-13

Allows users to manage their own data-processing consent.
All changes are audit-logged to admin_audit_log.

Routes:
  GET  /consent/purposes           — list available consent purposes
  GET  /consent/me                 — get current user's consent status
  POST /consent/me/{purpose}       — grant consent for a purpose
  DELETE /consent/me/{purpose}     — revoke consent for a purpose
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_consent import CONSENT_PURPOSES, UserConsent
from app.services.admin_audit import create_audit_entry

router = APIRouter(prefix="/consent", tags=["Consent"])


@router.get("/purposes")
async def list_purposes():
    """List all available data-processing consent purposes and descriptions."""
    descriptions = {
        "analytics": "Aggregate usage analytics to improve platform performance",
        "ml_training": "Use your crop data to train and improve ML risk models",
        "sms_alerts": "Receive SMS alerts for critical crop events",
        "third_party": "Share anonymised data with partner organisations",
        "research": "Allow academic or government research use of anonymised data",
    }
    return {
        "purposes": [
            {"id": p, "description": descriptions[p]} for p in CONSENT_PURPOSES
        ]
    }


@router.get("/me")
async def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current consent state for all purposes for the calling user."""
    existing = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == current_user.id,
            UserConsent.is_deleted == False,
        )
        .all()
    )
    consent_map = {c.purpose: c for c in existing}

    return {
        "user_id": str(current_user.id),
        "consents": [
            {
                "purpose": p,
                "granted": consent_map[p].granted if p in consent_map else False,
                "granted_at": (
                    consent_map[p].granted_at.isoformat()
                    if p in consent_map and consent_map[p].granted_at
                    else None
                ),
                "revoked_at": (
                    consent_map[p].revoked_at.isoformat()
                    if p in consent_map and consent_map[p].revoked_at
                    else None
                ),
            }
            for p in CONSENT_PURPOSES
        ],
    }


@router.post("/me/{purpose}", status_code=200)
async def grant_consent(
    purpose: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grant consent for a specific data-processing purpose."""
    if purpose not in CONSENT_PURPOSES:
        raise HTTPException(status_code=422, detail=f"Unknown purpose '{purpose}'")

    now = datetime.now(timezone.utc)
    consent = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == current_user.id,
            UserConsent.purpose == purpose,
            UserConsent.is_deleted == False,
        )
        .first()
    )

    if consent is None:
        consent = UserConsent(
            user_id=current_user.id,
            purpose=purpose,
            granted=True,
            granted_at=now,
            ip_address=request.client.host if request.client else None,
        )
        db.add(consent)
    else:
        consent.granted = True
        consent.granted_at = now
        consent.revoked_at = None

    db.commit()
    db.refresh(consent)

    # Audit log
    create_audit_entry(
        db,
        current_user.id,
        "consent_grant",
        "user_consent",
        consent.id,
        after_value={"purpose": purpose, "granted": True},
    )

    return {"purpose": purpose, "granted": True, "granted_at": now.isoformat()}


@router.delete("/me/{purpose}", status_code=200)
async def revoke_consent(
    purpose: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke consent for a specific data-processing purpose."""
    if purpose not in CONSENT_PURPOSES:
        raise HTTPException(status_code=422, detail=f"Unknown purpose '{purpose}'")

    now = datetime.now(timezone.utc)
    consent = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == current_user.id,
            UserConsent.purpose == purpose,
            UserConsent.is_deleted == False,
        )
        .first()
    )

    if consent is None:
        # Create a revoked record (evidence of explicit revoke)
        consent = UserConsent(
            user_id=current_user.id,
            purpose=purpose,
            granted=False,
            revoked_at=now,
            ip_address=request.client.host if request.client else None,
        )
        db.add(consent)
    else:
        consent.granted = False
        consent.revoked_at = now

    db.commit()
    db.refresh(consent)

    create_audit_entry(
        db,
        current_user.id,
        "consent_revoke",
        "user_consent",
        consent.id,
        after_value={"purpose": purpose, "granted": False},
    )

    return {"purpose": purpose, "granted": False, "revoked_at": now.isoformat()}
