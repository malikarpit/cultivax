"""
User Model

Users table: farmers, providers, and admins.
Fields from TDD Section 2.3.1 + soft delete (MSDD 5.10)
+ accessibility_settings (MSDD 7.14) + is_onboarded (Patch Sec 10).
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

# Lockout configuration
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class User(BaseModel):
    __tablename__ = "users"

    # Core identity
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)

    # Role: farmer | provider | admin
    role = Column(String(50), nullable=False, default="farmer", index=True)

    # Profile
    region = Column(String(100), nullable=True, index=True)
    preferred_language = Column(String(10), default="en", nullable=False)
    accessibility_settings = Column(JSONB, default=dict, nullable=False)

    # Onboarding state (Patch Module Sec 10)
    is_onboarded = Column(Boolean, default=False, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)

    # Login security — brute force protection
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # Soft delete timestamp (MSDD 5.10, TDD 2.2.1)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    crop_instances = relationship("CropInstance", back_populates="farmer", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.full_name} ({self.role})>"
