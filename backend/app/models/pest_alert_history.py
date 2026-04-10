"""
Pest Alert History Model

Historical pest detection records for crop instances.
MSDD Section 6 Enhancement.
"""

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class PestAlertHistory(BaseModel):
    __tablename__ = "pest_alert_history"

    crop_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_instances.id"),
        nullable=False,
        index=True,
    )

    # Pest details
    pest_type = Column(String(200), nullable=False)
    # aphids | bollworm | stem_borer | leaf_blight | rust | mildew | etc.

    alert_level = Column(String(50), nullable=False, default="Low")
    # Low | Medium | High | Critical

    # Detection source
    detected_by = Column(String(100), nullable=False, default="manual")
    # manual | edge_ai | backend_ml | media_analysis

    # Confidence of detection
    confidence = Column(Float, nullable=True)  # 0.0 - 1.0

    # Optional pest density index
    pest_density_index = Column(Float, nullable=True)

    # Additional details
    description = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<PestAlertHistory {self.pest_type} [{self.alert_level}]>"
