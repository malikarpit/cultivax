"""
Pydantic schemas for Weather API and Models.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class WeatherAlertItem(BaseModel):
    code: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    message: str
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class WeatherDataSchema(BaseModel):
    temperature_c: float = Field(alias="temperature")
    humidity_pct: float = Field(alias="humidity")
    wind_kph: float = Field(alias="wind_speed_kmh")
    rain_mm_24h: float = Field(alias="rainfall_mm")
    description: str
    source: str = "historical_fallback"
    is_fallback: bool = True
    uv_index: Optional[float] = None
    forecast_3d: list = []

    class Config:
        populate_by_name = True
        alias_generator = None


class WeatherRiskResponse(BaseModel):
    weather_data: WeatherDataSchema
    weather_risk_score: float = Field(ge=0.0, le=1.0)
    alerts: List[WeatherAlertItem] = []
    source: str
    is_fallback: bool
    weather_confidence: float = Field(ge=0.0, le=1.0)
    updated_at: datetime
    ttl_seconds: int
    crop_impact: Optional[str] = None
    coordinate_source: Optional[str] = None
