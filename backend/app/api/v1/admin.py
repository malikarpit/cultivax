"""
Admin API

Administrative endpoints for user management, provider governance,
and audit log access.

GET    /api/v1/admin/users
PUT    /api/v1/admin/users/{user_id}/role
DELETE /api/v1/admin/users/{user_id}
PUT    /api/v1/admin/providers/{provider_id}/verify
PUT    /api/v1/admin/providers/{provider_id}/suspend
GET    /api/v1/admin/audit
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.active_session import ActiveSession
from app.models.admin_audit import AdminAuditLog
from app.models.alert import Alert
from app.models.service_provider import ServiceProvider
from app.models.user import User
from app.schemas.admin import AdminAuditResponse
from app.schemas.user import UserResponse
from app.services.admin_audit import create_audit_entry

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_deleted: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users (admin only) with pagination and filters."""
    query = db.query(User)

    if is_deleted is not None:
        query = query.filter(User.is_deleted == is_deleted)
    if role:
        query = query.filter(User.role == role)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term))
            | (User.phone.ilike(search_term))
            | (User.email.ilike(search_term))
        )

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.put(
    "/users/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def update_user_role(
    user_id: UUID,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change a user's role (admin only)."""
    if new_role not in ("farmer", "provider", "admin"):
        raise HTTPException(
            status_code=400,
            detail="INVALID_ROLE: Role must be one of farmer, provider, admin",
        )

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = new_role

    # Session revocation hook if downgrading from admin
    if old_role == "admin" and new_role != "admin":
        active_sessions = (
            db.query(ActiveSession)
            .filter(ActiveSession.user_id == user_id, ActiveSession.is_revoked == False)
            .all()
        )
        for session in active_sessions:
            session.revoke()

    # Audit log entry
    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="role_change",
        entity_type="user",
        entity_id=user_id,
        after_value={"old_role": old_role, "new_role": new_role},
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["admin"]))],
)
async def soft_delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a user (admin only). No hard deletes per MSDD 5.10."""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.deleted_by = current_user.id

    # Revoke all sessions on soft delete
    active_sessions = (
        db.query(ActiveSession)
        .filter(ActiveSession.user_id == user_id, ActiveSession.is_revoked == False)
        .all()
    )
    for session in active_sessions:
        session.revoke()

    # Audit
    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="user_deleted",
        entity_type="user",
        entity_id=user_id,
    )
    db.commit()


@router.post(
    "/users/{user_id}/restore",
    response_model=UserResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def restore_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restore a soft-deleted user (admin only)."""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == True).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="INVALID_OPERATION: User is not deleted or not found",
        )

    user.is_deleted = False
    user.deleted_at = None
    user.deleted_by = None

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="user_restored",
        entity_type="user",
        entity_id=user_id,
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get(
    "/providers",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_providers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_verified: Optional[bool] = None,
    is_suspended: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve all service providers natively filtered for Administrative tracking."""
    query = db.query(ServiceProvider)

    if is_verified is not None:
        query = query.filter(ServiceProvider.is_verified == is_verified)

    if is_suspended is not None:
        query = query.filter(ServiceProvider.is_suspended == is_suspended)

    if search:
        query = query.filter(
            or_(
                ServiceProvider.business_name.ilike(f"%{search}%"),
                ServiceProvider.service_type.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    providers = (
        query.order_by(ServiceProvider.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {"items": providers, "total": total, "page": page, "per_page": per_page}


@router.put(
    "/providers/{provider_id}/verify",
    dependencies=[Depends(require_role(["admin"]))],
)
async def verify_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify a service provider (admin only)."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.is_suspended:
        raise HTTPException(
            status_code=400,
            detail="Cannot verify a suspended provider. Unsuspend first.",
        )

    if provider.is_verified:
        return {"status": "already_verified", "provider_id": str(provider_id)}

    provider.is_verified = True
    provider.verified_at = datetime.now(timezone.utc)
    provider.verified_by = current_user.id

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="provider_verified",
        entity_type="service_provider",
        entity_id=provider_id,
    )

    alert = Alert(
        user_id=provider.user_id,
        alert_type="GovernanceAction",
        severity="info",
        urgency_level="Medium",
        message="Your provider profile has been successfully verified! You are now visible in public search listings.",
    )
    db.add(alert)

    db.commit()
    return {"status": "verified", "provider_id": str(provider_id)}


@router.put(
    "/providers/{provider_id}/unverify",
    dependencies=[Depends(require_role(["admin"]))],
)
async def unverify_provider(
    provider_id: UUID,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove verification from a service provider (admin only)."""
    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if not provider.is_verified:
        raise HTTPException(status_code=400, detail="Provider is already unverified.")

    provider.is_verified = False
    provider.verified_at = None
    provider.verified_by = None

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="provider_unverified",
        entity_type="service_provider",
        entity_id=provider_id,
        reason=reason,
    )

    alert = Alert(
        user_id=provider.user_id,
        alert_type="GovernanceAction",
        severity="warning",
        urgency_level="High",
        message=f"Your provider verification was removed. Reason: {reason}. You are no longer visible in public verified bounds.",
    )
    db.add(alert)
    db.commit()
    return {"status": "unverified", "provider_id": str(provider_id)}


@router.put(
    "/providers/{provider_id}/suspend",
    dependencies=[Depends(require_role(["admin"]))],
)
async def suspend_provider(
    provider_id: UUID,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suspend a service provider (admin only)."""
    if not reason or len(reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Suspension requires a reason.")

    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.is_suspended:
        raise HTTPException(status_code=400, detail="Provider is already suspended.")

    provider.is_suspended = True
    provider.suspension_reason = reason

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="provider_suspended",
        entity_type="service_provider",
        entity_id=provider_id,
        reason=reason,
    )

    alert = Alert(
        user_id=provider.user_id,
        alert_type="GovernanceAction",
        severity="critical",
        urgency_level="Critical",
        message=f"Your provider profile has been suspended. Reason: {reason}. You have been removed from the platform. Contact support to appeal.",
    )
    db.add(alert)

    db.commit()
    return {"status": "suspended", "provider_id": str(provider_id), "reason": reason}


@router.put(
    "/providers/{provider_id}/unsuspend",
    dependencies=[Depends(require_role(["admin"]))],
)
async def unsuspend_provider(
    provider_id: UUID,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unsuspend a service provider (admin only)."""
    if not reason or len(reason.strip()) == 0:
        raise HTTPException(
            status_code=400, detail="Unsuspension requires a justification."
        )

    provider = (
        db.query(ServiceProvider)
        .filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_deleted == False,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if not provider.is_suspended:
        raise HTTPException(
            status_code=400, detail="Provider is not currently suspended."
        )

    provider.is_suspended = False
    provider.suspension_reason = None

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="provider_unsuspended",
        entity_type="service_provider",
        entity_id=provider_id,
        reason=reason,
    )

    alert = Alert(
        user_id=provider.user_id,
        alert_type="GovernanceAction",
        severity="info",
        urgency_level="Medium",
        message=f"Your profile suspension was lifted! Reason: {reason}.",
    )
    db.add(alert)

    db.commit()
    return {"status": "unsuspended", "provider_id": str(provider_id)}


# ──────────────────────────────────────────────────────────────────────────────
# Maintenance Status & Cron Observability
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/maintenance/status",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_maintenance_status(
    current_user: User = Depends(get_current_user),
):
    """
    Return live maintenance task status: last run, next eligible run,
    overdue flags, consecutive failure counts, and lock state.
    This endpoint reads in-memory state — no DB query required.
    """
    from app.services.cron import get_maintenance_status

    return get_maintenance_status()


@router.post(
    "/maintenance/run",
    dependencies=[Depends(require_role(["admin"]))],
)
async def trigger_maintenance(
    cadence: Optional[str] = None,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-authenticated cron trigger (session-based, no API key needed).
    Complements the API-key secured /admin/cron/run hook used by Cloud Scheduler.

    Query params:
      - cadence: hourly | daily | weekly | (omit = all)
      - force: bypass min-interval cadence guards
    """
    from app.services.cron import run_scheduled_tasks

    if cadence and cadence not in ("hourly", "daily", "weekly"):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail="cadence must be one of: hourly, daily, weekly"
        )

    result = await run_scheduled_tasks(db, cadence=cadence, force=force)
    return result


@router.get(
    "/audit",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_audit_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    admin_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve admin audit log entries."""
    query = db.query(AdminAuditLog)
    if action:
        query = query.filter(AdminAuditLog.action == action)
    if admin_id:
        query = query.filter(AdminAuditLog.admin_id == admin_id)
    if entity_type:
        query = query.filter(AdminAuditLog.entity_type == entity_type)
    if date_from:
        query = query.filter(AdminAuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AdminAuditLog.created_at <= date_to)

    total = query.count()
    logs = (
        query.order_by(AdminAuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [AdminAuditResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


# --- Farmer Data Export (MSDD 5.10 — Data Portability) ---


@router.get(
    "/farmers/{farmer_id}/export",
    dependencies=[Depends(require_role(["admin"]))],
)
async def export_farmer_data(
    farmer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export all farmer data as JSON (data portability per MSDD 5.10).
    Returns: user profile, crop instances, action logs, media files, alerts.
    """
    from app.models.action_log import ActionLog
    from app.models.alert import Alert
    from app.models.crop_instance import CropInstance
    from app.models.media_file import MediaFile

    user = db.query(User).filter(User.id == farmer_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Farmer not found")

    crops = (
        db.query(CropInstance)
        .filter(
            CropInstance.farmer_id == farmer_id,
            CropInstance.is_deleted == False,
        )
        .all()
    )

    crop_ids = [c.id for c in crops]

    actions = []
    media = []
    alerts_data = []
    if crop_ids:
        actions = (
            db.query(ActionLog)
            .filter(
                ActionLog.crop_instance_id.in_(crop_ids),
                ActionLog.is_deleted == False,
            )
            .all()
        )
        media = (
            db.query(MediaFile)
            .filter(
                MediaFile.crop_instance_id.in_(crop_ids),
                MediaFile.is_deleted == False,
            )
            .all()
        )
        alerts_data = (
            db.query(Alert)
            .filter(
                Alert.user_id == farmer_id,
                Alert.is_deleted == False,
            )
            .all()
        )

    return {
        "farmer": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
            "region": user.region,
            "preferred_language": user.preferred_language,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "crops": [
            {
                "id": str(c.id),
                "crop_type": c.crop_type,
                "variety": c.variety,
                "sowing_date": c.sowing_date.isoformat() if c.sowing_date else None,
                "state": c.state,
                "stage": c.stage,
                "region": c.region,
            }
            for c in crops
        ],
        "action_logs": [
            {
                "id": str(a.id),
                "crop_instance_id": str(a.crop_instance_id),
                "action_type": a.action_type,
                "effective_date": (
                    a.effective_date.isoformat() if a.effective_date else None
                ),
                "notes": a.notes,
            }
            for a in actions
        ],
        "media_files": [
            {
                "id": str(m.id),
                "crop_instance_id": str(m.crop_instance_id),
                "file_type": m.file_type,
                "analysis_status": m.analysis_status,
            }
            for m in media
        ],
        "alerts": [
            {
                "id": str(al.id),
                "alert_type": al.alert_type,
                "severity": al.severity,
                "message": al.message,
                "is_acknowledged": al.is_acknowledged,
            }
            for al in alerts_data
        ],
        "export_generated_at": datetime.now(timezone.utc).isoformat(),
    }


# --- Abuse Flag Review Pipeline ---


@router.get(
    "/abuse-flags",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_abuse_flags(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    flag_status: Optional[str] = Query("open", alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List abuse flags for admin review."""
    from app.models.abuse_flag import AbuseFlag

    query = db.query(AbuseFlag).filter(AbuseFlag.is_deleted == False)
    if flag_status:
        query = query.filter(AbuseFlag.status == flag_status)

    total = query.count()
    flags = (
        query.order_by(AbuseFlag.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [
            {
                "id": str(f.id),
                "farmer_id": str(f.farmer_id),
                "flag_type": f.flag_type,
                "severity": f.severity,
                "anomaly_score": f.anomaly_score,
                "details": f.details,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in flags
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get(
    "/abuse-flags/{flag_id}",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_abuse_flag(
    flag_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get abuse flag detail."""
    from app.models.abuse_flag import AbuseFlag

    flag = (
        db.query(AbuseFlag)
        .filter(
            AbuseFlag.id == flag_id,
            AbuseFlag.is_deleted == False,
        )
        .first()
    )

    if not flag:
        raise HTTPException(status_code=404, detail="Abuse flag not found")

    return {
        "id": str(flag.id),
        "farmer_id": str(flag.farmer_id),
        "flag_type": flag.flag_type,
        "severity": flag.severity,
        "anomaly_score": flag.anomaly_score,
        "details": flag.details,
        "status": flag.status,
        "resolved_by": str(flag.resolved_by) if flag.resolved_by else None,
        "created_at": flag.created_at.isoformat() if flag.created_at else None,
        "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
    }


@router.patch(
    "/abuse-flags/{flag_id}/review",
    dependencies=[Depends(require_role(["admin"]))],
)
async def review_abuse_flag(
    flag_id: UUID,
    new_status: str = Query(..., description="reviewed | dismissed | actioned"),
    review_notes: str = Query("", description="Admin notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review and action on an abuse flag (admin only)."""
    from app.models.abuse_flag import AbuseFlag

    if new_status not in ("reviewed", "dismissed", "actioned"):
        raise HTTPException(status_code=422, detail="Invalid status")

    flag = (
        db.query(AbuseFlag)
        .filter(
            AbuseFlag.id == flag_id,
            AbuseFlag.is_deleted == False,
        )
        .first()
    )

    if not flag:
        raise HTTPException(status_code=404, detail="Abuse flag not found")

    flag.status = new_status
    flag.resolved_by = current_user.id

    # Audit trail
    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="abuse_flag_reviewed",
        entity_type="abuse_flag",
        entity_id=flag_id,
        after_value={"new_status": new_status, "notes": review_notes},
    )

    return {
        "id": str(flag.id),
        "status": flag.status,
        "reviewed_at": flag.updated_at.isoformat() if flag.updated_at else None,
    }


@router.get(
    "/health",
    dependencies=[Depends(require_role(["admin"]))],
)
async def admin_health_detail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-only full health detail endpoint.
    Returns subsystem details, error messages, freshness, and latency probes.
    """
    from app.services.system_health_service import SystemHealthService

    service = SystemHealthService(db)
    summary = service.get_status_summary(admin_detail=True)
    return summary


# --- DLQ & Event Recovery ---

from typing import Any, List

from pydantic import BaseModel

from app.models.event_log import EventLog


class BulkRetryRequest(BaseModel):
    event_type: Optional[str] = None
    older_than_minutes: Optional[int] = None
    limit: int = 100
    reason: str


@router.get(
    "/dead-letters",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_dead_letters(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List failed DeadLetter events with full diagnostic parameters."""
    query = db.query(EventLog).filter(EventLog.status == "DeadLetter")

    if event_type:
        query = query.filter(EventLog.event_type == event_type)

    query = query.order_by(EventLog.created_at.desc())
    total_count = query.count()
    events = query.offset((page - 1) * per_page).limit(per_page).all()

    results = []
    now = datetime.now(timezone.utc)
    for e in events:
        created = e.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_seconds = (now - created).total_seconds() if created else 0

        results.append(
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": str(e.entity_id),
                "status": e.status,
                "retry_count": e.retry_count,
                "max_retries": e.max_retries,
                "failure_reason": e.failure_reason,
                "last_error": e.last_error,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "last_failed_at": (
                    e.last_failed_at.isoformat() if e.last_failed_at else None
                ),
                "age_seconds": round(age_seconds),
            }
        )

    return {"items": results, "total": total_count, "page": page, "per_page": per_page}


@router.post(
    "/dead-letters/{event_id}/retry",
    dependencies=[Depends(require_role(["admin"]))],
)
async def retry_single_dead_letter(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset a DeadLetter event to Created state for reprocessing."""
    event = db.query(EventLog).filter(EventLog.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "DeadLetter":
        raise HTTPException(
            status_code=400, detail=f"Cannot retry event in {event.status} state"
        )

    event.status = "Created"
    event.retry_count = 0  # Re-allow max_retries attempts
    event.failure_reason = f"Manually retried by admin {current_user.email}"
    event.next_retry_at = None

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="retry_dead_letter",
        entity_type="event_log",
        entity_id=event.id,
        reason="Manual UI recovery",
    )

    return {"status": "success", "event_id": str(event.id), "new_state": "Created"}


@router.post(
    "/dead-letters/bulk-retry",
    dependencies=[Depends(require_role(["admin"]))],
)
async def bulk_retry_dead_letters(
    req: BulkRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely reset multiple DeadLetter events matching constraints."""
    query = db.query(EventLog).filter(EventLog.status == "DeadLetter")

    if req.event_type:
        query = query.filter(EventLog.event_type == req.event_type)

    if req.older_than_minutes:
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=req.older_than_minutes)
        query = query.filter(EventLog.created_at <= cutoff)

    events = query.order_by(EventLog.created_at.asc()).limit(req.limit).all()

    retried_count = 0
    for event in events:
        event.status = "Created"
        event.retry_count = 0
        event.failure_reason = f"Bulk retry: {req.reason}"
        event.next_retry_at = None
        retried_count += 1

    if retried_count > 0:
        create_audit_entry(
            db=db,
            admin_id=current_user.id,
            action="bulk_retry_dead_letters",
            entity_type="system",
            entity_id=current_user.id,
            reason=req.reason,
            after_value={
                "event_type_filter": req.event_type,
                "limit": req.limit,
                "retried_count": retried_count,
            },
        )

    return {
        "retried": retried_count,
        "skipped": req.limit - retried_count if retried_count < req.limit else 0,
        "errors": [],
    }


@router.delete(
    "/dead-letters/{event_id}",
    dependencies=[Depends(require_role(["admin"]))],
)
async def discard_dead_letter(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Discard a DeadLetter event permanently (soft delete)."""
    event = db.query(EventLog).filter(EventLog.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "DeadLetter":
        raise HTTPException(
            status_code=400, detail=f"Cannot discard event in {event.status} state"
        )

    event.is_deleted = True
    event.deleted_at = datetime.now(timezone.utc)
    event.deleted_by = current_user.id
    event.failure_reason = (
        f"Discarded by admin {current_user.email}: {event.failure_reason}"
    )

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="discard_dead_letter",
        entity_type="event_log",
        entity_id=event.id,
        reason="Manual UI discard",
    )

    return {"status": "success", "event_id": str(event.id), "new_state": "Discarded"}


@router.get(
    "/security-events",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_security_events(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """Retrieve recent security events (rate limits, payload issues) from in-memory ring buffer (Admin only)."""
    try:
        from app.security.events import get_recent_security_events

        events = get_recent_security_events(limit=limit)
        return {"success": True, "events": events}
    except ImportError:
        return {
            "success": True,
            "events": [],
            "warning": "Security event store not available",
        }


# ──────────────────────────────────────────────────────────────────────────────
# Force-Replay endpoint (MSDD API-0083 / TDD-8-C0038)
# ──────────────────────────────────────────────────────────────────────────────


@router.post(
    "/crops/{crop_id}/force-replay",
    dependencies=[Depends(require_role(["admin"]))],
    summary="Force action-log replay for a crop instance (API-0083)",
)
async def force_crop_replay(
    crop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a full CTIS replay for a specific crop instance.

    Used by admins to recover from diverged state after data corrections.
    Queues the crop for immediate replay without waiting for the nightly cycle.

    MSDD API-0083 | TDD-8-C0038
    """
    from app.models.crop_instance import CropInstance

    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == crop_id,
            CropInstance.is_deleted == False,
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found")

    # Emit a domain event to trigger replay via the event pipeline
    import json

    from app.models.event_log import EventLog

    replay_event = EventLog(
        event_type="ctis.replay_requested",
        entity_type="crop_instance",
        entity_id=crop_id,
        payload=json.dumps(
            {
                "crop_id": str(crop_id),
                "requested_by": str(current_user.id),
                "reason": "admin_force_replay",
            }
        ),
        partition_key=str(crop_id),
        module_target="ctis",
        priority=10,  # High priority
        schema_version=1,
    )
    db.add(replay_event)

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="force_replay",
        entity_type="crop_instance",
        entity_id=crop_id,
    )

    db.commit()

    return {
        "status": "replay_queued",
        "crop_id": str(crop_id),
        "event_id": str(replay_event.id),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Admin event trace (MSDD API-0015 / MSDD-8-C0076)
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/events/{crop_instance_id}",
    dependencies=[Depends(require_role(["admin"]))],
    summary="Retrieve event trace for a crop instance (API-0015)",
)
async def get_crop_event_trace(
    crop_instance_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full event log trace for a specific crop instance.

    Useful for debugging CTIS divergence, replay issues, and audit purposes.
    Returns events ordered by creation time (oldest first).

    MSDD API-0015 | MSDD-8-C0076
    """
    from app.models.event_log import EventLog

    events = (
        db.query(EventLog)
        .filter(
            EventLog.entity_id == crop_instance_id,
            EventLog.is_deleted == False,
        )
        .order_by(EventLog.created_at.asc())
        .limit(limit)
        .all()
    )

    return {
        "crop_instance_id": str(crop_instance_id),
        "event_count": len(events),
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "status": e.status,
                "priority": e.priority,
                "retry_count": e.retry_count,
                "failure_reason": e.failure_reason,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
                "payload": e.payload,
            }
            for e in events
        ],
    }
