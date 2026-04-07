"""
Weather Repository
Handles database-level operations for weather snapshots.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.weather_snapshot import WeatherSnapshot


class WeatherRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_snapshot(self, location_key: str) -> Optional[WeatherSnapshot]:
        """
        Retrieves the latest unexpired snapshot for a location key.
        """
        now = datetime.now(timezone.utc)
        return (
            self.db.query(WeatherSnapshot)
            .filter(
                WeatherSnapshot.location_key == location_key,
                WeatherSnapshot.expires_at > now,
            )
            .order_by(WeatherSnapshot.captured_at.desc())
            .first()
        )

    def get_closest_snapshot(
        self, location_key: str, target_date: datetime
    ) -> Optional[WeatherSnapshot]:
        """
        Retrieves the snapshot closest to a target date, looking backwards.
        Used for replay determinism.
        """
        return (
            self.db.query(WeatherSnapshot)
            .filter(
                WeatherSnapshot.location_key == location_key,
                WeatherSnapshot.captured_at <= target_date,
            )
            .order_by(WeatherSnapshot.captured_at.desc())
            .first()
        )

    def save_snapshot(self, snapshot_data: dict) -> WeatherSnapshot:
        """
        Creates and persists a new WeatherSnapshot.
        """
        snapshot = WeatherSnapshot(**snapshot_data)
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
