"""
OTP Code Model

Stores one-time passwords for phone-based authentication.
OTPs are hashed before storage and have a short TTL (5 minutes).

Security Features:
- OTP stored as SHA-256 hash (never plaintext)
- Max 3 verification attempts per OTP
- Auto-expires after 5 minutes
- Rate limited: max 5 OTPs per phone per hour
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

# OTP configuration constants
OTP_TTL_MINUTES = 5
OTP_MAX_ATTEMPTS = 3
OTP_MAX_PER_HOUR = 5


class OTPCode(BaseModel):
    __tablename__ = "otp_codes"

    # Phone number this OTP was sent to
    phone = Column(String(20), nullable=False, index=True)

    # SHA-256 hash of the OTP code
    otp_hash = Column(String(64), nullable=False)

    # Tracking
    attempts = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash an OTP code using SHA-256."""
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def generate_expiry() -> datetime:
        """Generate an expiry timestamp (now + TTL)."""
        return datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)

    def is_expired(self) -> bool:
        """Check if this OTP has expired."""
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires

    def is_valid(self) -> bool:
        """Check if this OTP is still usable."""
        return (
            not self.is_used
            and not self.is_expired()
            and self.attempts < OTP_MAX_ATTEMPTS
        )

    def verify(self, otp_plain: str) -> bool:
        """
        Verify an OTP against the stored hash.
        Increments attempt counter regardless of result.
        """
        self.attempts += 1
        if not self.is_valid():
            return False
        if self.otp_hash == self.hash_otp(otp_plain):
            self.is_used = True
            self.used_at = datetime.now(timezone.utc)
            return True
        return False

    def __repr__(self):
        return f"<OTPCode phone={self.phone} used={self.is_used}>"
