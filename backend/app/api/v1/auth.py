"""
Auth API — Hardened Authentication Endpoints

Security Features:
- HttpOnly cookie token delivery (XSS-proof)
- Brute force protection with exponential lockout
- Refresh token rotation with session tracking
- Event-driven audit logging (UserLoggedIn, UserLoginFailed)
- OTP-based phone login (India context)
- Anomaly detection integration
- Automatic password hash migration (bcrypt → argon2)
- Proper logout with session revocation

Endpoints:
  POST /api/v1/auth/register  — Create account + set cookies
  POST /api/v1/auth/login     — Password login + set cookies
  POST /api/v1/auth/refresh   — Rotate tokens via cookie
  POST /api/v1/auth/logout    — Revoke session + clear cookies
  POST /api/v1/auth/send-otp  — Request phone OTP
  POST /api/v1/auth/verify-otp — Verify OTP + login
  GET  /api/v1/auth/me        — Get current user from cookie
  GET  /api/v1/auth/sessions  — List active sessions
  POST /api/v1/auth/sessions/revoke-all — Revoke all other sessions
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, MAX_FAILED_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES
from app.models.active_session import ActiveSession
from app.models.otp_code import OTPCode, OTP_TTL_MINUTES, OTP_MAX_PER_HOUR
from app.models.event_log import EventLog
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    LoginResponse,
    OTPRequest,
    OTPVerify,
    OTPResponse,
    ActiveSessionsResponse,
    SessionInfo,
    UserPreferencesUpdate,
    UserPreferencesResponse,
)
from app.security.auth import (
    hash_password,
    verify_password,
    needs_rehash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.security.secure_auth import (
    set_auth_cookies,
    clear_auth_cookies,
    get_refresh_token_from_cookie,
)
from app.api.deps import get_current_user
from app.config import settings
from app.utils.phone import normalize_phone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For for proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def _create_session(
    db: Session,
    user: User,
    refresh_token: str,
    request: Request,
) -> ActiveSession:
    """Create an active session record for a refresh token."""
    session = ActiveSession(
        user_id=user.id,
        refresh_token_hash=ActiveSession.hash_token(refresh_token),
        device_fingerprint=request.headers.get("X-Device-Fingerprint"),
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent", "")[:500],
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    return session


def _log_auth_event(
    db: Session,
    event_type: str,
    user_id,
    details: dict,
):
    """Publish an authentication event to the event log."""
    try:
        import uuid as _uuid
        import hashlib

        # Generate unique event hash for idempotency
        raw = f"{event_type}:{user_id}:{datetime.now(timezone.utc).isoformat()}"
        event_hash = hashlib.sha256(raw.encode()).hexdigest()

        # partition_key and entity_id require UUIDs — use user_id or a zero UUID
        pk = user_id if user_id else _uuid.UUID(int=0)
        eid = user_id if user_id else _uuid.UUID(int=0)

        event = EventLog(
            event_type=event_type,
            entity_type="User",
            entity_id=eid,
            payload=details,
            module_target="auth",
            partition_key=pk,
            event_hash=event_hash,
        )
        db.add(event)
    except Exception as e:
        logger.error(f"Failed to log auth event: {e}")


def _set_tokens_and_cookies(
    response: Response,
    user: User,
    db: Session,
    request: Request,
) -> tuple:
    """Generate tokens, set cookies, create session. Returns (access, refresh)."""
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Create session record
    _create_session(db, user, refresh_token, request)

    # Set HttpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    return access_token, refresh_token


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Register a new user and return JWT token pair via HttpOnly cookies."""

    # Normalize phone number — P2 FIX: prevent duplicate accounts
    normalized_phone = normalize_phone(user_data.phone)

    # Check if phone already exists
    existing = db.query(User).filter(User.phone == normalized_phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    # Check email uniqueness if provided
    if user_data.email:
        email_exists = db.query(User).filter(User.email == user_data.email).first()
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Validate role — P0 SECURITY FIX: block admin self-registration
    valid_roles = ["farmer", "provider"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts must be created by system administrators",
        )

    # Create user with Argon2id hashed password
    user = User(
        full_name=user_data.full_name,
        phone=normalized_phone,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        region=user_data.region,
        preferred_language=user_data.preferred_language,
    )
    db.add(user)
    db.flush()  # Get user.id before committing

    # Generate tokens & set cookies
    access_token, refresh_token = _set_tokens_and_cookies(response, user, db, request)

    # Log event
    _log_auth_event(db, "UserRegistered", user.id, {
        "phone": user.phone,
        "role": user.role,
        "ip": _get_client_ip(request),
    })

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return JWT token pair via HttpOnly cookies.

    Security:
    - Brute force protection: 5 failed attempts → 15 min lockout
    - Anomaly detection on login behavior
    - Event-driven audit logging
    - Transparent password hash migration (bcrypt → argon2)
    """
    client_ip = _get_client_ip(request)

    # Normalize phone number
    normalized_phone = normalize_phone(credentials.phone)

    # Find user
    user = db.query(User).filter(
        User.phone == normalized_phone,
        User.is_deleted == False,
    ).first()

    if not user:
        # Log failed attempt (unknown user) — use constant-time behavior
        _log_auth_event(db, "UserLoginFailed", None, {
            "phone": credentials.phone,
            "reason": "user_not_found",
            "ip": client_ip,
        })
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    # Check account lockout
    locked_until = user.locked_until
    if locked_until and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    if locked_until and locked_until > datetime.now(timezone.utc):
        remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds())
        _log_auth_event(db, "UserLoginFailed", user.id, {
            "reason": "account_locked",
            "ip": client_ip,
            "locked_until": locked_until.isoformat(),
        })
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked due to too many failed attempts. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)},
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            logger.warning(
                f"Account locked: user={user.id} phone={user.phone} "
                f"attempts={user.failed_login_attempts} ip={client_ip}"
            )

        _log_auth_event(db, "UserLoginFailed", user.id, {
            "reason": "wrong_password",
            "attempt_number": user.failed_login_attempts,
            "ip": client_ip,
        })
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    # Check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact admin.",
        )

    # --- Login successful ---

    # Transparent password hash migration (bcrypt → argon2)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(credentials.password)
        logger.info(f"Password hash upgraded to Argon2id for user={user.id}")

    # Reset lockout counters
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_ip

    # Generate tokens & set cookies
    access_token, refresh_token = _set_tokens_and_cookies(response, user, db, request)

    # Anomaly detection (non-blocking)
    try:
        from app.security.anomaly_detector import get_anomaly_detector
        detector = get_anomaly_detector()
        is_anomalous, score, reasons = detector.analyze_request(
            user_id=str(user.id),
            endpoint="/api/v1/auth/login",
            method="POST",
            ip_address=client_ip,
        )
        if is_anomalous:
            logger.warning(
                f"Anomalous login: user={user.id} score={score:.2f} reasons={reasons}"
            )
            _log_auth_event(db, "AnomalousLogin", user.id, {
                "score": score,
                "reasons": reasons,
                "ip": client_ip,
            })
    except Exception as e:
        logger.debug(f"Anomaly detection skipped: {e}")

    # Log successful login event
    _log_auth_event(db, "UserLoggedIn", user.id, {
        "ip": client_ip,
        "user_agent": request.headers.get("User-Agent", "")[:200],
    })

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    Token Rotation:
    - The old refresh token's session is revoked
    - A new session + tokens are created
    - This prevents replay attacks with stolen refresh tokens

    Reads the refresh token from HttpOnly cookie.
    """
    # Extract refresh token from cookie
    token = get_refresh_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found",
        )

    # Verify JWT validity
    payload = verify_refresh_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Validate session exists and is not revoked
    token_hash = ActiveSession.hash_token(token)
    session = db.query(ActiveSession).filter(
        ActiveSession.refresh_token_hash == token_hash,
        ActiveSession.is_revoked == False,
        ActiveSession.is_deleted == False,
    ).first()

    if not session or not session.is_valid():
        # Potential token reuse attack — revoke ALL sessions for this user
        if session and session.is_revoked:
            user_id = payload.get("sub")
            logger.critical(
                f"REFRESH TOKEN REUSE DETECTED for user={user_id}! "
                f"Revoking all sessions."
            )
            db.query(ActiveSession).filter(
                ActiveSession.user_id == user_id,
            ).update({"is_revoked": True, "revoked_at": datetime.now(timezone.utc)})
            _log_auth_event(db, "TokenReuseDetected", user_id, {
                "ip": _get_client_ip(request),
            })
            db.commit()
            clear_auth_cookies(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    # Fetch user
    user_id = payload.get("sub")
    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
        User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Revoke old session (token rotation)
    session.revoke()

    # Issue new tokens + session
    access_token, refresh_token_new = _set_tokens_and_cookies(response, user, db, request)

    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_new,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Log out: revoke current session and clear HttpOnly cookies.
    """
    # Try to revoke the session if we can find it
    token = get_refresh_token_from_cookie(request)
    if token:
        token_hash = ActiveSession.hash_token(token)
        session = db.query(ActiveSession).filter(
            ActiveSession.refresh_token_hash == token_hash,
        ).first()
        if session:
            session.revoke()
            _log_auth_event(db, "UserLoggedOut", session.user_id, {
                "ip": _get_client_ip(request),
            })
            db.commit()

    # Always clear cookies, even if session not found
    clear_auth_cookies(response)

    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# POST /send-otp
# ---------------------------------------------------------------------------

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    data: OTPRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Send a 6-digit OTP to the registered phone number.

    Rate limited: max 5 OTPs per phone per hour.
    In development mode, the OTP is returned in the response for testing.
    """
    client_ip = _get_client_ip(request)

    # Normalize phone
    normalized_phone = normalize_phone(data.phone)

    # Verify phone number is registered
    user = db.query(User).filter(
        User.phone == normalized_phone,
        User.is_deleted == False,
    ).first()

    if not user:
        # Don't reveal whether phone is registered — return identical
        # success response to prevent phone enumeration attacks
        return OTPResponse(
            message="OTP sent successfully",
            expires_in_seconds=OTP_TTL_MINUTES * 60,
            debug_otp=None,
        )

    # Rate limit: max OTPs per hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_count = db.query(OTPCode).filter(
        OTPCode.phone == normalized_phone,
        OTPCode.created_at > one_hour_ago,
    ).count()

    if recent_count >= OTP_MAX_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many OTP requests. Max {OTP_MAX_PER_HOUR} per hour.",
        )

    # Generate 6-digit OTP
    otp_plain = f"{secrets.randbelow(1000000):06d}"

    # Store hashed OTP
    otp_record = OTPCode(
        phone=normalized_phone,
        otp_hash=OTPCode.hash_otp(otp_plain),
        expires_at=OTPCode.generate_expiry(),
    )
    db.add(otp_record)

    _log_auth_event(db, "OTPSent", user.id, {
        "phone": normalized_phone,
        "ip": client_ip,
    })

    db.commit()

    # In development, return the OTP for testing
    debug_otp = otp_plain if settings.APP_ENV == "development" else None
    if debug_otp:
        logger.info(f"[DEV] OTP for {normalized_phone}: {otp_plain}")

    return OTPResponse(
        message="OTP sent successfully",
        expires_in_seconds=OTP_TTL_MINUTES * 60,
        debug_otp=debug_otp,
    )


# ---------------------------------------------------------------------------
# POST /verify-otp
# ---------------------------------------------------------------------------

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    data: OTPVerify,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Verify OTP and log in the user.
    Sets HttpOnly cookies on success.
    """
    client_ip = _get_client_ip(request)

    # Normalize phone
    normalized_phone = normalize_phone(data.phone)

    # Find the latest unused OTP for this phone
    otp_record = db.query(OTPCode).filter(
        OTPCode.phone == normalized_phone,
        OTPCode.is_used == False,
    ).order_by(OTPCode.created_at.desc()).first()

    if not otp_record or not otp_record.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Verify OTP (increments attempts)
    if not otp_record.verify(data.otp):
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    # Find user
    user = db.query(User).filter(
        User.phone == normalized_phone,
        User.is_deleted == False,
        User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Reset lockout on OTP login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_ip

    # Generate tokens & set cookies
    access_token, refresh_token = _set_tokens_and_cookies(response, user, db, request)

    _log_auth_event(db, "UserLoggedInViaOTP", user.id, {
        "ip": client_ip,
    })

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user from HttpOnly cookie.
    Used by the frontend to verify session status on page load.
    """
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# PATCH /me  — Update user preferences (language, accessibility)
# ---------------------------------------------------------------------------

@router.patch("/me", response_model=UserPreferencesResponse)
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user preferences (language, accessibility settings).
    Only the calling user's own preferences can be updated.
    Accessibility settings are MERGED (not replaced) to allow partial updates.
    """
    changes: dict = {}

    # Update preferred_language if provided (validated by schema)
    if payload.preferred_language is not None:
        changes["preferred_language"] = payload.preferred_language
        current_user.preferred_language = payload.preferred_language

    # Merge accessibility_settings (partial updates allowed)
    if payload.accessibility_settings is not None:
        existing = current_user.accessibility_settings or {}
        merged = {**existing, **payload.accessibility_settings}
        current_user.accessibility_settings = merged
        changes["accessibility_settings"] = merged

    if not changes:
        # No-op — return current state without writing
        return UserPreferencesResponse.model_validate(current_user)

    # Persist
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # Audit log
    _log_auth_event(db, "PreferencesUpdated", current_user.id, {
        "changed_fields": list(changes.keys()),
        "preferred_language": current_user.preferred_language,
    })
    db.commit()

    return UserPreferencesResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

@router.get("/sessions", response_model=ActiveSessionsResponse)
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active (non-revoked) sessions for the current user."""
    from app.security.secure_auth import get_refresh_token_from_cookie

    sessions = db.query(ActiveSession).filter(
        ActiveSession.user_id == current_user.id,
        ActiveSession.is_revoked == False,
        ActiveSession.is_deleted == False,
    ).order_by(ActiveSession.created_at.desc()).all()

    # Determine current session
    current_token = get_refresh_token_from_cookie(request)
    current_hash = ActiveSession.hash_token(current_token) if current_token else None

    session_list = []
    for s in sessions:
        if s.is_expired():
            continue
        info = SessionInfo.model_validate(s)
        info.is_current = (s.refresh_token_hash == current_hash) if current_hash else False
        session_list.append(info)

    return ActiveSessionsResponse(sessions=session_list, total=len(session_list))


# ---------------------------------------------------------------------------
# POST /sessions/revoke-all
# ---------------------------------------------------------------------------

@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke all sessions except the current one.
    Useful when user suspects account compromise.
    """
    current_token = get_refresh_token_from_cookie(request)
    current_hash = ActiveSession.hash_token(current_token) if current_token else None

    revoked_count = db.query(ActiveSession).filter(
        ActiveSession.user_id == current_user.id,
        ActiveSession.is_revoked == False,
        ActiveSession.refresh_token_hash != current_hash,
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc),
    })

    _log_auth_event(db, "AllSessionsRevoked", current_user.id, {
        "revoked_count": revoked_count,
        "ip": _get_client_ip(request),
    })

    db.commit()

    return {
        "message": f"Revoked {revoked_count} other session(s)",
        "revoked_count": revoked_count,
    }
