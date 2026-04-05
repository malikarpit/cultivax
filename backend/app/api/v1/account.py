"""
Account Self-Service API — NFR-16 / NFR-17 / NFR-18

Allows users to:
  - Export their personal data as JSON (GDPR-style right to portability)
  - Request account deletion (anonymises PII, soft-deletes record)

Routes:
  GET  /account/me/export   — download personal data bundle
  POST /account/me/delete   — anonymise and soft-delete account
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_consent import UserConsent
from app.services.admin_audit import create_audit_entry
from app.services.anonymization import anonymize_user

router = APIRouter(prefix="/account", tags=["Account"])


class DeleteAccountRequest(BaseModel):
    confirmation: str  # must equal "DELETE MY ACCOUNT"
    reason: str = ""


@router.get("/me/export")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all personal data for the requesting user.

    Returns a JSON bundle containing profile, consents, and summary counts.
    Complies with NFR-16 (right to portability).
    """
    consents = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == current_user.id,
            UserConsent.is_deleted == False,
        )
        .all()
    )

    # Build export bundle
    bundle = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
        "profile": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "region": current_user.region,
            "is_active": current_user.is_active,
            "created_at": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
        },
        "consents": [
            {
                "purpose": c.purpose,
                "granted": c.granted,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
            }
            for c in consents
        ],
    }

    create_audit_entry(
        db,
        current_user.id,
        "data_export",
        "user",
        current_user.id,
        after_value={"requested_at": bundle["exported_at"]},
    )

    return JSONResponse(
        content=bundle,
        headers={
            "Content-Disposition": f'attachment; filename="cultivax_data_{str(current_user.id)[:8]}.json"'
        },
    )


@router.post("/me/delete", status_code=200)
async def delete_my_account(
    req: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Anonymise and soft-delete the requesting user's account.

    PII is overwritten with anonymised values; the row is soft-deleted.
    Complies with NFR-17 (right to erasure / anonymisation).
    """
    if req.confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=422,
            detail="Confirmation text must be exactly 'DELETE MY ACCOUNT'",
        )

    anonymize_user(db, current_user, reason=req.reason)

    create_audit_entry(
        db,
        current_user.id,
        "account_delete",
        "user",
        current_user.id,
        reason=req.reason or "User-requested self-deletion",
        after_value={
            "anonymised": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "message": "Account anonymised and deleted",
        "user_id": str(current_user.id),
    }
