"""
Weather API — Proxy endpoint for frontend weather data

Exposes weather data from the existing WeatherService to the frontend.
Falls back to realistic mock data when no API key is configured.

GET /api/v1/weather?lat={lat}&lng={lng}
GET /api/v1/weather/risk?crop_id={id}
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.crop_instance import CropInstance
from app.models.land_parcel import LandParcel
from app.models.user import User
from app.schemas.weather import WeatherDataSchema, WeatherRiskResponse
from app.services.weather.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/", response_model=WeatherRiskResponse)
async def get_weather(
    lat: float | None = Query(None, ge=-90, le=90, description="Latitude"),
    lng: float | None = Query(None, ge=-180, le=180, description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current weather + 3-day forecast for given coordinates.
    Leverages WeatherService which uses caching and DB snapshots.
    """
    weather_service = WeatherService()

    try:
        # Fallback to user region default if coordinates missing
        if lat is None or lng is None:
            defaults = _region_coords(current_user.region)
            lat = lat if lat is not None else defaults.get("lat", 28.61)
            lng = lng if lng is not None else defaults.get("lng", 77.23)

        # Resolve weather risk using the new db-backed service
        result = await weather_service.get_weather_risk(
            db=db,
            region=current_user.region or "default",
            latitude=lat,
            longitude=lng,
        )

        return result

    except Exception as e:
        logger.error(f"Weather API failed: {e}")
        raise HTTPException(status_code=503, detail="Weather service unavailable.")


@router.get("/risk", response_model=WeatherRiskResponse)
async def get_crop_weather_risk(
    crop_id: UUID = Query(..., description="Crop instance ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get weather risk analysis for a specific crop.
    Looks up the crop's linked land parcel for coordinates,
    then fetches weather and computes crop-specific impact.
    """
    crop = (
        db.query(CropInstance)
        .filter(
            CropInstance.id == crop_id,
            CropInstance.farmer_id == current_user.id,
            CropInstance.is_deleted == False,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    # Try to get coordinates from linked land parcel
    lat, lng = None, None
    coordinate_source = "region_fallback"
    if hasattr(crop, "land_parcel_id") and crop.land_parcel_id:
        parcel = (
            db.query(LandParcel).filter(LandParcel.id == crop.land_parcel_id).first()
        )
        if parcel and parcel.gps_coordinates:
            centroid = parcel.gps_coordinates.get("centroid", {})
            lat = centroid.get("lat") or parcel.gps_coordinates.get("lat")
            lng = centroid.get("lng") or parcel.gps_coordinates.get("lng")
            if lat is not None and lng is not None:
                coordinate_source = "parcel_gps"

    # Fallback: use region-based defaults for common Indian ag regions
    if lat is None or lng is None:
        defaults = _region_coords(crop.region)
        lat, lng = defaults["lat"], defaults["lng"]

    weather_service = WeatherService()
    try:
        result = await weather_service.get_weather_risk(
            db=db,
            region=crop.region,
            latitude=lat,
            longitude=lng,
        )

        # Add context about the coordinate resolution strategy back into the payload
        result["coordinate_source"] = coordinate_source

        # Inject custom crop impact metadata into the response
        risk = result.get("weather_risk_score", 0.0)
        result["crop_impact"] = _crop_impact_text(risk, crop.crop_type, crop.stage)

        return result

    except Exception as e:
        logger.error(f"Weather crop API failed: {e}")
        raise HTTPException(status_code=503, detail="Weather service unavailable.")


def _region_coords(region: str) -> dict:
    """Default GPS coordinates for common Indian agricultural regions."""
    defaults = {
        "punjab": {"lat": 30.9, "lng": 75.85},
        "haryana": {"lat": 29.05, "lng": 76.08},
        "rajasthan": {"lat": 27.02, "lng": 74.22},
        "up": {"lat": 27.18, "lng": 79.98},
        "uttar pradesh": {"lat": 27.18, "lng": 79.98},
        "madhya pradesh": {"lat": 23.47, "lng": 77.94},
        "mp": {"lat": 23.47, "lng": 77.94},
        "maharashtra": {"lat": 19.66, "lng": 75.30},
        "karnataka": {"lat": 15.31, "lng": 75.71},
        "andhra pradesh": {"lat": 15.91, "lng": 79.74},
        "tamil nadu": {"lat": 11.13, "lng": 78.66},
        "gujarat": {"lat": 22.26, "lng": 71.19},
        "bihar": {"lat": 25.10, "lng": 85.31},
        "west bengal": {"lat": 22.99, "lng": 87.85},
        "odisha": {"lat": 20.94, "lng": 84.80},
        "telangana": {"lat": 17.12, "lng": 79.02},
    }
    key = (region or "").lower().strip()
    return defaults.get(key, {"lat": 28.61, "lng": 77.23})  # Default: Delhi


def _crop_impact_text(risk: float, crop_type: str, stage: str) -> str:
    """Generate human-readable crop impact text from risk score."""
    crop = (crop_type or "crop").capitalize()
    stage_text = f" ({stage} stage)" if stage else ""

    if risk < 0.2:
        return f"Low risk — favorable conditions for {crop}{stage_text}"
    elif risk < 0.4:
        return f"Moderate conditions for {crop}{stage_text}. Monitor closely."
    elif risk < 0.6:
        return (
            f"Elevated risk for {crop}{stage_text}. " f"Consider protective measures."
        )
    else:
        return f"High risk for {crop}{stage_text}! " f"Immediate attention recommended."
