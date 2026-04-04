"""
Active Session Model

Tracks active user sessions for token revocation, logout,
and device management. Each refresh token is associated with
a session record — when revoked, the refresh token becomes invalid.

Security Features:
- Refresh tokens are stored as SHA-256 hashes (never plaintext)
- Device fingerprinting for anomaly detection
- IP tracking for geographic anomaly detection
"""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ActiveSession(BaseModel):
    __tablename__ = "active_sessions"

    # Link to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hashed refresh token (SHA-256) — never store plaintext
    refresh_token_hash = Column(String(64), nullable=False, unique=True, index=True)

    # Device & location metadata
    device_fingerprint = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)

    # Session lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="sessions")

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a refresh token using SHA-256 for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def revoke(self) -> None:
        """Mark this session as revoked."""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires

    def is_valid(self) -> bool:
        """Check if the session is still valid (not revoked, not expired)."""
        return not self.is_revoked and not self.is_expired()

    def __repr__(self):
        return f"<ActiveSession user={self.user_id} revoked={self.is_revoked}>"
