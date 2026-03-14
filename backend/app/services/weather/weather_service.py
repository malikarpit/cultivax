"""
Weather Service — External Weather API Integration

Fetches weather data and computes weather-based risk scores.
Supports OpenWeatherMap API with fallback to historical baselines.

MSDD 4.8 | TDD Section 4.7
"""

import os
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Historical baseline risk values by region (fallback when API fails)
HISTORICAL_BASELINES = {
    "default": 0.3,
    "arid": 0.5,
    "tropical": 0.35,
    "temperate": 0.25,
    "semi-arid": 0.45,
}

# Weather risk thresholds
TEMP_HIGH_THRESHOLD = 42.0    # °C — extreme heat
TEMP_LOW_THRESHOLD = 5.0      # °C — frost risk
RAIN_HEAVY_THRESHOLD = 50.0   # mm/day — flood risk
WIND_HIGH_THRESHOLD = 60.0    # km/h — crop damage risk


class WeatherData:
    """Structured weather data from API or fallback."""

    def __init__(
        self,
        temperature: float = 25.0,
        humidity: float = 50.0,
        rainfall_mm: float = 0.0,
        wind_speed_kmh: float = 10.0,
        description: str = "clear",
        source: str = "fallback",
    ):
        self.temperature = temperature
        self.humidity = humidity
        self.rainfall_mm = rainfall_mm
        self.wind_speed_kmh = wind_speed_kmh
        self.description = description
        self.source = source
        self.fetched_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed_kmh": self.wind_speed_kmh,
            "description": self.description,
            "source": self.source,
            "fetched_at": self.fetched_at,
        }


class WeatherService:
    """
    Fetches weather data and computes weather-based risk scores.

    Flow (MSDD 4.8):
    1. Try OpenWeatherMap API for current/forecast data
    2. If API fails → fall back to historical baseline for region
    3. Compute weather_risk_score (0-1) from temperature, rainfall, wind
    """

    async def get_weather_risk(
        self,
        region: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> dict:
        """
        Get weather risk score for a region.

        Args:
            region: Region name (used for fallback baselines)
            latitude: Optional GPS latitude for precise API lookup
            longitude: Optional GPS longitude for precise API lookup

        Returns:
            Dict with weather_risk_score, weather_data, and source
        """

        weather = await self._fetch_weather(region, latitude, longitude)
        risk_score = self._compute_risk_score(weather)

        result = {
            "weather_risk_score": round(risk_score, 4),
            "weather_data": weather.to_dict(),
            "alerts": self._generate_alerts(weather),
        }

        logger.info(
            f"Weather risk for {region}: {risk_score:.3f} "
            f"(source={weather.source}, temp={weather.temperature}°C, "
            f"rain={weather.rainfall_mm}mm)"
        )

        return result

    async def _fetch_weather(
        self,
        region: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> WeatherData:
        """
        Fetch weather from OpenWeatherMap API.
        Falls back to historical baseline if API is unavailable.
        """

        if OPENWEATHER_API_KEY and latitude and longitude:
            try:
                import httpx  # type: ignore

                url = f"{OPENWEATHER_BASE_URL}/weather"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()

                return WeatherData(
                    temperature=data.get("main", {}).get("temp", 25.0),
                    humidity=data.get("main", {}).get("humidity", 50.0),
                    rainfall_mm=data.get("rain", {}).get("1h", 0.0) * 24,
                    wind_speed_kmh=data.get("wind", {}).get("speed", 0.0) * 3.6,
                    description=data.get("weather", [{}])[0].get(
                        "description", "unknown"
                    ),
                    source="openweathermap",
                )

            except Exception as e:
                logger.warning(
                    f"Weather API failed for {region}: {e}. "
                    "Falling back to historical baseline."
                )

        # Fallback to historical baseline
        return self._historical_fallback(region)

    def _historical_fallback(self, region: str) -> WeatherData:
        """Return a baseline WeatherData from historical averages."""
        return WeatherData(
            temperature=28.0,
            humidity=55.0,
            rainfall_mm=5.0,
            wind_speed_kmh=15.0,
            description="historical baseline",
            source="historical_fallback",
        )

    def _compute_risk_score(self, weather: WeatherData) -> float:
        """
        Compute weather risk score from weather parameters.
        Returns 0-1 where 1 = extreme risk.
        """
        risk = 0.0

        # Temperature risk (30% weight)
        if weather.temperature >= TEMP_HIGH_THRESHOLD:
            temp_risk = min((weather.temperature - TEMP_HIGH_THRESHOLD) / 10, 1.0)
        elif weather.temperature <= TEMP_LOW_THRESHOLD:
            temp_risk = min((TEMP_LOW_THRESHOLD - weather.temperature) / 10, 1.0)
        else:
            temp_risk = 0.0
        risk += 0.30 * temp_risk

        # Rainfall risk (35% weight)
        if weather.rainfall_mm >= RAIN_HEAVY_THRESHOLD:
            rain_risk = min(
                (weather.rainfall_mm - RAIN_HEAVY_THRESHOLD) / 50, 1.0
            )
        elif weather.rainfall_mm == 0 and weather.humidity < 30:
            rain_risk = 0.5  # Drought indicator
        else:
            rain_risk = 0.0
        risk += 0.35 * rain_risk

        # Wind risk (20% weight)
        if weather.wind_speed_kmh >= WIND_HIGH_THRESHOLD:
            wind_risk = min(
                (weather.wind_speed_kmh - WIND_HIGH_THRESHOLD) / 40, 1.0
            )
        else:
            wind_risk = 0.0
        risk += 0.20 * wind_risk

        # Humidity extremes (15% weight)
        if weather.humidity > 90:
            humidity_risk = 0.6  # Disease risk
        elif weather.humidity < 20:
            humidity_risk = 0.5  # Drought stress
        else:
            humidity_risk = 0.0
        risk += 0.15 * humidity_risk

        # Use historical baseline as floor if using fallback
        if weather.source == "historical_fallback":
            baseline = HISTORICAL_BASELINES.get(
                "default", HISTORICAL_BASELINES["default"]
            )
            risk = max(risk, baseline * 0.5)

        return max(0.0, min(1.0, risk))

    def _generate_alerts(self, weather: WeatherData) -> list[str]:
        """Generate weather alerts based on thresholds."""
        alerts = []

        if weather.temperature >= TEMP_HIGH_THRESHOLD:
            alerts.append(
                f"HEAT WARNING: Temperature {weather.temperature}°C exceeds "
                f"threshold ({TEMP_HIGH_THRESHOLD}°C)"
            )
        if weather.temperature <= TEMP_LOW_THRESHOLD:
            alerts.append(
                f"FROST WARNING: Temperature {weather.temperature}°C below "
                f"threshold ({TEMP_LOW_THRESHOLD}°C)"
            )
        if weather.rainfall_mm >= RAIN_HEAVY_THRESHOLD:
            alerts.append(
                f"FLOOD WARNING: Rainfall {weather.rainfall_mm}mm exceeds "
                f"threshold ({RAIN_HEAVY_THRESHOLD}mm)"
            )
        if weather.wind_speed_kmh >= WIND_HIGH_THRESHOLD:
            alerts.append(
                f"WIND WARNING: Wind speed {weather.wind_speed_kmh}km/h "
                f"exceeds threshold ({WIND_HIGH_THRESHOLD}km/h)"
            )

        return alerts
