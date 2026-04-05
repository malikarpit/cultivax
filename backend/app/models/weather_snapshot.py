"""
Weather Snapshot Model

Persists weather data for regions and specific coordinates to reduce
external API dependency. Uses BaseModel for soft-delete, timestamps,
and UUID PK consistency.
"""

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class WeatherSnapshot(BaseModel):
    __tablename__ = "weather_snapshots"

    location_key = Column(
        String, index=True, nullable=False
    )  # e.g. "geohash_w3q2" or "lat_lng_bucket"
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    provider_source = Column(
        String, nullable=False
    )  # "openweathermap", "historical_fallback", "mock"
    weather_payload_json = Column(JSON, nullable=False)
    weather_risk_score = Column(Float, nullable=False)
    alerts_json = Column(JSON, nullable=False, default=[])

    ttl_seconds = Column(Integer, nullable=False, default=600)

    captured_at = Column(DateTime(timezone=True), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
