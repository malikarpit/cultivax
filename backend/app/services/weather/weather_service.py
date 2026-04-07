"""
Weather Service — External Weather API Integration & Caching

Fetches weather data, computes weather-based risk scores,
utilizes DB caching via WeatherRepository, and emits Events.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.repositories.weather_repository import WeatherRepository
from app.schemas.weather import WeatherAlertItem, WeatherDataSchema
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.services.event_dispatcher.event_types import NotificationEvents

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Historical baseline risk values by region
HISTORICAL_BASELINES = {
    "default": 0.3,
    "arid": 0.5,
    "tropical": 0.35,
    "temperate": 0.25,
    "semi-arid": 0.45,
}

TEMP_HIGH_THRESHOLD = 42.0  # °C
TEMP_LOW_THRESHOLD = 5.0  # °C
RAIN_HEAVY_THRESHOLD = 50.0  # mm/day
WIND_HIGH_THRESHOLD = 60.0  # km/h

# Cache TTL overrides
TTL_CURRENT_WEATHER = 600   # 10m
TTL_FORECAST = 1800          # 30m
TTL_RISK_ENDPOINT = 900      # 15m

# WMO Weather interpretation code → description
WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Light snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm",
}


class WeatherService:
    """
    Fetches weather, computes risk scores, uses snapshots for caching,
    and emits event logs for async processors.
    """

    async def get_weather_risk(
        self,
        db: Session,
        region: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        crop_id: Optional[UUID] = None,
    ) -> dict:
        """
        Get weather risk score for a region/coordinates.
        Leverages caching via snapshot repository.
        """
        repo = WeatherRepository(db)
        # Location key formatting (geohash equivalent precision)
        location_key = self._generate_location_key(region, latitude, longitude)

        snapshot = repo.get_active_snapshot(location_key)

        if snapshot:
            logger.info(f"Weather Cache HIT for {location_key}")
            # Reconstruct response from snapshot
            weather_data = snapshot.weather_payload_json
            risk_score = snapshot.weather_risk_score
            alerts_data = snapshot.alerts_json
            source = snapshot.provider_source
            updated_at = snapshot.captured_at

            alerts = []
            for a in alerts_data:
                alerts.append(WeatherAlertItem(**a))

            # Provide Confidence score based on age and source
            confidence = self._compute_confidence(source, updated_at)

            return {
                "weather_risk_score": float(round(risk_score, 4)),
                "weather_data": weather_data,
                "alerts": alerts,
                "source": source,
                "is_fallback": source not in ["open-meteo", "openweathermap"],
                "weather_confidence": float(round(confidence, 4)),
                "updated_at": updated_at.isoformat(),
                "ttl_seconds": snapshot.ttl_seconds,
            }

        logger.info(f"Weather Cache MISS for {location_key}. Fetching...")
        weather = await self._fetch_weather(region, latitude, longitude, db=db)
        risk_score = self._compute_risk_score(weather)
        alerts = self._generate_alerts(weather)

        # Determine TTL
        ttl = TTL_RISK_ENDPOINT

        # Persist new snapshot
        snapshot_data = {
            "location_key": location_key,
            "lat": latitude,
            "lng": longitude,
            "provider_source": (
                weather.description
                if getattr(weather, "source", None) == "mock"
                else getattr(weather, "source", "historical_fallback")
            ),
            "weather_payload_json": weather.model_dump(by_alias=True),
            "weather_risk_score": float(round(risk_score, 4)),
            "alerts_json": [a.model_dump() for a in alerts],
            "ttl_seconds": ttl,
            "captured_at": datetime.now(timezone.utc),
        }

        saved_snapshot = repo.save_snapshot(snapshot_data)

        # Emit event if high risk or alerts exist
        if alerts or risk_score >= 0.5:
            dispatcher = DBEventDispatcher(db)
            event_base_id = crop_id or saved_snapshot.id

            # Use 'weather_updated' schema
            for alert in alerts:
                dispatcher.publish(
                    event_type=NotificationEvents.WEATHER_UPDATED,
                    entity_type="CropInstance",
                    entity_id=event_base_id,
                    payload={
                        "crop_instance_id": str(crop_id) if crop_id else None,
                        "advisory": alert.message,
                        "severity": alert.severity,
                        "urgency_level": (
                            "High"
                            if alert.severity in ["HIGH", "CRITICAL"]
                            else "Medium"
                        ),
                        "code": alert.code,
                        "risk_score": float(round(risk_score, 4)),
                    },
                )

        confidence = self._compute_confidence(
            weather.source, saved_snapshot.captured_at
        )

        return {
            "weather_risk_score": float(round(risk_score, 4)),
            "weather_data": weather.model_dump(by_alias=True),
            "alerts": alerts,
            "source": weather.source,
            "is_fallback": weather.source not in ["open-meteo", "openweathermap"],
            "weather_confidence": float(round(confidence, 4)),
            "updated_at": saved_snapshot.captured_at.isoformat(),
            "ttl_seconds": ttl,
        }

    def _generate_location_key(
        self, region: str, lat: Optional[float], lng: Optional[float]
    ) -> str:
        if lat is not None and lng is not None:
            return f"geo_{round(lat, 2)}_{round(lng, 2)}"
        return f"reg_{region.lower().strip().replace(' ', '_')}"

    async def _fetch_weather(
        self,
        region: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> WeatherDataSchema:
        """Fetch from Open-Meteo (primary), OpenWeatherMap (secondary), or historical fallback."""
        if latitude and longitude:
            # 1. Open-Meteo — free, no key required
            try:
                return await self._fetch_open_meteo(latitude, longitude)
            except Exception as e:
                logger.warning(f"Open-Meteo failed for {region}: {e}. Trying OpenWeatherMap.")

            # 2. OpenWeatherMap — if API key is configured
            if OPENWEATHER_API_KEY:
                try:
                    url = f"{OPENWEATHER_BASE_URL}/weather"
                    params = {"lat": latitude, "lon": longitude, "appid": OPENWEATHER_API_KEY, "units": "metric"}
                    async with httpx.AsyncClient(timeout=2.5) as client:
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        data = response.json()
                    return WeatherDataSchema(
                        temperature=data["main"]["temp"],
                        humidity=data["main"]["humidity"],
                        rainfall_mm=data.get("rain", {}).get("1h", 0.0) * 24,
                        wind_speed_kmh=data["wind"]["speed"] * 3.6,
                        description=data["weather"][0]["description"],
                        source="openweathermap",
                        is_fallback=False,
                    )
                except Exception as e:
                    logger.warning(f"OpenWeatherMap failed for {region}: {e}. Falling back.")

        return self._historical_fallback(region)

    async def _fetch_open_meteo(self, latitude: float, longitude: float) -> WeatherDataSchema:
        """Fetch real-time weather + 7-day forecast from Open-Meteo (free, no API key)."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code,uv_index",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": 7,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(OPENMETEO_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        wmo_code = current.get("weather_code", 0)
        description = WMO_DESCRIPTIONS.get(wmo_code, "Unknown conditions")

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip_sums = daily.get("precipitation_sum", [])
        daily_codes = daily.get("weather_code", [])

        forecast = []
        for i in range(len(dates)):
            forecast.append({
                "date": dates[i],
                "temp_max": round(max_temps[i], 1) if i < len(max_temps) and max_temps[i] is not None else None,
                "temp_min": round(min_temps[i], 1) if i < len(min_temps) and min_temps[i] is not None else None,
                "precipitation_mm": round(precip_sums[i], 1) if i < len(precip_sums) and precip_sums[i] is not None else 0.0,
                "description": WMO_DESCRIPTIONS.get(daily_codes[i] if i < len(daily_codes) else 0, "Unknown"),
                "weather_code": daily_codes[i] if i < len(daily_codes) else 0,
            })

        # Use today's daily precipitation sum (more accurate than current hourly)
        rainfall_24h = precip_sums[0] if precip_sums and precip_sums[0] is not None else current.get("precipitation", 0.0)

        return WeatherDataSchema(
            temperature=current.get("temperature_2m", 25.0),
            humidity=current.get("relative_humidity_2m", 50.0),
            rainfall_mm=rainfall_24h,
            wind_speed_kmh=current.get("wind_speed_10m", 0.0),
            description=description,
            source="open-meteo",
            is_fallback=False,
            uv_index=current.get("uv_index"),
            forecast_3d=forecast,
        )

    def _historical_fallback(self, region: str) -> WeatherDataSchema:
        """Return a baseline WeatherData from historical averages."""
        return WeatherDataSchema(
            temperature=28.0,
            humidity=55.0,
            rainfall_mm=5.0,
            wind_speed_kmh=15.0,
            description="historical baseline",
            source="historical_fallback"
        )

    def _compute_risk_score(self, weather: WeatherDataSchema) -> float:
        """Compute weather risk score from weather parameters."""
        risk = 0.0

        if weather.temperature_c >= TEMP_HIGH_THRESHOLD:
            temp_risk = min((weather.temperature_c - TEMP_HIGH_THRESHOLD) / 10, 1.0)
        elif weather.temperature_c <= TEMP_LOW_THRESHOLD:
            temp_risk = min((TEMP_LOW_THRESHOLD - weather.temperature_c) / 10, 1.0)
        else:
            temp_risk = 0.0
        risk += 0.30 * temp_risk

        if weather.rain_mm_24h >= RAIN_HEAVY_THRESHOLD:
            rain_risk = min((weather.rain_mm_24h - RAIN_HEAVY_THRESHOLD) / 50, 1.0)
        elif weather.rain_mm_24h == 0 and weather.humidity_pct < 30:
            rain_risk = 0.5
        else:
            rain_risk = 0.0
        risk += 0.35 * rain_risk

        if weather.wind_kph >= WIND_HIGH_THRESHOLD:
            wind_risk = min((weather.wind_kph - WIND_HIGH_THRESHOLD) / 40, 1.0)
        else:
            wind_risk = 0.0
        risk += 0.20 * wind_risk

        if weather.humidity_pct > 90:
            humidity_risk = 0.6
        elif weather.humidity_pct < 20:
            humidity_risk = 0.5
        else:
            humidity_risk = 0.0
        risk += 0.15 * humidity_risk

        # Extract source (from model or default to fallback logic)
        source = getattr(weather, "source", "historical_fallback")

        if source == "historical_fallback":
            baseline = HISTORICAL_BASELINES.get(
                "default", HISTORICAL_BASELINES["default"]
            )
            risk = max(risk, baseline * 0.5)

        return max(0.0, min(1.0, risk))

    def _generate_alerts(self, weather: WeatherDataSchema) -> list[WeatherAlertItem]:
        """Generate typed weather alerts based on thresholds."""
        alerts = []

        if weather.temperature_c >= TEMP_HIGH_THRESHOLD:
            alerts.append(
                WeatherAlertItem(
                    code="HEAT_STRESS",
                    severity="HIGH",
                    message=f"HEAT WARNING: Temp {weather.temperature_c}°C above bounds.",
                )
            )

        if weather.temperature_c <= TEMP_LOW_THRESHOLD:
            alerts.append(
                WeatherAlertItem(
                    code="FROST_RISK",
                    severity="HIGH",
                    message=f"FROST WARNING: Temp {weather.temperature_c}°C below bounds.",
                )
            )

        if weather.rain_mm_24h >= RAIN_HEAVY_THRESHOLD:
            alerts.append(
                WeatherAlertItem(
                    code="HEAVY_RAIN",
                    severity="HIGH",
                    message=f"FLOOD WARNING: Rainfall {weather.rain_mm_24h}mm expected.",
                )
            )

        if weather.wind_kph >= WIND_HIGH_THRESHOLD:
            alerts.append(
                WeatherAlertItem(
                    code="HIGH_WIND",
                    severity="MEDIUM",
                    message=f"WIND WARNING: Speed {weather.wind_kph}km/h expected.",
                )
            )

        return alerts

    def _compute_confidence(self, source: str, captured_at: datetime) -> float:
        """Compute weather data confidence score based on staleness and source."""
        age_seconds = (
            datetime.now(timezone.utc) - captured_at.replace(tzinfo=timezone.utc)
        ).total_seconds()

        # Source base confidence
        if source in ["open-meteo", "openweathermap"]:
            base = 1.0
        elif source == "historical_fallback":
            base = 0.6
        else:
            base = 0.4

        # Staleness degradation (decays ~10% per hour)
        age_penalty = min(0.5, max(0.0, (age_seconds / 3600)) * 0.1)

        return max(0.1, base - age_penalty)
