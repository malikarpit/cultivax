"""
Dispute Resolution API — FR-33

Full lifecycle dispute workflow:
  POST   /disputes                        farmer/provider opens dispute
  GET    /disputes                        farmer sees own disputes
  GET    /admin/disputes                  admin sees all
  PATCH  /admin/disputes/{id}/assign      assign to admin investigator
  PATCH  /admin/disputes/{id}/resolve     close with resolution notes
  PATCH  /admin/disputes/{id}/dismiss     dismiss with reason
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.dispute_case import DisputeCase
from app.models.user import User
from app.services.admin_audit import create_audit_entry

router = APIRouter(tags=["Disputes"])

DISPUTE_SLA_HOURS = 48
VALID_CATEGORIES = {"quality", "fraud", "non_delivery", "payment", "other"}


class OpenDisputeRequest(BaseModel):
    respondent_id: UUID
    service_request_id: Optional[UUID] = None
    category: str
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Farmer — open and list own disputes
# ---------------------------------------------------------------------------


@router.post("/disputes", status_code=201)
async def open_dispute(
    req: OpenDisputeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open a new dispute case (FR-33)."""
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
        )

    case = DisputeCase(
        reporter_id=current_user.id,
        respondent_id=req.respondent_id,
        service_request_id=req.service_request_id,
        category=req.category,
        description=req.description,
        status="open",
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=DISPUTE_SLA_HOURS),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {
        "id": str(case.id),
        "status": case.status,
        "sla_deadline": case.sla_deadline.isoformat(),
    }


@router.get("/disputes")
async def list_own_disputes(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List disputes filed by the current user."""
    q = db.query(DisputeCase).filter(
        (DisputeCase.reporter_id == current_user.id)
        | (DisputeCase.respondent_id == current_user.id)
    )
    if status:
        q = q.filter(DisputeCase.status == status)

    total = q.count()
    cases = (
        q.order_by(DisputeCase.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": _serialize_cases(cases),
        "total": total,
    }


# ---------------------------------------------------------------------------
# Admin — full queue management
# ---------------------------------------------------------------------------


@router.get("/admin/disputes", dependencies=[Depends(require_role(["admin"]))])
async def list_all_disputes(
    status: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    overdue_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin view of all disputes (FR-33)."""
    q = db.query(DisputeCase)
    if status:
        q = q.filter(DisputeCase.status == status)
    if assigned_to:
        q = q.filter(DisputeCase.assigned_to == assigned_to)
    if overdue_only:
        q = q.filter(
            DisputeCase.sla_deadline < datetime.now(timezone.utc),
            DisputeCase.status.in_(["open", "investigating"]),
        )

    total = q.count()
    cases = (
        q.order_by(DisputeCase.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {"items": _serialize_cases(cases), "total": total}


@router.patch(
    "/admin/disputes/{case_id}/assign", dependencies=[Depends(require_role(["admin"]))]
)
async def assign_dispute(
    case_id: UUID,
    assignee_id: UUID = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign dispute to an admin investigator (FR-33)."""
    case = _get_or_404(db, case_id)
    case.assigned_to = assignee_id
    case.status = "investigating"
    create_audit_entry(
        db,
        admin_id=current_user.id,
        action="dispute_assigned",
        entity_type="dispute_case",
        entity_id=case_id,
    )
    db.commit()
    return {"id": str(case.id), "status": case.status, "assigned_to": str(assignee_id)}


@router.patch(
    "/admin/disputes/{case_id}/resolve", dependencies=[Depends(require_role(["admin"]))]
)
async def resolve_dispute(
    case_id: UUID,
    resolution_notes: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve a dispute with outcome notes (FR-33)."""
    case = _get_or_404(db, case_id)
    case.status = "resolved"
    case.resolution_notes = resolution_notes
    case.resolved_at = datetime.now(timezone.utc)
    case.resolved_by = current_user.id
    create_audit_entry(
        db,
        admin_id=current_user.id,
        action="dispute_resolved",
        entity_type="dispute_case",
        entity_id=case_id,
        after_value={"resolution_notes": resolution_notes},
    )
    db.commit()
    return {"id": str(case.id), "status": case.status}


@router.patch(
    "/admin/disputes/{case_id}/dismiss", dependencies=[Depends(require_role(["admin"]))]
)
async def dismiss_dispute(
    case_id: UUID,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss a dispute with reason (FR-33)."""
    case = _get_or_404(db, case_id)
    case.status = "dismissed"
    case.resolution_notes = f"Dismissed: {reason}"
    case.resolved_at = datetime.now(timezone.utc)
    case.resolved_by = current_user.id
    create_audit_entry(
        db,
        admin_id=current_user.id,
        action="dispute_dismissed",
        entity_type="dispute_case",
        entity_id=case_id,
        reason=reason,
    )
    db.commit()
    return {"id": str(case.id), "status": case.status}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, case_id: UUID) -> DisputeCase:
    case = db.query(DisputeCase).filter(DisputeCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Dispute case not found")
    return case


def _serialize_cases(cases):
    now = datetime.now(timezone.utc)
    result = []
    for c in cases:
        deadline = c.sla_deadline
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        overdue = (
            deadline is not None
            and deadline < now
            and c.status in ("open", "investigating")
        )
        result.append(
            {
                "id": str(c.id),
                "reporter_id": str(c.reporter_id) if c.reporter_id else None,
                "respondent_id": str(c.respondent_id) if c.respondent_id else None,
                "category": c.category,
                "status": c.status,
                "assigned_to": str(c.assigned_to) if c.assigned_to else None,
                "sla_deadline": c.sla_deadline.isoformat() if c.sla_deadline else None,
                "overdue": overdue,
                "resolution_notes": c.resolution_notes,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        )
    return result
