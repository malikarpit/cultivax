"""
Authentication Utilities

JWT token creation/verification and password hashing.
Uses python-jose for JWT and passlib+argon2 for passwords.

Security Upgrades (2026):
- Argon2id password hashing (memory-hard, GPU-resistant)
- Short-lived access tokens (15 minutes)
- Refresh tokens with rotation support
- Token type discrimination (access vs refresh)
- JTI (JWT ID) for token revocation tracking
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context — Argon2id (preferred), bcrypt (fallback/migration)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated=["bcrypt"],  # Auto-rehash bcrypt -> argon2 on verify
    argon2__rounds=4,
    argon2__memory_cost=65536,  # 64 MB
    argon2__parallelism=2,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    If the hash is bcrypt (legacy), passlib will verify it and
    flag it for automatic rehashing to Argon2id on next login.
    """
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be upgraded (bcrypt -> argon2).
    Call after successful verify() to transparently upgrade old hashes.
    """
    return pwd_context.needs_update(hashed_password)


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived JWT access token (default: 15 minutes).

    Claims:
        sub: user_id (string UUID)
        role: user role
        token_type: "access"
        jti: unique token ID for revocation
        iat: issued at
        exp: expiration
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "access",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT access token.

    Returns:
        Decoded payload dict, or None if invalid/expired/wrong type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Ensure it's an access token (not a refresh token used as access)
        if payload.get("token_type") not in (None, "access"):
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(data: Dict) -> str:
    """
    Create a long-lived JWT refresh token (default: 7 days).

    The refresh token includes a unique JTI that is stored (hashed)
    in the active_sessions table for revocation support.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "refresh",
        "jti": jti,
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_refresh_token(token: str) -> Optional[Dict]:
    """
    Verify a refresh token — must have token_type='refresh'.

    Returns:
        Decoded payload dict, or None if invalid/expired/wrong type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
