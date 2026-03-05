"""
Feature Flag Model

Feature flags for progressive rollout and kill switches.
MSDD Enhancement Section 13 + Development Roadmap Enhancement 6.
"""

from sqlalchemy import Column, String, Boolean, Text

from app.models.base import BaseModel


class FeatureFlag(BaseModel):
    __tablename__ = "feature_flags"

    flag_name = Column(String(100), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    # Scope: global | per_region | per_user
    scope = Column(String(20), default="global", nullable=False)
    scope_value = Column(String(100), nullable=True)  # region name or user_id

    def __repr__(self):
        return f"<FeatureFlag {self.flag_name}={self.is_enabled}>"
