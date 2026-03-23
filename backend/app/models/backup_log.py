"""
BackupLog — backup verification audit trail.
Tracks backup dates, restore tests, and results.
"""

from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone

from app.models.base import BaseModel


class BackupLog(BaseModel):
    __tablename__ = "backup_verification_logs"

    backup_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    backup_type = Column(String(50), nullable=False, default="full")
    # full | incremental | schema_only

    restore_tested = Column(Boolean, default=False, nullable=False)
    restore_date = Column(DateTime(timezone=True), nullable=True)
    result = Column(String(20), nullable=False, default="pending")
    # success | failure | pending | skipped

    notes = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<BackupLog(date={self.backup_date}, result={self.result})>"
