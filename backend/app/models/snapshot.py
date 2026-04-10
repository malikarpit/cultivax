"""
Crop Instance Snapshot Model

Stores periodic snapshots for incremental replay optimization.
TDD Section 2.3.3.
"""

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CropInstanceSnapshot(BaseModel):
    __tablename__ = "crop_instance_snapshots"

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Snapshot data contains full crop state at this point
    snapshot_data = Column(JSONB, nullable=False)

    # How many actions were processed when this snapshot was taken
    action_count_at_snapshot = Column(Integer, nullable=False)

    # Snapshot version for compatibility
    snapshot_version = Column(Integer, default=1, nullable=False)

    # Relationships
    crop_instance = relationship("CropInstance", back_populates="snapshots")

    def __repr__(self):
        return f"<Snapshot actions={self.action_count_at_snapshot}>"
