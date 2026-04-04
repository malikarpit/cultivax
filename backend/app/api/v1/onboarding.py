"""
Onboarding API

Lightweight endpoints for onboarding state transitions.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/complete", status_code=status.HTTP_200_OK)
def complete_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark the current user as fully onboarded.

    Idempotent: calling twice will keep the flag true without errors.
    """
    if not current_user.is_onboarded:
        current_user.is_onboarded = True
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return {"is_onboarded": current_user.is_onboarded}

