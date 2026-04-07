"""
Land Parcel Service

Business logic for land parcel CRUD operations.
Includes polygon area calculation and centroid computation.
"""

import logging
import math
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.land_parcel import LandParcel
from app.models.user import User
from app.schemas.land_parcel import LandParcelCreate, LandParcelUpdate

logger = logging.getLogger(__name__)


class LandParcelService:
    """Service for land parcel management with geospatial computations."""

    def __init__(self, db: Session):
        self.db = db

    def create_parcel(self, farmer: User, data: LandParcelCreate) -> LandParcel:
        """Create a new land parcel with auto-computed geo fields."""
        gps_data = data.gps_coordinates.model_dump()
        soil_data = data.soil_type.model_dump() if data.soil_type else {}

        parcel = LandParcel(
            farmer_id=farmer.id,
            parcel_name=data.parcel_name,
            region=data.region,
            sub_region=data.sub_region,
            land_area=data.land_area,
            land_area_unit=data.land_area_unit,
            soil_type=soil_data,
            gps_coordinates=gps_data,
            irrigation_source=data.irrigation_source,
        )

        # Auto-compute area from polygon if available and area not provided
        polygon = gps_data.get("boundary_polygon")
        if polygon and len(polygon) >= 3:
            computed_area = self._polygon_area_acres(polygon)
            if not data.land_area:
                parcel.land_area = round(computed_area, 2)
                parcel.land_area_unit = "acres"
            # Store computed area in gps_coordinates for reference
            gps_data["computed_area_acres"] = round(computed_area, 2)
            gps_data["centroid"] = self._polygon_centroid(polygon)
            parcel.gps_coordinates = gps_data

        self.db.add(parcel)
        self.db.commit()
        self.db.refresh(parcel)

        logger.info(
            f"Created land parcel '{parcel.parcel_name}' for farmer {farmer.id} "
            f"in {parcel.region} ({parcel.land_area} {parcel.land_area_unit})"
        )
        return parcel

    def list_parcels(
        self, farmer_id: UUID, include_deleted: bool = False
    ) -> List[LandParcel]:
        """List all parcels for a farmer."""
        query = self.db.query(LandParcel).filter(LandParcel.farmer_id == farmer_id)
        if not include_deleted:
            query = query.filter(LandParcel.is_deleted == False)
        return query.order_by(LandParcel.created_at.desc()).all()

    def get_parcel(self, parcel_id: UUID, farmer_id: UUID) -> Optional[LandParcel]:
        """Get a specific parcel by ID (owned by farmer)."""
        return (
            self.db.query(LandParcel)
            .filter(
                LandParcel.id == parcel_id,
                LandParcel.farmer_id == farmer_id,
                LandParcel.is_deleted == False,
            )
            .first()
        )

    def update_parcel(
        self, parcel_id: UUID, farmer_id: UUID, data: LandParcelUpdate
    ) -> Optional[LandParcel]:
        """Update a land parcel."""
        parcel = self.get_parcel(parcel_id, farmer_id)
        if not parcel:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle GPS coordinates update with recomputation
        if "gps_coordinates" in update_data and update_data["gps_coordinates"]:
            gps_data = update_data["gps_coordinates"]
            polygon = gps_data.get("boundary_polygon")
            if polygon and len(polygon) >= 3:
                gps_data["computed_area_acres"] = round(
                    self._polygon_area_acres(polygon), 2
                )
                gps_data["centroid"] = self._polygon_centroid(polygon)
            update_data["gps_coordinates"] = gps_data

        # Handle soil_type serialization
        if "soil_type" in update_data and update_data["soil_type"]:
            if hasattr(update_data["soil_type"], "model_dump"):
                update_data["soil_type"] = update_data["soil_type"].model_dump()

        for key, value in update_data.items():
            setattr(parcel, key, value)

        self.db.commit()
        self.db.refresh(parcel)

        logger.info(f"Updated land parcel {parcel_id}")
        return parcel

    def delete_parcel(self, parcel_id: UUID, farmer_id: UUID) -> bool:
        """Soft-delete a land parcel."""
        parcel = self.get_parcel(parcel_id, farmer_id)
        if not parcel:
            return False

        parcel.is_deleted = True
        self.db.commit()

        logger.info(f"Soft-deleted land parcel {parcel_id}")
        return True

    def restore_parcel(self, parcel_id: UUID, farmer_id: UUID) -> bool:
        """Restore a previously soft-deleted land parcel."""
        parcel = (
            self.db.query(LandParcel)
            .filter(
                LandParcel.id == parcel_id,
                LandParcel.farmer_id == farmer_id,
                LandParcel.is_deleted == True,
            )
            .first()
        )
        if not parcel:
            return False

        parcel.is_deleted = False
        parcel.deleted_at = None
        self.db.commit()

        logger.info(f"Restored land parcel {parcel_id}")
        return True

    # -------------------------------------------------------------------------
    # Geospatial Computations
    # -------------------------------------------------------------------------

    @staticmethod
    def _polygon_area_acres(polygon: List[List[float]]) -> float:
        """
        Calculate the area of a GPS polygon in acres.

        Uses the Shoelace formula on projected coordinates.
        Accurate for small areas (typical farm fields).

        Args:
            polygon: List of [lat, lng] pairs

        Returns:
            Area in acres
        """
        if len(polygon) < 3:
            return 0.0

        # Convert to radians and use equirectangular projection
        # Reference point: first vertex
        ref_lat = math.radians(polygon[0][0])

        # Convert GPS to meters using equirectangular approximation
        R = 6371000  # Earth radius in meters
        points_m = []
        for point in polygon:
            lat_r = math.radians(point[0])
            lng_r = math.radians(point[1])
            x = R * (lng_r - math.radians(polygon[0][1])) * math.cos(ref_lat)
            y = R * (lat_r - ref_lat)
            points_m.append((x, y))

        # Shoelace formula for area in square meters
        n = len(points_m)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points_m[i][0] * points_m[j][1]
            area -= points_m[j][0] * points_m[i][1]
        area_sqm = abs(area) / 2.0

        # Convert square meters to acres (1 acre = 4046.86 sq meters)
        return area_sqm / 4046.86

    @staticmethod
    def _polygon_centroid(polygon: List[List[float]]) -> dict:
        """Calculate the centroid of a polygon."""
        if not polygon:
            return {"lat": 0, "lng": 0}

        lat_sum = sum(p[0] for p in polygon)
        lng_sum = sum(p[1] for p in polygon)
        n = len(polygon)

        return {
            "lat": round(lat_sum / n, 6),
            "lng": round(lng_sum / n, 6),
        }
