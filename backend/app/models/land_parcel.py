"""
LandParcel — farmer land parcel registry.
Associates farmers with physical land areas, soil types, coordinates.
"""

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class LandParcel(BaseModel):
    __tablename__ = "land_parcels"

    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    parcel_name = Column(String(255), nullable=False)
    region = Column(String(200), nullable=False)
    sub_region = Column(String(200), nullable=True)

    land_area = Column(Float, nullable=True)  # in acres
    land_area_unit = Column(String(20), default="acres")  # acres | hectares | bigha

    soil_type = Column(JSONB, default=dict)
    # {"primary": "alluvial", "ph": 6.5, "organic_matter": "medium"}

    gps_coordinates = Column(JSONB, default=dict)
    # {"lat": 28.7, "lng": 77.1, "boundary_polygon": [...]}

    irrigation_source = Column(String(100), nullable=True)
    # canal | tubewell | rainfed | drip

    def __repr__(self):
        return f"<LandParcel({self.parcel_name}@{self.region})>"
