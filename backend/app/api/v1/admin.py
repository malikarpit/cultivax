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

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.service_provider import ServiceProvider
from app.models.admin_audit import AdminAuditLog
from app.schemas.user import UserResponse
from app.schemas.admin import AdminAuditResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users (admin only)."""
    query = db.query(User).filter(User.is_deleted == False)
    if role:
        query = query.filter(User.role == role)

    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [UserResponse.model_validate(u) for u in users]


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
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = new_role

    # Audit log entry
    audit = AdminAuditLog(
        admin_id=current_user.id,
        action="role_change",
        target_type="user",
        target_id=user_id,
        details={"old_role": old_role, "new_role": new_role},
    )
    db.add(audit)
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

    # Audit
    audit = AdminAuditLog(
        admin_id=current_user.id,
        action="user_deleted",
        target_type="user",
        target_id=user_id,
    )
    db.add(audit)
    db.commit()


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
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == provider_id,
        ServiceProvider.is_deleted == False,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.is_verified = True
    provider.verified_at = datetime.now(timezone.utc)
    provider.verified_by = current_user.id

    audit = AdminAuditLog(
        admin_id=current_user.id,
        action="provider_verified",
        target_type="service_provider",
        target_id=provider_id,
    )
    db.add(audit)
    db.commit()
    return {"status": "verified", "provider_id": str(provider_id)}


@router.put(
    "/providers/{provider_id}/suspend",
    dependencies=[Depends(require_role(["admin"]))],
)
async def suspend_provider(
    provider_id: UUID,
    reason: str = "Policy violation",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suspend a service provider (admin only)."""
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.id == provider_id,
        ServiceProvider.is_deleted == False,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.is_suspended = True
    provider.suspension_reason = reason

    audit = AdminAuditLog(
        admin_id=current_user.id,
        action="provider_suspended",
        target_type="service_provider",
        target_id=provider_id,
        details={"reason": reason},
    )
    db.add(audit)
    db.commit()
    return {"status": "suspended", "provider_id": str(provider_id), "reason": reason}


@router.get(
    "/audit",
    response_model=list[AdminAuditResponse],
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_audit_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve admin audit log entries."""
    query = db.query(AdminAuditLog)
    if action:
        query = query.filter(AdminAuditLog.action == action)

    logs = (
        query.order_by(AdminAuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [AdminAuditResponse.model_validate(log) for log in logs]


# --- Dead Letter Queue Management (MSDD Enhancement Sec 3) ---

@router.get(
    "/dead-letters",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_dead_letters(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all events in the Dead Letter Queue."""
    from app.models.event_log import EventLog

    query = db.query(EventLog).filter(EventLog.status == "DeadLetter")
    if event_type:
        query = query.filter(EventLog.event_type == event_type)

    total = query.count()
    events = (
        query.order_by(EventLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": str(e.entity_id),
                "failure_reason": e.failure_reason,
                "retry_count": e.retry_count,
                "max_retries": e.max_retries,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post(
    "/dead-letters/{event_id}/retry",
    dependencies=[Depends(require_role(["admin"]))],
)
async def retry_dead_letter(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retry a dead-lettered event by resetting it back to Created status."""
    from app.models.event_log import EventLog

    event = db.query(EventLog).filter(
        EventLog.id == event_id,
        EventLog.status == "DeadLetter",
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Dead letter event not found")

    event.status = "Created"
    event.retry_count = 0
    event.failure_reason = None

    # Audit
    audit = AdminAuditLog(
        admin_id=current_user.id,
        action="dead_letter_retry",
        target_type="event_log",
        target_id=event_id,
        details={"event_type": event.event_type},
    )
    db.add(audit)
    db.commit()

    return {"status": "retried", "event_id": str(event_id)}


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
    from app.models.crop_instance import CropInstance
    from app.models.action_log import ActionLog
    from app.models.media_file import MediaFile
    from app.models.alert import Alert

    user = db.query(User).filter(User.id == farmer_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Farmer not found")

    crops = db.query(CropInstance).filter(
        CropInstance.farmer_id == farmer_id,
        CropInstance.is_deleted == False,
    ).all()

    crop_ids = [c.id for c in crops]

    actions = []
    media = []
    alerts_data = []
    if crop_ids:
        actions = db.query(ActionLog).filter(
            ActionLog.crop_instance_id.in_(crop_ids),
            ActionLog.is_deleted == False,
        ).all()
        media = db.query(MediaFile).filter(
            MediaFile.crop_instance_id.in_(crop_ids),
            MediaFile.is_deleted == False,
        ).all()
        alerts_data = db.query(Alert).filter(
            Alert.user_id == farmer_id,
            Alert.is_deleted == False,
        ).all()

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
                "effective_date": a.effective_date.isoformat() if a.effective_date else None,
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

