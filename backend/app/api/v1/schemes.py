"""
Official Schemes API — FR-31

Public browsing of government agricultural schemes.
Admin management of scheme entries.
Redirect audit trail when users click portal links.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.official_scheme import OfficialScheme
from app.models.scheme_redirect_log import SchemeRedirectLog
from app.models.user import User

router = APIRouter(prefix="/schemes", tags=["Schemes"])


class SchemeCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    portal_url: str
    category: Optional[str] = None
    region: Optional[str] = None
    crop_type: Optional[str] = None
    tags: Optional[List[str]] = None


class SchemeUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    portal_url: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Public — browse schemes
# ---------------------------------------------------------------------------


@router.get("")
async def list_schemes(
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List active government schemes. Public endpoint — no auth required."""
    q = db.query(OfficialScheme).filter(OfficialScheme.is_active == True)

    if region:
        q = q.filter(
            (OfficialScheme.region == region) | (OfficialScheme.region == None)
        )
    if crop_type:
        q = q.filter(
            (OfficialScheme.crop_type == crop_type) | (OfficialScheme.crop_type == None)
        )
    if category:
        q = q.filter(OfficialScheme.category == category)

    total = q.count()
    schemes = (
        q.order_by(OfficialScheme.name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "region": s.region,
                "crop_type": s.crop_type,
                "portal_url": s.portal_url,
                "tags": s.tags or [],
            }
            for s in schemes
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{scheme_id}")
async def get_scheme(scheme_id: UUID, db: Session = Depends(get_db)):
    """Get single scheme detail."""
    scheme = (
        db.query(OfficialScheme)
        .filter(
            OfficialScheme.id == scheme_id,
            OfficialScheme.is_active == True,
        )
        .first()
    )
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {
        "id": str(scheme.id),
        "name": scheme.name,
        "description": scheme.description,
        "category": scheme.category,
        "region": scheme.region,
        "crop_type": scheme.crop_type,
        "portal_url": scheme.portal_url,
        "tags": scheme.tags or [],
    }


# ---------------------------------------------------------------------------
# Authenticated — redirect with audit log
# ---------------------------------------------------------------------------


@router.post("/{scheme_id}/redirect", status_code=200)
async def redirect_to_scheme(
    scheme_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a portal redirect click and return the portal URL.
    Farmers call this when opening a scheme's official portal.
    """
    scheme = (
        db.query(OfficialScheme)
        .filter(
            OfficialScheme.id == scheme_id,
            OfficialScheme.is_active == True,
        )
        .first()
    )
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    log = SchemeRedirectLog(
        user_id=current_user.id,
        scheme_id=scheme.id,
        redirect_url=scheme.portal_url,
    )
    db.add(log)
    db.commit()

    return {"redirect_url": scheme.portal_url, "scheme_name": scheme.name}


# ---------------------------------------------------------------------------
# Admin — create / update schemes
# ---------------------------------------------------------------------------


@router.post("", status_code=201, dependencies=[Depends(require_role(["admin"]))])
async def create_scheme(
    req: SchemeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new government scheme entry (admin only)."""
    scheme = OfficialScheme(
        name=req.name,
        description=req.description,
        portal_url=req.portal_url,
        category=req.category,
        region=req.region,
        crop_type=req.crop_type,
        tags=req.tags or [],
    )
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return {"id": str(scheme.id), "name": scheme.name, "portal_url": scheme.portal_url}


@router.put("/{scheme_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_scheme(
    scheme_id: UUID,
    req: SchemeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing scheme entry (admin only). No downtime required."""
    scheme = db.query(OfficialScheme).filter(OfficialScheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    if req.name is not None:
        scheme.name = req.name
    if req.description is not None:
        scheme.description = req.description
    if req.portal_url is not None:
        scheme.portal_url = req.portal_url
    if req.category is not None:
        scheme.category = req.category
    if req.is_active is not None:
        scheme.is_active = req.is_active
    if req.tags is not None:
        scheme.tags = req.tags

    db.commit()
    return {"id": str(scheme.id), "is_active": scheme.is_active}
