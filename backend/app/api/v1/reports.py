"""
User Reporting API — OR-14, OR-15

Enables users to flag fraudulent/abusive/non-compliant actors.
Admin review queue with status transitions.

Farmer routes:
  POST /reports                   — file a new report
  GET  /reports/me                — my filed reports

Admin routes:
  GET  /admin/reports             — all reports queue (filterable by status)
  PATCH /admin/reports/{id}/review — mark reviewed with notes
  PATCH /admin/reports/{id}/action — action taken
  PATCH /admin/reports/{id}/dismiss — dismiss report
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_report import REPORT_CATEGORIES, UserReport

router = APIRouter(tags=["Reports"])


def _require_admin(cu: User = Depends(get_current_user)) -> User:
    if cu.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return cu


# ─── Pydantic Schemas ────────────────────────────────────────────────────────


class ReportCreateRequest(BaseModel):
    reported_id: UUID
    category: str
    description: str = ""
    evidence_url: str = ""


class ReportReviewRequest(BaseModel):
    review_notes: str


class ReportDismissRequest(BaseModel):
    reason: str = ""


# ─── Farmer Routes ───────────────────────────────────────────────────────────


@router.post("/reports", status_code=201)
async def file_report(
    req: ReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """File a new report against a platform actor."""
    if req.category not in REPORT_CATEGORIES:
        raise HTTPException(
            status_code=422, detail=f"Invalid category '{req.category}'"
        )

    if req.reported_id == current_user.id:
        raise HTTPException(status_code=422, detail="Cannot report yourself")

    report = UserReport(
        reporter_id=current_user.id,
        reported_id=req.reported_id,
        category=req.category,
        description=req.description or None,
        evidence_url=req.evidence_url or None,
        status="open",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": str(report.id), "status": report.status, "category": report.category}


@router.get("/reports/me")
async def my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
):
    """List all reports filed by the current user."""
    PAGE_SIZE = 20
    q = (
        db.query(UserReport)
        .filter(
            UserReport.reporter_id == current_user.id,
            UserReport.is_deleted == False,
        )
        .order_by(UserReport.created_at.desc())
    )

    total = q.count()
    items = q.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    return {
        "items": [
            {
                "id": str(r.id),
                "category": r.category,
                "status": r.status,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": total,
        "page": page,
    }


# ─── Admin Routes ─────────────────────────────────────────────────────────────


@router.get("/admin/reports")
async def list_all_reports(
    status: str = Query(default="", description="Filter by status"),
    category: str = Query(default="", description="Filter by category"),
    page: int = Query(default=1, ge=1),
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Admin report queue with optional status/category filters."""
    PAGE_SIZE = 25
    q = db.query(UserReport).filter(UserReport.is_deleted == False)
    if status:
        q = q.filter(UserReport.status == status)
    if category:
        q = q.filter(UserReport.category == category)

    total = q.count()
    items = (
        q.order_by(UserReport.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    return {
        "items": [
            {
                "id": str(r.id),
                "reporter_id": str(r.reporter_id),
                "reported_id": str(r.reported_id),
                "category": r.category,
                "status": r.status,
                "description": r.description,
                "review_notes": r.review_notes,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": total,
        "page": page,
    }


@router.patch("/admin/reports/{report_id}/review")
async def review_report(
    report_id: UUID,
    req: ReportReviewRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Mark a report as reviewed and add admin notes."""
    report = (
        db.query(UserReport)
        .filter(UserReport.id == report_id, UserReport.is_deleted == False)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "reviewed"
    report.reviewed_by = admin.id
    report.review_notes = req.review_notes
    db.commit()
    db.refresh(report)
    return {"id": str(report.id), "status": report.status}


@router.patch("/admin/reports/{report_id}/action")
async def action_report(
    report_id: UUID,
    req: ReportReviewRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Record that action was taken on a report."""
    report = (
        db.query(UserReport)
        .filter(UserReport.id == report_id, UserReport.is_deleted == False)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "actioned"
    report.reviewed_by = admin.id
    report.review_notes = req.review_notes
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return {"id": str(report.id), "status": report.status}


@router.patch("/admin/reports/{report_id}/dismiss")
async def dismiss_report(
    report_id: UUID,
    req: ReportDismissRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Dismiss a report as invalid or duplicate."""
    report = (
        db.query(UserReport)
        .filter(UserReport.id == report_id, UserReport.is_deleted == False)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "dismissed"
    report.reviewed_by = admin.id
    report.review_notes = req.reason
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return {"id": str(report.id), "status": report.status}
