"""
API Dependencies

FastAPI dependency injection for authentication and authorization.

Security Features:
- Dual token extraction: HttpOnly cookies (preferred) + Bearer header (fallback)
- Role-based access control (RBAC) enforcement
- Automatic password hash migration on login
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.security.auth import verify_token
from app.security.secure_auth import get_token_from_request
from app.models.user import User

# HTTPBearer is optional — we prefer cookies but support headers for API clients
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: extracts and validates JWT, returns the current user.

    Token extraction priority:
    1. HttpOnly cookie (most secure — immune to XSS)
    2. Authorization: Bearer header (for API clients / backward compat)

    Raises 401 if token is invalid or user not found.
    """
    # Extract token from cookie or header
    token = get_token_from_request(request)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    # Validate role claim exists in token
    token_role = payload.get("role")
    if token_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing role claim",
        )

    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )

    user = db.query(User).filter(
        User.id == user_uuid,
        User.is_deleted == False,
        User.is_active == True,
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Cross-verify token role matches database role (prevent stale tokens)
    if user.role != token_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token role does not match current user role. Please re-login.",
        )

    return user


def require_role(allowed_roles: List[str]):
    """
    Dependency factory: ensures current user has one of the allowed roles.

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role(["admin"]))])
        async def list_users(...):
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized. Required: {allowed_roles}",
            )
        return current_user
    return role_checker
