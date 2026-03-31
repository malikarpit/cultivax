"""
User & Auth Schemas

Pydantic schemas for user registration, login, JWT tokens,
OTP authentication, session management, and user preferences.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import re

SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "mr"]
ALLOWED_ACCESSIBILITY_KEYS = {"largeText", "highContrast", "reducedMotion", "theme", "sidebarPinned"}


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Minimum 8 characters with at least one uppercase letter and one digit",
    )
    role: str = "farmer"
    region: Optional[str] = None
    preferred_language: str = "en"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1)
    device_fingerprint: Optional[str] = Field(None, description="Client device fingerprint for session tracking")


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    email: Optional[str]
    role: str
    region: Optional[str]
    preferred_language: str
    accessibility_settings: Dict[str, Any]
    is_onboarded: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    preferred_language: Optional[str] = None
    accessibility_settings: Optional[Dict[str, Any]] = None


class UserPreferencesUpdate(BaseModel):
    """Schema for PATCH /auth/me — update language and accessibility settings only."""
    preferred_language: Optional[str] = Field(
        None,
        description=f"BCP-47 language code. Supported: {SUPPORTED_LANGUAGES}",
    )
    accessibility_settings: Optional[Dict[str, Any]] = Field(
        None,
        description=f"Accessibility settings. Allowed keys: {ALLOWED_ACCESSIBILITY_KEYS}",
    )

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{v}'. Must be one of: {SUPPORTED_LANGUAGES}")
        return v

    @field_validator("accessibility_settings")
    @classmethod
    def validate_a11y_keys(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is not None:
            bad_keys = set(v.keys()) - ALLOWED_ACCESSIBILITY_KEYS
            if bad_keys:
                raise ValueError(f"Invalid accessibility keys: {bad_keys}. Allowed: {ALLOWED_ACCESSIBILITY_KEYS}")
        return v


class UserPreferencesResponse(BaseModel):
    """Response after PATCH /auth/me — preference fields only."""
    id: UUID
    preferred_language: str
    accessibility_settings: Dict[str, Any]
    is_onboarded: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response for login/register — tokens are set in HttpOnly cookies.
    The access_token and refresh_token fields are kept for backward
    compatibility during the transition period but will be deprecated."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse


class LoginResponse(BaseModel):
    """Cookie-based login response. Tokens are in HttpOnly cookies, not body."""
    message: str = "Login successful"
    user: UserResponse


# --- OTP Schemas ---

class OTPRequest(BaseModel):
    """Request to send an OTP to a phone number."""
    phone: str = Field(..., min_length=10, max_length=20)


class OTPVerify(BaseModel):
    """Verify an OTP code for phone-based login."""
    phone: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    device_fingerprint: Optional[str] = None


class OTPResponse(BaseModel):
    """Response after requesting OTP."""
    message: str
    expires_in_seconds: int = 300  # 5 minutes
    # In development, we include the OTP for testing
    debug_otp: Optional[str] = None


# --- Session Schemas ---

class SessionInfo(BaseModel):
    """Information about an active session."""
    id: UUID
    device_fingerprint: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


class ActiveSessionsResponse(BaseModel):
    """List of active sessions for a user."""
    sessions: List[SessionInfo]
    total: int
