"""
Land Parcel Schemas

Pydantic schemas for land parcel CRUD operations.
Supports GPS boundary polygons for plot mapping.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GPSCoordinates(BaseModel):
    """GPS coordinates with optional boundary polygon."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    boundary_polygon: Optional[List[List[float]]] = Field(
        None, description="Array of [lat, lng] pairs forming a closed polygon"
    )

    @field_validator("boundary_polygon")
    @classmethod
    def validate_boundary_polygon(cls, polygon):
        if polygon is None:
            return polygon

        if len(polygon) < 3:
            raise ValueError("boundary_polygon must contain at least 3 points")

        for point in polygon:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError("Each boundary_polygon point must be [lat, lng]")
            lat, lng = point
            if lat < -90 or lat > 90:
                raise ValueError("Polygon latitude must be between -90 and 90")
            if lng < -180 or lng > 180:
                raise ValueError("Polygon longitude must be between -180 and 180")

        return polygon


class SoilInfo(BaseModel):
    """Soil composition data."""

    primary: Optional[str] = None  # alluvial | black | red | laterite | sandy | clay
    ph: Optional[float] = Field(None, ge=0, le=14)
    organic_matter: Optional[str] = None  # low | medium | high


class LandParcelCreate(BaseModel):
    """Schema for creating a new land parcel."""

    parcel_name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=200)
    sub_region: Optional[str] = Field(None, max_length=200)
    land_area: Optional[float] = Field(None, gt=0)
    land_area_unit: str = Field("acres", pattern="^(acres|hectares|bigha)$")
    soil_type: Optional[SoilInfo] = None
    gps_coordinates: GPSCoordinates
    irrigation_source: Optional[str] = Field(
        None, pattern="^(canal|tubewell|rainfed|drip|sprinkler|mixed)$"
    )


class LandParcelUpdate(BaseModel):
    """Schema for updating a land parcel."""

    parcel_name: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[str] = Field(None, max_length=200)
    sub_region: Optional[str] = Field(None, max_length=200)
    land_area: Optional[float] = Field(None, gt=0)
    land_area_unit: Optional[str] = Field(None, pattern="^(acres|hectares|bigha)$")
    soil_type: Optional[SoilInfo] = None
    gps_coordinates: Optional[GPSCoordinates] = None
    irrigation_source: Optional[str] = Field(
        None, pattern="^(canal|tubewell|rainfed|drip|sprinkler|mixed)$"
    )


class LandParcelResponse(BaseModel):
    """Schema for land parcel API response."""

    id: UUID
    farmer_id: UUID
    parcel_name: str
    region: str
    sub_region: Optional[str] = None
    land_area: Optional[float] = None
    land_area_unit: str = "acres"
    soil_type: Optional[dict] = None
    gps_coordinates: dict
    irrigation_source: Optional[str] = None
    is_deleted: bool = False
    area_from_polygon: Optional[float] = None
    centroid: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
