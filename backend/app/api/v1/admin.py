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
